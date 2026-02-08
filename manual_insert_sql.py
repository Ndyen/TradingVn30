import asyncio
from datetime import date
from sqlalchemy import text
from src.app.db.session import AsyncSessionLocal

async def seed_sql():
    async with AsyncSessionLocal() as db:
        print("Seeding manually using SQL...")
        
        # Universe
        await db.execute(text("INSERT INTO trading.universe (universe_id, code, name, source) VALUES (1, 'VN30', 'VN30 Index', 'manual') ON CONFLICT DO NOTHING"))
        
        # Symbol
        await db.execute(text("INSERT INTO trading.market_symbol (symbol_id, symbol, exchange) VALUES (1, 'ACB', 'HOSE') ON CONFLICT DO NOTHING"))
        
        # Member
        await db.execute(text("INSERT INTO trading.universe_member (universe_id, symbol_id, effective_from) VALUES (1, 1, '2023-01-01') ON CONFLICT DO NOTHING"))
        
        # Timeframe
        await db.execute(text("INSERT INTO trading.timeframe (timeframe_id, code, bar_seconds) VALUES (1, '1D', 86400) ON CONFLICT DO NOTHING"))
        
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_sql())
