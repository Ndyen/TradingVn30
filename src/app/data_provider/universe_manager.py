import logging
from datetime import date
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.db.models import Universe, UniverseMember, MarketSymbol

try:
    from vnstock import Listing
except ImportError:
    Listing = None

logger = logging.getLogger(__name__)

class UniverseManager:
    def __init__(self, db: AsyncSession, api_key: str = None):
        self.db = db
        self.api_key = api_key

    async def update_vn30(self, source: str = "vnstock", file_path: str = "vn30.txt"):
        """
        Update VN30 universe members.
        """
        # 1. Get or Create Universe
        univ_stmt = select(Universe).where(Universe.code == 'VN30')
        univ = (await self.db.execute(univ_stmt)).scalar_one_or_none()
        if not univ:
            univ = Universe(code='VN30', name='VN30 Index', source=source)
            self.db.add(univ)
            await self.db.flush()
        
        # 2. Get List
        symbols = []
        if source == "vnstock" and Listing is not None:
             try:
                 # Try with API key first (vnstock 3.4.2+)
                 try:
                     if self.api_key:
                         lst = Listing(source='vci', api_key=self.api_key, show_log=False)
                     else:
                         lst = Listing(source='vci', show_log=False)
                 except TypeError:
                     # Fallback: older vnstock version doesn't support api_key
                     logger.warning("vnstock Listing doesn't support api_key parameter, using without API key")
                     lst = Listing(source='vci', show_log=False)
                 
                 # symbols_by_group("VN30")
                 df = lst.symbols_by_group(group='VN30')
                 if not df.empty and 'ticker' in df.columns:
                     symbols = df['ticker'].tolist()
                 # Some sources might use different column names? VCI usually 'ticker' or 'symbol'
                 # If 'ticker' not present, check columns
                 elif not df.empty and 'symbol' in df.columns:
                     symbols = df['symbol'].tolist()
             except Exception as e:
                 logger.error(f"Failed to fetch VN30 from vnstock: {e}")
        
        if not symbols:
             # Fallback to file
             try:
                 with open(file_path, "r", encoding="utf-8") as f:
                     symbols = [line.strip() for line in f if line.strip()]
             except FileNotFoundError:
                 logger.error(f"vn30.txt not found at {file_path}")
                 return

        if not symbols:
            logger.warning("No symbols found for VN30")
            return

        logger.info(f"Updating VN30 with {len(symbols)} symbols: {symbols}")

        # 3. Upsert Symbols & Members
        today = date.today()
        
        for ticker in symbols:
            # Ensure Symbol Exists
            sym_stmt = select(MarketSymbol).where(MarketSymbol.symbol == ticker)
            sym = (await self.db.execute(sym_stmt)).scalar_one_or_none()
            if not sym:
                sym = MarketSymbol(symbol=ticker)
                self.db.add(sym)
                await self.db.flush()
            
            # Ensure Membership
            # Check if already active member
            mem_stmt = select(UniverseMember).where(
                UniverseMember.universe_id == univ.universe_id,
                UniverseMember.symbol_id == sym.symbol_id,
                UniverseMember.effective_to.is_(None)
            ).distinct()
            # Use first() instead of scalar_one_or_none() to handle duplicates gracefully
            mem = (await self.db.execute(mem_stmt)).scalars().first()
            
            if not mem:
                # Add new membership
                new_mem = UniverseMember(
                    universe_id=univ.universe_id,
                    symbol_id=sym.symbol_id,
                    effective_from=today
                )
                self.db.add(new_mem)
        
        # TODO: Handle removals? If a symbol is no longer in list, set effective_to?
        # For simplicity, we just add new ones. 
        
        await self.db.commit()
        logger.info("VN30 universe updated.")
