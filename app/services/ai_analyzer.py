from typing import Dict, List
import logging
import json
import re
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.models.models import DataCategory, AITag
from config.config import settings
from bs4 import BeautifulSoup

class AIAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(
            #model="google/gemini-flash-1.5",
            model='deepseek-reasoner',
            temperature=0.2,
            #api_key=settings.OPENROUTER_KEY,
            api_key='sk-47cf411ee6e34ef0bc2ae77ac412194b',
            # base_url="https://openrouter.ai/api/v1",
            base_url="https://api.deepseek.com"
        )
        # 加载分类和标签数据
        self.categories = self._load_categories()
        self.tags = self._load_tags()

    async def analyze(self, site_data: dict) -> dict:
        """分析网站内容，提取所有需要的信息"""
        try:
            if not self.categories or not self.tags:
                raise ValueError("Categories or tags not loaded")
            # 合并所有内容
            content = self._merge_site_content(site_data)
            if not content:
                raise ValueError("No valid content found")
            
            # 构建分类和标签提示
            categories_prompt = "\n".join([
                f"{cat['id']}. {cat['name']}" + (f" ({cat['sub_name']})" if cat['sub_name'] else "")
                for cat in self.categories
            ])
            
            tags_prompt = "\n".join([
                f"{tag['id']}. {tag['name']}"
                for tag in self.tags
            ])

            # 一次性分析所有内容
            prompt = ChatPromptTemplate.from_messages([
                ("system", """
                你是一个专业的内容分析AI助手。请分析网站内容，提取以下所有信息。使用中文输出，不要使用英文。
                注意：如果内容中没有明确提到的信息，请不要随意猜测或填充。

                1. 基本信息：
                   - title: AI工具的名称
                   - slug: title slugify
                   - summary: 100字以内的简短介绍
                   - logo: 网站Logo的URL，优先选择高分辨率图片，使用 ICON 信息作为备选
                   - region: 工具所属地区，如 cn、us、uk、au 等，全小写国家与地区代码
                   - free_plan: 是否有免费计划
                   - details: 详细介绍工具的功能、特点、使用场景，以博文形式撰写，包含以下内容：1)工具的主要功能和特色；2)适用的场景和用户群体；3)使用建议和技巧。采用生动、专业的语言，使读者能够快速理解工具价值，500-1000字

                2. 定价信息：
                   - pricing_plans: 定价方案列表，每个方案包含：
                     * name: 计划名称
                     * service: 详细的服务内容描述, markdown 格式数据。
                     * price_currency: 货币单位(如USD)
                     * price_month: 月付价格
                     * price_year: 年付价格
                     * price_lifetime: 终身价格(如果有)
                     * recommended: 是否为推荐方案
                   注意：只有在内容中明确提到价格信息时才填写，不要猜测或填写不确定的价格

                3. 分类和标签：
                   - category_ids: 从以下选项中选择1-2个最相关的分类ID：
                     {categories_prompt}
                   
                   - tag_ids: 从以下选项中选择3-5个相关的标签ID：
                     {tags_prompt}

                请以JSON格式输出所有信息。对于找不到或不确定的字段，请使用空字符串或空数组，不要随意填充：
                {{
                    "title": "工具名称",
                    "summary": "简短介绍",
                    "logo": "logo url",
                    "region": "CN",
                    "free_plan": true,
                    "details": "详细介绍",
                    "pricing_plans": [
                        {{
                            "name": "计划名称",
                            "service": "服务内容",
                            "price_currency": "USD",
                            "price_month": "29.99",
                            "price_year": "299.99",
                            "price_lifetime": "999.99",
                            "recommended": true
                        }}
                    ],
                    "category_ids": [1, 2],
                    "tag_ids": [1, 2, 3, 4, 5]
                }}
                """),
                ("human", "{content}")
            ])

            logging.info(f"Analyzing content ({len(content)} chars)")
            result = await (prompt | self.llm).ainvoke({
                "content": content,
                "categories_prompt": categories_prompt,
                "tags_prompt": tags_prompt
            })
            
            parsed = self._parse_result(result)
            if not parsed:
                logging.error("Failed to parse AI response")
                return {}
                
            logging.info(f"Successfully analyzed content: {parsed.get('title', 'No title')}")
            return parsed

        except Exception as e:
            logging.error(f"Error in analyze: {str(e)}")
            return {}

    def _merge_site_content(self, site_data: dict) -> str:
        """合并所有网站内容"""
        try:
            if not site_data or not isinstance(site_data, dict):
                raise ValueError("Invalid site_data format")
            
            # 记录处理的页面数量
            logging.info(f"Processing {len(site_data)} pages")
            
            merged_content = []
            for url, html in site_data.items():
                try:
                    if not html or not isinstance(html, str):
                        logging.warning(f"Invalid HTML content for URL: {url}")
                        continue
                        
                    content = self._extract_content_from_html(html)
                    if content:
                        # 添加 URL 作为内容的标识
                        merged_content.append(f"URL: {url}\n{content}")
                        logging.debug(f"Extracted content from {url}: {len(content)} chars")
                except Exception as e:
                    logging.error(f"Error processing URL {url}: {str(e)}")
                    continue
            
            if not merged_content:
                raise ValueError("No valid content extracted from any page")
            
            # 合并所有内容
            result = "\n\n".join(merged_content)
            logging.info(f"Total merged content length: {len(result)} chars")
            return result
            
        except Exception as e:
            logging.error(f"Error in _merge_site_content: {str(e)}")
            raise

    def _extract_content_from_html(self, html: str) -> str:
        """从HTML中提取有效内容和图标信息"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取favicon和icon信息
            icon_links = []
            head = soup.find('head')
            if head:
                # 查找所有可能的图标链接
                for link in head.find_all('link', rel=lambda x: x and ('icon' in x.lower() or 'shortcut' in x.lower())):
                    href = link.get('href')
                    if href:
                        icon_links.append(href)
                        
            # 移除无用标签，但保留head
            for tag in soup.find_all(['script', 'style', 'noscript', 'iframe', 'nav', 'footer']):
                tag.decompose()
            
            # 获取主要内容
            main_content = soup.get_text(separator=' ', strip=True)
            
            # 如果找到了图标链接，添加到内容中
            if icon_links:
                main_content = f"ICONS: {' '.join(icon_links)}\n{main_content}"
            
            return main_content
            
        except Exception as e:
            logging.error(f"Error extracting content from HTML: {str(e)}")
            return ""

    def _parse_result(self, result) -> dict:
        """解析AI返回的结果"""
        try:
            content = result.content if hasattr(result, 'content') else str(result)
            
            # 记录原始内容以便调试
            logging.debug(f"Original content: {content}")
            
            # 提取 JSON 部分
            json_str = self._extract_json_from_text(content)
            if not json_str:
                logging.warning("No JSON found in content")
                return {}
            
            # 清理 JSON 字符串
            cleaned_json = self._clean_json_string(json_str)
            logging.debug(f"Cleaned JSON: {cleaned_json}")
            
            try:
                # 首先尝试直接解析
                return json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                logging.warning(f"Initial JSON parsing failed: {str(e)}")
                try:
                    # 尝试使用 ast.literal_eval 作为备选方案
                    import ast
                    # 将 true/false/null 替换为 Python 的 True/False/None
                    py_str = cleaned_json.replace('true', 'True').replace('false', 'False').replace('null', 'None')
                    return ast.literal_eval(py_str)
                except Exception as e:
                    logging.error(f"Backup parsing failed: {str(e)}")
                    return {}
                
        except Exception as e:
            logging.error(f"Error parsing result: {str(e)}")
            return {}

    def _extract_json_from_text(self, text: str) -> str:
        """从文本中提取 JSON 部分"""
        try:
            # 尝试找到 JSON 开始的 {
            start_idx = text.find('{')
            if start_idx == -1:
                return ""
            
            # 计算括号匹配
            count = 0
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    count += 1
                elif text[i] == '}':
                    count -= 1
                if count == 0:
                    return text[start_idx:i+1]
            
            return ""
        except Exception as e:
            logging.error(f"Error extracting JSON: {str(e)}")
            return ""

    def _clean_json_string(self, json_str: str) -> str:
        """清理和修复常见的 JSON 格式问题"""
        try:
            # 移除 BOM 和其他特殊字符
            json_str = json_str.strip().lstrip('\ufeff')
            
            # 替换错误的引号
            json_str = json_str.replace('"', '"').replace('"', '"')
            json_str = json_str.replace(''', "'").replace(''', "'")
            
            # 处理常见的布尔值和 null
            json_str = re.sub(r':\s*true\s*([,}])', r': true\1', json_str, flags=re.IGNORECASE)
            json_str = re.sub(r':\s*false\s*([,}])', r': false\1', json_str, flags=re.IGNORECASE)
            json_str = re.sub(r':\s*null\s*([,}])', r': null\1', json_str, flags=re.IGNORECASE)
            
            # 处理数字值
            json_str = re.sub(r':\s*(\d+\.?\d*)\s*([,}])', r': \1\2', json_str)
            
            return json_str
        except Exception as e:
            logging.error(f"Error cleaning JSON string: {str(e)}")
            return json_str

    def _load_categories(self) -> List[Dict]:
        """加载所有数据类别"""
        try:
            from app.database import db_connection
            with db_connection():
                categories = []
                for category in DataCategory.select().where(DataCategory.parent == 4):
                    categories.append({
                        'id': category.id,
                        'name': category.name,
                        'sub_name':category.sub_name
                    })
                return categories
        except Exception as e:
            logging.error(f"Error loading categories: {str(e)}")
            return []

    def _load_tags(self) -> List[Dict]:
        """加载所有标签"""
        try:
            from app.database import db_connection
            with db_connection():
                tags = []
                for tag in AITag.select():
                    tags.append({
                        'id': tag.id,
                        'name': tag.title
                    })
                return tags
        except Exception as e:
            logging.error(f"Error loading tags: {str(e)}")
            return []