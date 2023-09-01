from fastapi import APIRouter
from app.http.api import demo, data_cards, posts
from app.http.api import auth
from app.http.api import users

api_router = APIRouter()

api_router.include_router(demo.router, tags=["demo"])

api_router.include_router(auth.router, tags=["auth"])

api_router.include_router(users.router, tags=["users"])

api_router.include_router(data_cards.router, tags=["data_cards"])

api_router.include_router(posts.router, tags=["posts"])
