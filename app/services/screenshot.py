import os
import base64
import logging
from playwright.async_api import async_playwright
from app.services.file_service import FileService

class ScreenshotService:
    def __init__(self):
        self.base_url = "https://directus.aimazing.site/assets"
        self.file_service = FileService()
        
    async def take_screenshot(self, url: str) -> str:
        """
        对网站进行截图并上传到服务器
        
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
            
            # 使用 playwright 进行截图
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url)
                await page.wait_for_load_state('networkidle')
                await page.screenshot(path=screenshot_path, full_page=True)
                await browser.close()
            
            # 将截图文件转换为base64
            with open(screenshot_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode()
            
            # 构造data URI
            data_uri = f"data:image/png;base64,{base64_image}"
            
            # 上传到服务器
            file_id = await self.file_service.upload_file_from_url(data_uri)
            
            # 删除临时文件
            os.remove(screenshot_path)
            
            if file_id:
                return f"{self.base_url}/{file_id}"
            return ""
            
        except Exception as e:
            logging.error(f"Error taking screenshot: {str(e)}")
            return ""