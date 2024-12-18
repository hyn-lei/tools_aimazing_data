import logging
from concurrent.futures import ThreadPoolExecutor

import requests
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.models.doc_page import DocPage

router = APIRouter(prefix="/doc_pages")

executor = ThreadPoolExecutor(max_workers=5)

headers = {
    "X-RapidAPI-Key": "07a05c759fmshd0cd5e0712bed8ap19e6a0jsn8c3d0b8d1654",
    "X-RapidAPI-Host": "medium2.p.rapidapi.com",
}


def content_medium(id: str):
    url = f"https://medium2.p.rapidapi.com/article/{id}/markdown"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    data = response.json()
    return data.get("markdown")


@router.post("/")
async def add(request: Request):
    data = await request.json()
    logging.info(data)
    medium_id = data.get("medium_id")

    content = data.get("content")
    if not medium_id and not content:
        return JSONResponse(status_code=400, content='{"error": "request invalid"}')

    if medium_id:
        content = content_medium(medium_id)

    if not content:
        return {"error": "content empty"}

    # logging content with medium_id
    logging.info(f"content: {content}")

    # translate and insert
    executor.submit(lambda: DocPage.add(content, medium_id))
    # result = DocPage.add(content)

    return {"result": True}
