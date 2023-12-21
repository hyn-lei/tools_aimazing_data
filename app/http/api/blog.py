from fastapi import APIRouter, Depends

from app.http.deps import get_db_blog
from app.providers.database import db_blog

router = APIRouter(prefix="/blog")


@router.get("/tags", dependencies=[Depends(get_db_blog)])
async def get_tags():
    sql = """
    SELECT count(1), t.title, t.slug, pt.post_tags_id
    FROM posts p
    JOIN posts_post_tags pt ON p.id = pt.posts_id
    JOIN post_tags t ON t.id = pt.post_tags_id  
    GROUP BY pt.post_tags_id, t.title, t.slug;
    """
    ret = []
    rows = db_blog.execute_sql(sql).fetchall()
    for row in rows:
        count = row[0]
        title = row[1]
        slug = row[2]
        value = {"count": count, "title": title, "slug": slug}
        ret.append(value)

    return ret


@router.get("/categories", dependencies=[Depends(get_db_blog)])
async def get_categories():
    sql = """
    SELECT count(1), c.name, c.slug, c.id
    FROM posts p
    JOIN posts_post_categories pc ON p.id = pc.posts_id  
    JOIN post_categories c ON c.id = pc.post_categories_id
    GROUP BY c.name, c.slug, c.id
    """
    ret = []
    rows = db_blog.execute_sql(sql).fetchall()
    for row in rows:
        count = row[0]
        name = row[1]
        slug = row[2]
        value = {"count": count, "name": name, "slug": slug}
        ret.append(value)

    return ret
