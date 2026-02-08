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
        # Note: Backfill step removed due to Windows subprocess limitation
        # Data should be manually updated or scheduled separately
        # Scheduler focuses on analyzing existing data
        
        # Analysis
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
                 try:
                     query = text(f"SELECT ts, open, high, low, close, volume FROM trading.ohlcv_bar WHERE symbol_id = {sym_id} ORDER BY ts ASC")
                     rows = (await db.execute(query)).fetchall()
                     if not rows or len(rows) < 30:
                         logger.debug(f"Skipping {sym}: insufficient data")
                         continue
                     
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
                     logger.debug(f"✅ {sym}: Score = {score_res['score_total']}")
                     
                 except Exception as e:
                     logger.error(f"Error processing {sym}: {e}")
                     # Continue with next symbol instead of failing entire pipeline
                     continue
                 
             # Sort and Report
             results.sort(key=lambda x: x['score_total'], reverse=True)
             top3 = results[:3]
             
             # Send Telegram
             await bot.send_report(top3, str(run_id))
             logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        await bot.send_message(f"❌ Analysis failed: {e}")

def start_scheduler():
    interval = settings.SCHEDULE_INTERVAL_MINUTES
    # Run immediately AND every interval
    scheduler.add_job(pipeline_job, IntervalTrigger(minutes=interval), next_run_time=datetime.now())
    scheduler.start()
    logger.info(f"Scheduler started. Job interval: {interval} minutes. First run triggered immediately.")
