import typer
import asyncio
import sys
import logging
import pandas as pd
from datetime import datetime

from src.app.db.init_db import init_db as init_db_func
from src.app.db.session import AsyncSessionLocal
from src.app.data_provider.universe_manager import UniverseManager
from src.app.data_provider.client import DataProvider
from src.app.db.models import Universe, UniverseMember, MarketSymbol, Timeframe
from sqlalchemy import select

# Fix for Windows asyncio loop
if sys.platform == 'win32':
    import warnings
    warnings.filterwarnings("ignore", message=".*WindowsSelectorEventLoopPolicy.*")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = typer.Typer()

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

@app.command()
def init_db():
    """
    Initialize the database using trading_app_init.sql
    """
    asyncio.run(init_db_func())

@app.command()
def update_universe(source: str = "vnstock"):
    """
    Fetch VN30 constituents and update DB.
    """
    async def _do():
        from src.app.core.config import settings
        async with AsyncSessionLocal() as db:
            api_key = getattr(settings, 'VNSTOCK_API_KEY', None)
            um = UniverseManager(db, api_key=api_key)
            await um.update_vn30(source=source)
    
    asyncio.run(_do())

@app.command()
def backfill_ohlcv(days: int = 365, universe: str = "VN30"):
    """
    Backfill OHLCV data for universe members.
    """
    async def _do():
        async with AsyncSessionLocal() as db:
            # Get Universe Members
            stmt = select(MarketSymbol.symbol)\
                .join(UniverseMember, UniverseMember.symbol_id == MarketSymbol.symbol_id)\
                .join(Universe, Universe.universe_id == UniverseMember.universe_id)\
                .where(Universe.code == universe, UniverseMember.effective_to.is_(None))
            
            result = await db.execute(stmt)
            symbols = result.scalars().all()
            
            logger.info(f"Backfilling {len(symbols)} symbols from {universe}...")
            
            dp = DataProvider(db)
            for sym in symbols:
                logger.info(f"Processing {sym}...")
                try:
                    await dp.get_ohlcv(sym, days=days)
                    await db.commit()
                except Exception as e:
                    logger.error(f"Error backfilling {sym}: {e}")
                    await db.rollback()
    
    asyncio.run(_do())

