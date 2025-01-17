import logging

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.http.api.doc_pages import content_medium

router = APIRouter(prefix="/mediums")


@router.post("/")
async def post(request: Request):
    """
    获取 medium 数据，不做其他；
    """

    data = await request.json()

    medium_id = data.get("medium_id")
    content = content_medium(medium_id)
    content = content.replace("miro.medium.com", "auto.aimazing.site/medium")

    if not content:
        return JSONResponse(status_code=400, content='{"error": "request invalid"}')

    # logging content with medium_id
    logging.info(f"content: {content}")

    return {"content": content}
