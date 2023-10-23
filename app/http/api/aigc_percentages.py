from fastapi import APIRouter
from starlette.requests import Request

from test.test_rapid_api import langchain_percentage_quiz

router = APIRouter(prefix="/aigc_pts")


@router.post("/")
async def token(request: Request):
    """
    获取生成的内容
    """
    request_data = await request.json()
    print(request_data)
    content = request_data.get("content")
    print(content)

    # question
    data = langchain_percentage_quiz(content_=content)
    return data
