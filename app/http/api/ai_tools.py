import logging
import asyncio
from operator import index
import sys
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from app.database import db_new
from app.services.web_crawler import WebCrawler
from app.services.ai_analyzer import AIAnalyzer
from app.services.screenshot import ScreenshotService
from app.services.file_service import FileService
from app.models.models import AITool, PricingPlan, AIToolCategory, AIToolTag
router = APIRouter(prefix="/ai_tools")

# class PricingPlan2(BaseModel):
#     name: str
#     service: str
#     price_currency: str
#     price_month: Optional[str]
#     price_year: Optional[str]
#     price_lifetime: Optional[str]
#     price_day: Optional[str]
#     recommended: bool = False
#
# class AIToolCreate2(BaseModel):
#     title: str
#     slug: str
#     summary: str
#     logo: str
#     url: str
#     region: str
#     free_plan: bool
#     details: str
#     pricing_plans: List[PricingPlan]
#     category_ids: List[int]
#     tag_ids: List[int]

@router.post("/analyze")
async def analyze_url(request: Request):
    """
    分析URL并创建AI工具记录
    """
    try:
        data = await request.json()
        url = data.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        # 1. 爬取网页内容
        crawler = WebCrawler(url)
        site_data = await crawler.crawl()

        # print(site_data)

        # 2. AI分析内容
        analyzer = AIAnalyzer()
        analysis_result = await analyzer.analyze(site_data)
        # print(analysis_result)

        # 3. 获取截图
        screenshot_service = ScreenshotService()
        screenshot_path = await screenshot_service.take_screenshot(url)

        # 4. 保存数据到数据库
        try:
            # 上传logo
            file_service = FileService()
            logo_id = None
            if analysis_result.get('logo'):
                logo_id = await file_service.upload_file_from_url(analysis_result['logo'])
                if not logo_id:
                    logging.warning(f"Failed to upload logo from URL: {analysis_result['logo']}")

            db_new.connect(reuse_if_open=True)
            with db_new.atomic():
                # 创建AI工具记录
                tool = AITool.create(
                    url=url,
                    title=analysis_result['title'],
                    slug=analysis_result['slug'],
                    summary=analysis_result['summary'],
                    details=f"![{analysis_result['title']}]({screenshot_path})\n\n" + analysis_result['details'] ,
                    logo=logo_id,  # 使用上传后的文件ID
                    region=analysis_result['region'],
                    free_plan=analysis_result['free_plan']
                )

                # 保存定价方案
                for index, plan in enumerate(analysis_result['pricing_plans']):
                    PricingPlan.create(
                        tool=tool,
                        sort=index,
                        name=plan['name'],
                        service=plan['service'],
                        price_currency=plan['price_currency'],
                        price_month=plan['price_month'],
                        price_year=plan['price_year'],
                        price_lifetime=plan['price_lifetime'],
                        recommended=plan['recommended']
                    )

                # 保存分类关联
                for category_id in analysis_result['category_ids']:
                    AIToolCategory.create(
                        ai_tools=tool,
                        data_categories_id=category_id
                    )

                # 保存标签关联
                for tag_id in analysis_result['tag_ids']:
                    AIToolTag.create(
                        ai_tools=tool,
                        ai_tags_id=tag_id
                    )
        finally:
            if not db_new.is_closed():
                db_new.close()

        return {
            "status": "success",
            "message": "AI tool analysis completed",
            "tool_id": tool.id
        }

    except Exception as e:
        logging.error(f"Error analyzing URL: {str(e)}",exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# async def create_ai_tool(analysis_result, screenshot_path):
#     now = datetime.now()
    
#     return await db.execute("""
#         INSERT INTO ai_tools (
#             status, title, slug, summary, details, logo, url,
#             region, free_plan, date_created, date_updated
#         ) VALUES (
#             'draft', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
#         ) RETURNING id
#     """, (
#         analysis_result.title,
#         analysis_result.slug,
#         analysis_result.summary,
#         analysis_result.details + f"\n![{analysis_result.title}]({screenshot_path})",
#         analysis_result.logo,
#         analysis_result.url,
#         analysis_result.region,
#         analysis_result.free_plan,
#         now,
#         now
#     ))

# async def save_pricing_plans(tool_id: int, pricing_plans: List[PricingPlan]):
#     for plan in pricing_plans:
#         await db.execute("""
#             INSERT INTO pricing_plans (
#                 tool, name, service, price_currency,
#                 price_month, price_year, price_lifetime,
#                 price_day, recommended
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """, (
#             tool_id,
#             plan.name,
#             plan.service,
#             plan.price_currency,
#             plan.price_month,
#             plan.price_year,
#             plan.price_lifetime,
#             plan.price_day,
#             plan.recommended
#         ))

# async def save_categories(tool_id: int, category_ids: List[int]):
#     for category_id in category_ids:
#         await db.execute("""
#             INSERT INTO ai_tools_data_categories (
#                 ai_tools_id, data_categories_id
#             ) VALUES (%s, %s)
#         """, (tool_id, category_id))

# async def save_tags(tool_id: int, tag_ids: List[int]):
#     for tag_id in tag_ids:
#         await db.execute("""
#             INSERT INTO ai_tools_ai_tags (
#                 ai_tools_id, ai_tags_id
#             ) VALUES (%s, %s)
#         """, (tool_id, tag_id)) 