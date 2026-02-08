import asyncio
import logging
import sys
import uuid
import pandas as pd
from sqlalchemy import text
from src.app.db.session import AsyncSessionLocal
from src.app.logic.indicators import calculate_indicators
from src.app.logic.scorer import Scorer
from src.app.logic.signals import generate_trade_plan
from src.app.notification.telegram import TelegramBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_analysis_and_report():
    print("🚀 Starting Analysis & Reporting...")
    bot = TelegramBot()
    run_id = str(uuid.uuid4())
    
    await bot.send_message(f"🚀 Manual Analysis Run `{run_id}` started.")

    results = []
    async with AsyncSessionLocal() as db:
         # Get symbols
         res = await db.execute(text("SELECT symbol, symbol_id FROM trading.market_symbol"))
         symbols_map = {r[0]: r[1] for r in res.fetchall()}
         
         print(f"Analyzing {len(symbols_map)} symbols...")
         
         for sym, sym_id in symbols_map.items():
             query = text(f"SELECT ts, open, high, low, close, volume FROM trading.ohlcv_bar WHERE symbol_id = {sym_id} ORDER BY ts ASC")
             rows = (await db.execute(query)).fetchall()
             
             if not rows or len(rows) < 30: 
                 continue
             
             df = pd.DataFrame(rows, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
             df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric)
             
             try:
                 df = calculate_indicators(df)
                 score_res = Scorer().calculate_score(df)
                 signal_res = generate_trade_plan(df, score_res)
                 
                 results.append({
                     "symbol": sym,
                     "score_total": score_res['score_total'],
                     "breakdown": score_res['breakdown'],
                     "signal": signal_res
                 })
             except Exception as e:
                 logger.error(f"Error analyzing {sym}: {e}")
                 
    # Sort and Report
    results.sort(key=lambda x: x['score_total'], reverse=True)
    top3 = results[:3]
    
    print("Sending report to Telegram...")
    await bot.send_report(top3, run_id)
    print("✅ Done.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_analysis_and_report())
