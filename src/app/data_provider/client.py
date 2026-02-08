import logging
import asyncio
from typing import List, Optional
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.db.models import OhlcvBar, MarketSymbol, DataFetchLog, Timeframe
from src.app.core.config import settings

# Import vnstock
try:
    from vnstock import Quote
except ImportError:
    Quote = None
    import traceback
    traceback.print_exc()

logger = logging.getLogger(__name__)

class VnStockClient:
    def __init__(self):
        if Quote is None:
             logger.warning("vnstock.Quote not available")

    def fetch_ohlcv(self, symbol: str, start_date: str, end_date: str, resolution: str = "1D"):
        if Quote is None:
            raise RuntimeError("Vnstock Quote not imported")

        try:
            # Map resolution
            res_map = {'15m': '15m', '15': '15m'} 
            res = res_map.get(resolution, resolution)
            
            # Instantiate Quote for this symbol
            quote = Quote(symbol=symbol, source='vci', show_log=False)
            
            df = quote.history(start=start_date, end=end_date, interval=res)
            return df
        except Exception as e:
            logger.error(f"vnstock error for {symbol}: {e}")
            raise e

class DataProvider:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = VnStockClient()

    async def get_ohlcv(self, symbol: str, timeframe: str = "1D", days: int = 365) -> pd.DataFrame:
        """
        Get OHLCV from DB or fetch if missing.
        """
        # Determine date range
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)
        
        # Check DB coverage (simplification: just check max date in DB, if recent enough return DB)
        # Actually proper logic: fetch what we have, if gap at end, fetch new data.
        
        # 1. Resolve Symbol ID and Timeframe ID
        sym_stmt = select(MarketSymbol).where(MarketSymbol.symbol == symbol)
        sym = (await self.db.execute(sym_stmt)).scalar_one_or_none()
        if not sym:
            # Need to create symbol if not exists? Usually update-universe handles this.
            # But for robustness, let's create simple entry
            sym = MarketSymbol(symbol=symbol)
            self.db.add(sym)
            await self.db.flush() # get ID
            
        tf_stmt = select(Timeframe).where(Timeframe.code == timeframe)
        tf = (await self.db.execute(tf_stmt)).scalar_one_or_none()
        if not tf:
            raise ValueError(f"Timeframe {timeframe} not found")

        # 2. Query DB
        # Only select range needed
        stmt = select(OhlcvBar).where(
            OhlcvBar.symbol_id == sym.symbol_id,
            OhlcvBar.timeframe_id == tf.timeframe_id,
            OhlcvBar.ts >= start_dt
        ).order_by(OhlcvBar.ts.asc())
        
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        
        # 3. Gap Analysis
        # If no rows or last row is old, fetch fresh
        fetch_needed = False
        last_date = None
        if rows:
            last_date = rows[-1].ts.date() # Ensure it's date
            # If last_date < today (trading day), fetch.
            # Simple check: if last_date < today - 1 (allowing for weekend/delay)
            # Better: fetch from last_date + 1 day
            if last_date < end_dt.date():
                fetch_start = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                fetch_needed = True
        else:
            fetch_start = start_dt.strftime('%Y-%m-%d')
            fetch_needed = True
            
        fetch_end = end_dt.strftime('%Y-%m-%d')

        if fetch_needed:
            logger.info(f"Fetching {symbol} from {fetch_start} to {fetch_end}")
            try:
                df_new = await asyncio.to_thread(
                    self.client.fetch_ohlcv, symbol, fetch_start, fetch_end, timeframe
                )
                if df_new is not None and not df_new.empty:
                    await self._save_ohlcv(df_new, sym.symbol_id, tf.timeframe_id)
                    # Refresh DB rows
                    rows = (await self.db.execute(stmt)).scalars().all()
            except Exception as e:
                logger.error(f"Failed to fetch/save: {e}")
                # Continue with what we have? Or raise?
                pass
        
        # Convert to DataFrame
        if not rows:
            return pd.DataFrame()
            
        data = [r.as_dict() for r in rows]
        df = pd.DataFrame(data)
        # Cleanup
        if 'ts' in df.columns:
            df['time'] = df['ts']
            df.set_index('time', inplace=True)
            
        return df

    async def _save_ohlcv(self, df: pd.DataFrame, symbol_id: int, timeframe_id: int):
        # Map df columns to DB
        # vnstock: time, open, high, low, close, volume, ticker
        records = []
        for _, row in df.iterrows():
            # Parse time
            # vnstock time might be string or date
            ts_val = pd.to_datetime(row['time'])
            
            records.append({
                'symbol_id': symbol_id,
                'timeframe_id': timeframe_id,
                'ts': ts_val,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'source': 'vnstock',
                'ingested_at': datetime.now()
            })
            
        if not records:
            return

        stmt = insert(OhlcvBar).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=['symbol_id', 'timeframe_id', 'ts'],
            set_={
                'open': stmt.excluded.open,
                'high': stmt.excluded.high,
                'low': stmt.excluded.low,
                'close': stmt.excluded.close,
                'volume': stmt.excluded.volume,
                'ingested_at': stmt.excluded.ingested_at
            }
        )
        await self.db.execute(stmt)
        await self.db.commit()
