import asyncio
import os
from datetime import date
from sqlalchemy import text
from src.app.db.session import AsyncSessionLocal

async def seed_full_vn30():
    # 1. Read VN30 list
    vn30_file = "vn30.txt"
    if not os.path.exists(vn30_file):
        print(f"Error: {vn30_file} not found.")
        return
        
    with open(vn30_file, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]

    print(f"Found {len(symbols)} symbols in {vn30_file}")

    async with AsyncSessionLocal() as db:
        print("Starting manual seeding (Raw SQL)...")
        
        # 1. Universe
        # ID 1 for VN30
        print("Seeding Universe 'VN30'...")
        await db.execute(text("""
            INSERT INTO trading.universe (universe_id, code, name, source) 
            VALUES (1, 'VN30', 'VN30 Index', 'manual') 
            ON CONFLICT (code) DO NOTHING
        """))
        
        # 2. Timeframe
        # ID 1 for 1D
        print("Seeding Timeframe '1D'...")
        await db.execute(text("""
            INSERT INTO trading.timeframe (timeframe_id, code, bar_seconds) 
            VALUES (1, '1D', 86400) 
            ON CONFLICT (code) DO NOTHING
        """))
        
        # 3. Symbols & Members
        print("Seeding Symbols and Members...")
        
        # We need to handle IDs manually or let serial handle it if we didn't specify.
        # But our models defined Integers without autoincrement explicitly in the SQL I wrote? 
        # Actually init_db.sql usually uses SERIAL. 
        # Let's assuming SERIAL/IDENTITY is working if we omit ID, BUT
        # for MarketSymbol we defined symbol_id as PK.
        # Let's check if we can rely on DB sequence or if we need to manually assign.
        # To be safe and simple: query max ID or just insert. 
        # Using "ON CONFLICT (symbol) DO UPDATE SET symbol=EXCLUDED.symbol RETURNING symbol_id" is postgres way.
        
        for sym in symbols:
            # Insert Symbol if not exists, return ID
            # Postgres supports RETURNING
            query_sym = text("""
                INSERT INTO trading.market_symbol (symbol, exchange, is_active)
                VALUES (:sym, 'HOSE', true)
                ON CONFLICT (symbol) DO UPDATE SET is_active = true
                RETURNING symbol_id
            """)
            res = await db.execute(query_sym, {"sym": sym})
            sym_id = res.scalar()
            
            if not sym_id:
                # If UPDATE doesn't return ID in some PG versions (it should), query it
                res = await db.execute(text("SELECT symbol_id FROM trading.market_symbol WHERE symbol = :sym"), {"sym": sym})
                sym_id = res.scalar()
            
            # Insert Member
            # Universe 1, Symbol ID
            query_mem = text("""
                INSERT INTO trading.universe_member (universe_id, symbol_id, effective_from)
                VALUES (1, :sym_id, :eff_from)
                ON CONFLICT (universe_id, symbol_id, effective_from) DO NOTHING
            """)
            await db.execute(query_mem, {"sym_id": sym_id, "eff_from": date.today()})
            print(f" - Processed {sym} (ID: {sym_id})")

        await db.commit()
        print("✅ Seeding Complete.")

if __name__ == "__main__":
    import sys
    # Fix for Windows asyncio loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(seed_full_vn30())
    except Exception as e:
        print(f"❌ Scritp Error: {e}")
