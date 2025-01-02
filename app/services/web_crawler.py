import asyncio
import logging
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup

class WebCrawler:
    def __init__(self, start_url: str, max_depth: int = 3, max_pages: int = 100):
        """初始化爬虫
        
        Args:
            start_url: 起始URL
            max_depth: 最大爬取深度，默认3级
            max_pages: 最大爬取页面数，默认100个
        """
        self.start_url = start_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited_urls = set()
        self.data = {}  # 存储所有页面的源码

    def _is_same_domain(self, url: str) -> bool:
        """检查URL是否属于同一域名"""
        try:
            return urlparse(url).netloc == urlparse(self.start_url).netloc
        except:
            return False

    def _is_valid_url(self, url: str) -> bool:
        """检查URL是否有效且应该被爬取"""
        try:
            parsed = urlparse(url)
            # 基本URL检查
            if not all([parsed.scheme, parsed.netloc]) or parsed.scheme not in ['http', 'https']:
                return False

            # 检查是否同域名
            if not self._is_same_domain(url):
                return False

            # 忽略特定类型的URL
            ignore_patterns = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar',
                'login', 'signin', 'signup', 'register', 'auth',
                'cart', 'checkout', 'account',
                'privacy',
                'post', 'blog', 'affiliate'
            ]
            path_lower = parsed.path.lower()
            return not any(pattern in path_lower for pattern in ignore_patterns)

        except Exception as e:
            logging.error(f"Error validating URL {url}: {str(e)}")
            return False

    def _extract_links(self, html: str, base_url: str) -> set:
        """从HTML中提取链接"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = set()
            for a in soup.find_all('a', href=True):
                url = urljoin(base_url, a['href'])
                if self._is_valid_url(url):
                    links.add(url)
            return links
        except Exception as e:
            logging.error(f"Error extracting links from {base_url}: {str(e)}")
            return set()

    async def _fetch_url(self, session: aiohttp.ClientSession, url: str) -> tuple:
        """获取URL的内容"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    return html, True
                else:
                    logging.error(f"Failed to fetch {url}: status={response.status}")
                    return "", False
        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            return "", False

    async def _crawl_url(self, session: aiohttp.ClientSession, url: str, depth: int):
        """爬取单个URL及其内链"""
        if depth > self.max_depth or len(self.visited_urls) >= self.max_pages or url in self.visited_urls:
            return

        self.visited_urls.add(url)
        logging.info(f"Crawling {url} (depth={depth}, visited={len(self.visited_urls)})")
        
        html, success = await self._fetch_url(session, url)
        
        if not success:
            return

        # 存储页面源码
        self.data[url] = html
        logging.info(f"Successfully fetched {url} ({len(html)} chars)")

        # 如果还没到最大深度，继续爬取内链
        if depth < self.max_depth and len(self.visited_urls) < self.max_pages:
            links = self._extract_links(html, url)
            logging.info(f"Found {len(links)} links in {url}")
            
            # 顺序爬取内链
            for link in links:
                if link not in self.visited_urls and len(self.visited_urls) < self.max_pages:
                    await self._crawl_url(session, link, depth + 1)

    async def crawl(self) -> dict:
        """开始爬取网页"""
        try:
            async with aiohttp.ClientSession() as session:
                await self._crawl_url(session, self.start_url, 0)
            return self.data
        except Exception as e:
            logging.error(f"Crawl error: {str(e)}")
            return self.data