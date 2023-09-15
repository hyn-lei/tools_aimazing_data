import json
import logging

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response, JSONResponse

from app.http.deps import get_db
from app.models.data_card import DataCard
from app.models.post import Post
from app.models.user import User
from app.providers.github_data import git_hub_retriever
from app.services.auth import hashing
from datetime import datetime
import requests

router = APIRouter(prefix="/posts")


def content_medium(id: str):
    url = f"https://medium2.p.rapidapi.com/article/{id}/markdown"

    headers = {
        "X-RapidAPI-Key": "07a05c759fmshd0cd5e0712bed8ap19e6a0jsn8c3d0b8d1654",
        "X-RapidAPI-Host": "medium2.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    data = response.json()
    return data.get("markdown")


@router.post("/", dependencies=[Depends(get_db)])
async def add(request: Request):
    data = await request.json()
    logging.info(data)
    medium_id = data.get("medium_id")
    content = data.get("content")
    if not medium_id and not content:
        return JSONResponse(status_code=400, content='{"error": "request invalid"}')

    if medium_id:
        content = content_medium(medium_id)
        medium_id = str(datetime.now())

    if not content:
        return {"error": "content empty"}

    # logging content with medium_id
    logging.info(f"content: {content}")

    # translate and insert
    Post.add(medium_id, content)
    return {"result": True}
