import asyncio
import pandas as pd
from sqlalchemy import text
from src.app.db.session import AsyncSessionLocal
from src.app.logic.indicators import calculate_indicators
from src.app.logic.scorer import Scorer
from src.app.logic.signals import generate_trade_plan

async def run_report():
    print("Starting Analysis (Raw SQL)...")
    results = []
    
    async with AsyncSessionLocal() as db:
        # Get symbols
        res = await db.execute(text("SELECT symbol, symbol_id FROM trading.market_symbol"))
        symbols_map = {r[0]: r[1] for r in res.fetchall()}
        symbols = list(symbols_map.keys())
        print(f"Found {len(symbols)} symbols.")
        
        from src.app.logic.scorer import Scorer
        from src.app.logic.signals import generate_trade_plan
        from src.app.logic.reporting import Reporter
        import uuid
        
        run_id = uuid.uuid4()
        
        for sym in symbols:
            # Fetch OHLCV
            query = text(f"""
                SELECT ts, open, high, low, close, volume 
                FROM trading.ohlcv_bar 
                WHERE symbol_id = {symbols_map[sym]}
                ORDER BY ts ASC
            """)
            res = await db.execute(query)
            rows = res.fetchall()
            
            if not rows or len(rows) < 50:
                # print(f"Skipping {sym} (Data len: {len(rows)})")
                continue
                
            # Convert to DF
            df = pd.DataFrame(rows, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric)
            
            # Indicators
            df = calculate_indicators(df)
            
            # Score
            scorer = Scorer()
            score_res = scorer.calculate_score(df)
            
            # Signal
            signal_res = generate_trade_plan(df, score_res)
            
            item = {
                "symbol": sym,
                "score_total": score_res['score_total'],
                "breakdown": score_res['breakdown'],
                "signal": signal_res,
                "row": {} 
            }
            results.append(item)
            # print(f"Analysed {sym}: {score_res['score_total']}")

        print(f"Analysis complete. Total analyzed: {len(results)}")
        
        # Rank
        results.sort(key=lambda x: x['score_total'], reverse=True)
        top3 = results[:3]
        
        # Report
        rep = Reporter()
        md_path = rep.save_run_results(str(run_id), top3, results, datetime.now())
        print(f"Report generated: {md_path}")
        
        print("\nTOP 3 CANDIDATES:")
        for i, item in enumerate(top3):
            print(f"{i+1}. {item['symbol']} (Score: {item['score_total']})")

if __name__ == "__main__":
    import sys
    from datetime import datetime
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_report())
