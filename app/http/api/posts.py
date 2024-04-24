import logging
from datetime import datetime

import requests
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.http.api.doc_pages import content_medium
from app.models.post import Post

from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/posts")

executor = ThreadPoolExecutor(max_workers=5)


@router.post("/")
async def add(request: Request):
    data = await request.json()
    logging.info(data)
    medium_id = data.get("medium_id")
    auto_translate = data.get("auto_translate")

    content = data.get("content")
    if not medium_id and not content:
        return JSONResponse(status_code=400, content='{"error": "request invalid"}')

    if medium_id:
        content = content_medium(medium_id)
    else:
        medium_id = str(datetime.now())

    if not content:
        return {"error": "content empty"}

    # logging content with medium_id
    logging.info(f"content: {content}")

    # translate and insert
    executor.submit(lambda: Post.add(medium_id, content, auto_translate))
    # result = Post.add(medium_id, content)

    return {"result": True}
