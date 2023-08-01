from bootstrap.application import create_app
from config.config import settings
from datetime import datetime
import uvicorn

app = create_app()


@app.get("/")
async def root():
    return f"Welcome! {datetime.utcnow()}"


if __name__ == "__main__":
    uvicorn.run(app="main:app", host=settings.SERVER_HOST, port=settings.SERVER_PORT, reload=True)
