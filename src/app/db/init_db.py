import asyncio
import logging
import os
import sys
import psycopg
from src.app.core.config import settings

# Fix for Windows asyncio loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    logger.info("Initializing database with raw psycopg...")
    
    sql_path = "trading_app_init.sql"
    if not os.path.exists(sql_path):
        logger.error(f"SQL file not found at {sql_path}")
        return

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # postgresql+psycopg:// -> postgresql://
    dsn = settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    
    async def try_connect_and_init(target_dsn):
         async with await psycopg.AsyncConnection.connect(target_dsn) as aconn:
            async with aconn.cursor() as cur:
                await cur.execute(sql_content)
                await aconn.commit()
                logger.info(f"Database initialized successfully on {target_dsn}")

    try:
        await try_connect_and_init(dsn)
    except psycopg.OperationalError as e:
        # Check if DB does not exist
        if 'does not exist' in str(e) or '3D000' in str(e): # 3D000 is invalid_catalog_name
            logger.info("Database not found. Attempting to create...")
            base_dsn = dsn.rsplit('/', 1)[0] + '/postgres'
            try:
                # autocommit=True needed for CREATE DATABASE
                async with await psycopg.AsyncConnection.connect(base_dsn, autocommit=True) as conn:
                    await conn.execute("CREATE DATABASE trading_vn30")
                logger.info("Database 'trading_vn30' created. Retrying init...")
                await try_connect_and_init(dsn)
            except Exception as e2:
                logger.error(f"Failed to create DB: {e2}")
                raise e2
        else:
            raise e
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(init_db())
