from bootstrap.application import create_app
from config.config import settings
from datetime import datetime
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = create_app()

# 增加请求体大小限制
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return f"Welcome! {datetime.utcnow()}"


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=True,
        timeout_keep_alive=300,
        limit_concurrency=100,
        limit_max_requests=100,
    )
