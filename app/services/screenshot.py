import os
import sys
import base64
import logging
import asyncio
from pyppeteer import launch
from app.services.file_service import FileService

class ScreenshotService:
    def __init__(self):
        self.base_url = "https://directus.aimazing.site/assets"
        self.file_service = FileService()
        
    async def take_screenshot(self, url: str) -> str:
        """
        使用pyppeteer对网站进行截图并上传到服务器
        
        Args:
            url: 要截图的网站URL
            
        Returns:
            str: 截图的URL，格式为 https://directus.aimazing.site/assets/{file_id}
                 如果截图失败返回空字符串
        """
        try:
            # 创建临时文件路径
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            screenshot_path = os.path.join(temp_dir, "screenshot.png")
            logging.info(f"Screenshot path: {screenshot_path}")
            
            # 设置环境变量来指定Chromium的下载镜像
            os.environ['PYPPETEER_DOWNLOAD_HOST'] = 'http://npm.taobao.org/mirrors'
            
            # 启动浏览器，使用系统安装的Chrome
            browser_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-zygote',
                '--single-process'
            ]
            
            if sys.platform == 'win32':
                # Windows下尝试使用本地Chrome
                chrome_paths = [
                    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
                    os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe'),
                ]
                
                chrome_exe = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_exe = path
                        break
                
                if chrome_exe:
                    browser = await launch(
                        executablePath=chrome_exe,
                        args=browser_args,
                        headless=True,
                        handleSIGINT=False,
                        handleSIGTERM=False,
                        handleSIGHUP=False
                    )
                else:
                    # 如果找不到本地Chrome，使用下载的版本
                    browser = await launch(
                        args=browser_args,
                        headless=True,
                        handleSIGINT=False,
                        handleSIGTERM=False,
                        handleSIGHUP=False
                    )
            else:
                # Linux下使用默认配置
                browser = await launch(
                    args=browser_args,
                    headless=True,
                    handleSIGINT=False,
                    handleSIGTERM=False,
                    handleSIGHUP=False
                )
            
            try:
                # 创建新页面
                page = await browser.newPage()
                
                # 设置视口大小
                await page.setViewport({'width': 1920, 'height': 1080})
                
                # 访问URL
                await page.goto(url, {
                    'waitUntil': 'networkidle0',
                    'timeout': 30000
                })
                
                # 等待页面加载完成
                await page.waitFor(2000)  # 额外等待2秒确保动态内容加载
                
                # 截取全页面截图
                await page.screenshot({
                    'path': screenshot_path
                })
                
            finally:
                 # 确保页面关闭
                if page:
                    await page.close()
                # 确保浏览器关闭
                await browser.close()
            
            # 上传到服务器
            file_id = await self.file_service.upload_file(screenshot_path, 'image/png')
            
            # 删除临时文件
            os.remove(screenshot_path)
            
            if file_id:
                return f"{self.base_url}/{file_id}"
            return ""
            
        except Exception as e:
            logging.error(f"Error taking screenshot: {str(e)}")
            return ""

if __name__ == "__main__":
    # 使用新的事件循环
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    async def main():
        screenshot_service = ScreenshotService()
        result = await screenshot_service.take_screenshot("https://www.baidu.com")
        print(f"Screenshot URL: {result}")
    
    asyncio.run(main())