import logging

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


@router.get("/posts/{slug}/navs", dependencies=[Depends(get_db_blog)])
async def get_navs(slug: str):
    sql = f"""
    select slug, prev_slug, prev_title,next_slug,next_title
    from (
        select  slug,
                lag(slug) over (order by id desc) as prev_slug,
                lag(title) over (order by id desc) as prev_title,
                lead(slug) over (order by id desc) as next_slug,
                lead(title) over (order by id desc) as next_title
        from posts where status='published'
        ) x
    where slug ='{slug}';
    """
    rows = db_blog.execute_sql(sql).fetchall()
    if not rows:
        return {}
    row = rows[0]
    slug = row[0]

    return {
        "slug": slug,
        "prev": {"slug": row[1], "title": row[2]},
        "next": {"slug": row[3], "title": row[4]},
    }


@router.post("/posts/{slug}/view_counts", dependencies=[Depends(get_db_blog)])
async def update_read_count(slug: str):
    if not slug:
        return {"result": False}

    sql = f"""
    update posts set view_count = view_count+1 where slug='{slug}'
    """
    # logging.info(sql)
    rows = db_blog.execute_sql(sql=sql)
    logging.info(f"{rows}")

    return {"result": True}


@router.get("/posts/{slug}/relations", dependencies=[Depends(get_db_blog)])
async def get_related(slug: str, limit: int):
    """
    没用了
    """
    sql = f"""
    SELECT ps.slug, ps.title, ps.feature_image, ps.updated_at, cts.name, cts.slug
    FROM posts ps
             JOIN posts_post_categories ps_cts ON ps.id = ps_cts.posts_id
             JOIN post_categories cts ON cts.id = ps_cts.post_categories_id
    WHERE cts.slug = '{slug}'
    order by updated_at desc
    LIMIT {limit};
    """
    rows = db_blog.execute_sql(sql).fetchall()
    if not rows:
        return []
    ret = []

    return ret
