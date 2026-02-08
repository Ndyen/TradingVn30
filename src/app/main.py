from fastapi import FastAPI
from src.app.api.endpoints import router
from src.app.core.config import settings

app = FastAPI(title="VN30 Best Buy Finder")

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
