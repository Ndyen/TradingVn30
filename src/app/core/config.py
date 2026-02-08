from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    APP_TIMEZONE: str = "Asia/Bangkok"
    DEFAULT_UNIVERSE: str = "VN30"
    DEFAULT_TIMEFRAME: str = "1D"
    DEFAULT_STRATEGY: str = "shortterm_v1"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Scheduler
    SCHEDULE_INTERVAL_MINUTES: int = 60
    
    # VNStock API
    VNSTOCK_API_KEY: str = ""

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
