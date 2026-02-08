import asyncio
from src.app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT count(*) FROM trading.universe_member"))
        cnt_mem = res.scalar()
        print(f"Universe Members: {cnt_mem}")
        
        res = await db.execute(text("SELECT count(*) FROM trading.ohlcv_bar"))
        cnt_ohlcv = res.scalar()
        print(f"OHLCV Bars: {cnt_ohlcv}")
        
        if cnt_mem > 0:
            res = await db.execute(text("SELECT symbol FROM trading.market_symbol LIMIT 5"))
            print(f"Sample Symbols: {res.scalars().all()}")

if __name__ == "__main__":
    # Fix windows loop
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check())
