import logging
from datetime import datetime

import requests
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.http.api.doc_pages import content_medium
from app.models.post import Post

from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/posts")

executor = ThreadPoolExecutor(max_workers=5)


@router.post("/")
async def add(request: Request):
    data = await request.json()
    logging.info(data)
    medium_id = data.get("medium_id")
    auto_translate = data.get("auto_translate")

    content = data.get("content")
    if not medium_id and not content:
        return JSONResponse(status_code=400, content='{"error": "request invalid"}')

    if medium_id:
        content = content_medium(medium_id)
    else:
        medium_id = str(datetime.now())

    if not content:
        return {"error": "content empty"}

    # logging content with medium_id
    logging.info(f"content: {content}")

    # translate and insert
    executor.submit(lambda: Post.add(medium_id, content, auto_translate))
    # result = Post.add(medium_id, content)

    return {"result": True}


@router.post("/vectorize")
async def vectorize_posts(request: Request):
    """
    Create vector embeddings for posts content
    """
    try:
        sql = """
        SELECT ai.create_vectorizer(
            'posts'::regclass,
            destination => 'posts_content_embeddings',
            embedding => ai.embedding_openai('text-embedding-3-small', 768),
            chunking => ai.chunking_recursive_character_text_splitter('content_zh')
        );
        """
        
        # Execute SQL using the database connection
        from app.providers.database import db_blog
        db_blog.execute_sql(sql)
        
        return {"status": "success", "message": "Posts vectorization completed"}
    except Exception as e:
        logging.error(f"Error during vectorization: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.post("/search")
async def search_posts(request: Request):
    """
    Search posts using vector similarity
    """
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Query string is required"}
            )
            
        sql = """
        SELECT
            chunk,
            embedding <=> ai.openai_embed('text-embedding-3-small', %s, dimensions=>768) as distance
        FROM posts_content_embeddings
        ORDER BY distance
        LIMIT 10;
        """
        
        # Execute SQL using the database connection
        from app.providers.database import db_blog
        cursor = db_blog.execute_sql(sql, (query,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "content": row[0],
                "distance": float(row[1])
            })
        
        return {
            "status": "success", 
            "results": results
        }
    except Exception as e:
        logging.error(f"Error during vector search: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
