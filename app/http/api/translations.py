import logging
from datetime import datetime

import requests
from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse

from app.http.deps import get_db_blog
from app.models.post import Post

router = APIRouter(prefix="/translations")


@router.post("/")
async def get(request: Request):
    """
    调用ai 做翻译，不做其他
    """

    data = await request.json()
    content = data.get("content")
    if not content:
        return JSONResponse(status_code=400, content='{"error": "request invalid"}')

    # logging content with medium_id
    logging.info(f"content: {content}")

    # translate
    title, summary, translation = Post.ai_handle(content)
    logging.info(f"title:{title}, summary:{summary}, translation:{translation}")

    return {"title": title, "summary": summary, "translation": translation}
