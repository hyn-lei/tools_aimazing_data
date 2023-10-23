import logging
import urllib.parse

from fastapi import APIRouter
from starlette.requests import Request

from test.test_rapid_api import langchain_percentage_quiz

router = APIRouter(prefix="/aigc_pts")


@router.get("/{content_str}")
async def token(content_str: str, request: Request):
    """
    获取生成的内容
    """
    headers = request.headers
    logging.info(f"headers:{headers}")

    content = urllib.parse.unquote(content_str)
    logging.info(f"content_str:{content_str}, content:{content}")

    # question
    data = langchain_percentage_quiz(content_=content)
    return data
