import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.app.core.config import settings
from src.app.notification.telegram import TelegramBot
# Reuse CLI logic or import components?
# CLI logic for 'run' is complex (init db, backfill, run).
# Let's import the components directly for better control.
from src.app.data_provider.universe_manager import UniverseManager
from src.app.data_provider.client import VnStockClient
from src.app.db.session import AsyncSessionLocal
from src.app.logic.reporting import Reporter
from src.app.logic.indicators import calculate_indicators
from src.app.logic.scorer import Scorer
from src.app.logic.signals import generate_trade_plan
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

from src.app.db.init_db import init_db as init_db_func

scheduler = AsyncIOScheduler()
bot = TelegramBot()

async def pipeline_job():
    logger.info("⏰ Starting scheduled analysis pipeline...")
    await bot.send_message("⏰ Scheduled Analysis Run Started.")
    
    try:
        # 1. Backfill (Last 5 days to be safe and fast)
        logger.info("Step 1: Backfilling data...")
        # We need to replicate backfill logic slightly or call CLI function?
        # Replicating logic is cleaner for a library.
        # But for MVP, let's call the CLI command via subprocess?
        # No, subprocess is heavy. Let's use the code we verified in debug_report.py but modularized.
        
        async with AsyncSessionLocal() as db:
            # Get symbols
            res = await db.execute(text("SELECT symbol, symbol_id FROM trading.market_symbol"))
            symbols_map = {r[0]: r[1] for r in res.fetchall()}
            symbols = list(symbols_map.keys())
        
        # Backfill
        client = VnStockClient()
        # For simplicity, backfill all 30 symbols, last 5 days
        end = datetime.now()
        start = end - timedelta(days=5)
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        
        async with AsyncSessionLocal() as db:
            for sym in symbols:
                try:
                    df = client.fetch_ohlcv(sym, start_str, end_str, "1D")
                    if df is not None and not df.empty:
                        # Ingest (simplified insert)
                        # We need proper ingestion logic here. 
                        # To save time, I will assume ingestion is similar to what backfill command does.
                        # Actually, backfill command DOES ingestion. 
                        # Let's import the specific function if possible, or WRITE raw SQL insert like we did manually?
                        # Writing raw SQL insert here for safety since ORM is iffy.
                        for _, row in df.iterrows():
                            # time as ts
                            ts = row.get('time', row.get('t'))
                            if not ts: continue
                                
                            # basic insert
                            # We'll skip complex Upsert logic for now and blindly insert ON CONFLICT DO NOTHING
                            pass 
                            # Wait, re-implementing backfill here is risky.
                            # Calling the CLI command `backfill-ohlcv` via asyncio subprocess is SAFER and REUSES tested code.
                            
                except Exception as e:
                    logger.error(f"Backfill error for {sym}: {e}")

        # Usage of CLI via subprocess for robustness
        import sys
        
        cmd = [sys.executable, "-m", "src.app.cli.main", "backfill-ohlcv", "--days", "5"]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            logger.error(f"Backfill subprocess failed with code {proc.returncode}")
            logger.error(f"STDOUT: {stdout.decode()}")
            logger.error(f"STDERR: {stderr.decode()}")
            await bot.send_message("⚠️ Backfill step failed. Analysis may be stale.")
        else:
            logger.info("Backfill subprocess finished successfully.")

        # 2. Analysis
        logger.info("Step 2: Running Analysis...")
        # Since we have ORM issues, let's look at how we want to run analysis.
        # debug_report.py worked well. Let's adapt it here.
        # Or better: call a new CLI command `run-analysis` (which is what `run` was supposed to be)
        # But `run` failed with ORM error. `debug_report.py` worked.
        # Let's use `debug_report.py` logic here directly.
        
        results = []
        async with AsyncSessionLocal() as db:
             res = await db.execute(text("SELECT symbol, symbol_id FROM trading.market_symbol"))
             symbols_map = {r[0]: r[1] for r in res.fetchall()}
             
             run_id = uuid.uuid4()
             
             for sym, sym_id in symbols_map.items():
                 query = text(f"SELECT ts, open, high, low, close, volume FROM trading.ohlcv_bar WHERE symbol_id = {sym_id} ORDER BY ts ASC")
                 rows = (await db.execute(query)).fetchall()
                 if not rows or len(rows) < 30: continue
                 
                 df = pd.DataFrame(rows, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
                 df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric)
                 
                 df = calculate_indicators(df)
                 score_res = Scorer().calculate_score(df)
                 signal_res = generate_trade_plan(df, score_res)
                 
                 results.append({
                     "symbol": sym,
                     "score_total": score_res['score_total'],
                     "breakdown": score_res['breakdown'],
                     "signal": signal_res
                 })
                 
             # Sort and Report
             results.sort(key=lambda x: x['score_total'], reverse=True)
             top3 = results[:3]
             
             # Send Telegram
             await bot.send_report(top3, str(run_id))
             logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        await bot.send_message(f"❌ Analysis failed: {e}")

def start_scheduler():
    interval = settings.SCHEDULE_INTERVAL_MINUTES
    # Run immediately AND every interval
    scheduler.add_job(pipeline_job, IntervalTrigger(minutes=interval), next_run_time=datetime.now())
    scheduler.start()
    logger.info(f"Scheduler started. Job interval: {interval} minutes. First run triggered immediately.")
