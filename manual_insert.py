import asyncio
from datetime import date
from src.app.db.session import AsyncSessionLocal
from src.app.db.models import Universe, UniverseMember, MarketSymbol, Timeframe

async def manual_seed():
    print(f"UniverseMember FKs: {UniverseMember.__table__.foreign_keys}")
    async with AsyncSessionLocal() as db:
        print("Seeding Universe...")
        univ = Universe(code='VN30', name='VN30 Index', source='manual')
        db.add(univ)
        await db.flush()
        print(f"Universe ID: {univ.universe_id}")
        
        print("Seeding Symbol...")
        sym = MarketSymbol(symbol='ACB', exchange='HOSE')
        db.add(sym)
        await db.flush()
        print(f"Symbol ID: {sym.symbol_id}")
        
        print("Seeding Member...")
        mem = UniverseMember(
            universe_id=univ.universe_id,
            symbol_id=sym.symbol_id,
            effective_from=date.today()
        )
        db.add(mem)
        await db.flush()
        print("Member added.")
        
        print("Seeding Timeframe...")
        tf = Timeframe(code='1D', bar_seconds=86400)
        db.add(tf)
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(manual_seed())
