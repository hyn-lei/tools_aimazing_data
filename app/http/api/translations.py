import logging

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.providers.ai import ai_handle

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
    title, summary, translation = ai_handle(content)
    logging.info(f"title:{title}, summary:{summary}, translation:{translation}")

    return {"title": title, "summary": summary, "translation": translation}