@app.command()
def run(
    timeframe: str = "1D", 
    universe: str = "VN30",
    strategy: str = "shortterm_v1"
):
    """
    Run analysis and generate report.
    """
    from src.app.logic.indicators import calculate_indicators
    from src.app.logic.scorer import Scorer
    from src.app.logic.signals import generate_trade_plan
    from src.app.logic.reporting import Reporter
    from src.app.db.models import AnalysisRun, RunScore, RunSignal, RunReport, Strategy, Universe, Timeframe
    from sqlalchemy import select
    from sqlalchemy.dialects.postgresql import insert
    from src.app.notification.telegram import TelegramBot
    import uuid
    from datetime import datetime

    
    async def _do():
        async with AsyncSessionLocal() as db:
            # 1. Setup Run
            # Get IDs
            univ_obj = (await db.execute(select(Universe).where(Universe.code == universe))).scalar_one()
            tf_obj = (await db.execute(select(Timeframe).where(Timeframe.code == timeframe))).scalar_one()
            
            # Ensure strategy exists (mock/default)
            strat_obj = (await db.execute(select(Strategy).where(Strategy.code == strategy))).scalar_one_or_none()
            if not strat_obj:
                strat_obj = Strategy(
                    code=strategy, 
                    name="Default Short-term", 
                    weights={"trend":0.22, "base":0.20, "breakout":0.22, "volume":0.18, "momentum":0.10, "risk":0.08},
                    parameters={}
                )
                db.add(strat_obj)
                await db.flush()
                
            run_id = uuid.uuid4()
            run_rec = AnalysisRun(
                run_id=run_id,
                universe_id=univ_obj.universe_id,
                timeframe_id=tf_obj.timeframe_id,
                strategy_id=strat_obj.strategy_id,

                as_of=datetime.now(),
                started_at=datetime.now(),
                status='running'

            )
            db.add(run_rec)
            await db.commit()
            
            try:
                # 2. Fetch Data
                # Get members
                # ... reused logic from backfill or just query members ...
                stmt = select(MarketSymbol.symbol, MarketSymbol.symbol_id).join(UniverseMember, MarketSymbol.symbol_id == UniverseMember.symbol_id).where(UniverseMember.universe_id == univ_obj.universe_id)
                symbols = (await db.execute(stmt)).all()


                
                logger.info(f"Analyzing {len(symbols)} symbols for run {run_id}...")
                
                dp = DataProvider(db)
                scorer = Scorer(strat_obj.weights)
                
                results = []
                
                for sym in symbols:
                    try:
                        # Fetch
                        df = await dp.get_ohlcv(sym.symbol, timeframe=timeframe, days=200) # need enough for indicators
                        if df.empty or len(df) < 50:
                            continue
                        
                        # Convert to float (fix for Decimal type from DB)
                        cols = ['open', 'high', 'low', 'close', 'volume']
                        df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
                            
                        # Calc Indicators
                        df = calculate_indicators(df)

                        
                        # Score
                        score_res = scorer.calculate_score(df)
                        
                        # Signal
                        signal_res = generate_trade_plan(df, score_res)
                        
                        # Store in memory
                        item = {
                            "symbol_id": sym.symbol_id,
                            "symbol": sym.symbol,
                            "run_id": run_id,
                            **score_res, # score_total, breakdown, penalties
                            "signal": signal_res
                        }
                        results.append(item)
                        
                        # Save detailed score/signal to DB
                        # RunScore
                        rs = RunScore(
                            run_id=run_id,
                            symbol_id=sym.symbol_id,
                            score_total=score_res['score_total'],
                            score_trend=score_res['breakdown']['trend'],
                            score_base=score_res['breakdown']['base'],
                            score_breakout=score_res['breakdown']['breakout'],
                            score_volume=score_res['breakdown']['volume'],
                            score_momentum=score_res['breakdown']['momentum'],
                            score_risk=score_res['breakdown']['risk'],
                            penalties=score_res.get('penalties', []),
                            features={k: (v.isoformat() if isinstance(v, pd.Timestamp) else float(v) if isinstance(v, (int, float)) else str(v)) 
                                     for k, v in df.iloc[-1].to_dict().items() if not pd.isna(v)} if not df.empty else {},
                            computed_at=datetime.now()
                        )


                        db.add(rs)
                        
                        # RunSignal
                        sig = RunSignal(
                            run_id=run_id,
                            symbol_id=sym.symbol_id,
                            entry_zone=signal_res.get('entry_zone', {}),
                            stop_loss=signal_res.get('stop_loss'),
                            take_profit_1=signal_res.get('take_profit_1'),
                            take_profit_2=signal_res.get('take_profit_2'),
                            invalidation=signal_res.get('invalidation'),
                            key_reasons=signal_res.get('key_reasons', []),
                            risk_notes=signal_res.get('risk_notes', []),
                            created_at=datetime.now()
                        )

                        db.add(sig)
                        await db.commit() # Commit per symbol
                        
                    except Exception as e:
                        logger.error(f"Error processing {sym.symbol}: {e}")
                        await db.rollback() # Reset session on error
                
                # Final commit not needed if we commit per symbol, but harmless
                # await db.commit() 

                
                # 3. Rank & Report
                results.sort(key=lambda x: x['score_total'], reverse=True)
                top3 = results[:3]
                
                # Save RunReport
                # Serialize for DB (convert UUIDs to strings)
                def serialize_for_json(obj):
                    if isinstance(obj, dict):
                        return {k: serialize_for_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [serialize_for_json(item) for item in obj]
                    elif isinstance(obj, uuid.UUID):
                        return str(obj)
                    else:
                        return obj
                
                rr = RunReport(
                    run_id=run_id,
                    top3=[serialize_for_json({k:v for k,v in x.items() if k!='row'}) for x in top3],
                    ranking=[serialize_for_json({k:v for k,v in x.items() if k!='row'}) for x in results],
                    summary={"count": len(results)},
                    created_at=datetime.now()
                )


                db.add(rr)
                
                # Update status
                run_rec.status = 'success'
                run_rec.finished_at = datetime.now()
                await db.commit()
                
                # Generate File Report
                rep = Reporter()
                md_path = rep.save_run_results(str(run_id), top3, results, run_rec.as_of)
                
                
                
                typer.echo(f"Report generated: {md_path}")
                for i, item in enumerate(top3):
                    typer.echo(f"{i+1}. {item['symbol']}: {item['score_total']}")
                    
                # Send Telegram
                bot = TelegramBot()
                await bot.send_report(top3, str(run_id))

                    
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"CRITICAL ERROR: {e}")
                logger.error(f"Run failed: {e}")
                
                # Rollback session to recovery from error state
                await db.rollback()
                
                # Reload run_rec since it's detached
                run_rec = await db.get(AnalysisRun, run_id)
                if run_rec:
                    run_rec.status = 'failed'
                    run_rec.error_message = str(e)[:255] # truncation
                    await db.commit()
                # raise e # Optionally re-raise if we want crash, but better to exit cleanly?
                # Actually re-raising helps seeing it in CLI output if logger is redirected.
                # But we printed already.

                raise e
    
    asyncio.run(_do())

@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000):
    """
    Start the FastAPI server.
    """
    import uvicorn
    uvicorn.run("src.app.main:app", host=host, port=port, reload=True)


@app.command()
def schedule():
    """
    Start the hourly scheduler.
    """
    from src.app.core.scheduler import start_scheduler
    import asyncio
    
    async def run_forever():
        start_scheduler()
        # Keep alive
        while True:
            await asyncio.sleep(60)

    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")

@app.command()
def test_telegram(msg: str = "Test message from VN30 Bot"):
    """
    Send a test message to Telegram.
    """
    from src.app.notification.telegram import TelegramBot
    
    async def send_test():
        bot = TelegramBot()
        await bot.send_message(msg)
        
    if sys.platform == 'win32':
         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(send_test())

if __name__ == "__main__":
    app()
