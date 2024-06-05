from fastapi import APIRouter
from app.http.api import (
    demo,
    data_cards,
    posts,
    translations,
    doc_pages,
    aigc_percentages,
    blog,
    mediums,
)
from app.http.api import auth
from app.http.api import users

api_router = APIRouter()

api_router.include_router(demo.router, tags=["demo"])

api_router.include_router(auth.router, tags=["auth"])

api_router.include_router(users.router, tags=["users"])

api_router.include_router(data_cards.router, tags=["data_cards"])

api_router.include_router(posts.router, tags=["posts"])

# blog 站点相关 api
api_router.include_router(blog.router, tags=["blog"])

api_router.include_router(doc_pages.router, tags=["doc_pages"])

api_router.include_router(translations.router, tags=["translations"])

api_router.include_router(mediums.router, tags=["mediums"])

api_router.include_router(aigc_percentages.router, tags=["aigc_pts"])
