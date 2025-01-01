import aiohttp
import json
import logging
import asyncio
import sys
import os
from typing import Optional
from uuid import UUID

'''
curl -i -X POST \
   -H "Content-Type:application/json" \
   -d \
'{"url": "https://pics6.baidu.com/feed/58ee3d6d55fbb2fb2162aa9ea65104ab4723dc98.jpeg@f_auto?token=9e91174778e579607d534fd43a008025"}' \
 'https://directus.aimazing.site/files/import'

返回的数据，是这种。

{
    "data": {
        "id": "377676eb-2d22-477d-a297-9a9fef597ff6",
        "storage": "local",
        "filename_disk": "377676eb-2d22-477d-a297-9a9fef597ff6.jpeg@f_auto",
        "filename_download": "58ee3d6d55fbb2fb2162aa9ea65104ab4723dc98.jpeg@f_auto",
        "title": "58ee3d6d55fbb2fb2162aa9ea65104ab4723dc98.jpeg@f Auto",
        "type": "image/jpeg",
        "folder": null,
        "uploaded_by": "f4662431-27b7-421a-858a-b43cfa1ea61e",
        "created_on": "2024-12-31T15:56:57.757Z",
        "modified_by": null,
        "modified_on": "2024-12-31T15:56:57.928Z",
        "charset": null,
        "filesize": "51875",
        "width": 640,
        "height": 413,
        "duration": null,
        "embed": null,
        "description": null,
        "location": null,
        "tags": null,
        "metadata": {
        },
        "focal_point_x": null,
        "focal_point_y": null,
        "tus_id": null,
        "tus_data": null,
        "uploaded_on": "2024-12-31T15:56:57.927Z"
    }
}

'''
class FileService:
    def __init__(self):
        self.base_url = 'https://directus.aimazing.site'
        
    async def upload_file(self, file_path: str, content_type: str = None) -> Optional[UUID]:
        """
        上传本地文件到Directus服务器
        
        Args:
            file_path: 本地文件路径
            content_type: 文件类型，如 'image/png'
            
        Returns:
            UUID: 上传成功返回文件ID，失败返回None
        """
        try:
            if not os.path.exists(file_path):
                logging.error(f"File not found: {file_path}")
                return None
                
            # 如果没有指定content_type，尝试猜测
            if not content_type:
                if file_path.lower().endswith('.png'):
                    content_type = 'image/png'
                elif file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                    content_type = 'image/jpeg'
                else:
                    content_type = 'application/octet-stream'
            
            # 准备文件数据
            data = aiohttp.FormData()
            data.add_field('file',
                          open(file_path, 'rb'),
                          filename=os.path.basename(file_path),
                          content_type=content_type)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/files",
                    data=data
                ) as response:
                    if response.status != 200:
                        logging.error(f"Failed to upload file. Status: {response.status}")
                        return None
                        
                    result = await response.json()
                    
                    if not result or 'data' not in result or 'id' not in result['data']:
                        logging.error("Invalid response format")
                        return None
                        
                    file_id = result['data']['id']
                    logging.info(f"File uploaded successfully. ID: {file_id}")
                    return UUID(file_id)
                    
        except Exception as e:
            logging.error(f"Error uploading file: {str(e)}")
            return None
            
    async def upload_file_from_url(self, url: str) -> Optional[UUID]:
        """
        从URL上传文件到Directus服务器
        
        Args:
            url: 文件的URL
            
        Returns:
            UUID: 上传成功返回文件ID，失败返回None
        """
        try:
            if not url:
                return None
                
            payload = { 
                "url": url
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/files/import",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        logging.error(f"Failed to upload file. Status: {response.status}")
                        return None
                        
                    data = await response.json()
                    
                    if not data or 'data' not in data or 'id' not in data['data']:
                        logging.error("Invalid response format")
                        return None
                        
                    file_id = data['data']['id']
                    logging.info(f"File uploaded successfully. ID: {file_id}")
                    return UUID(file_id)
                    
        except Exception as e:
            logging.error(f"Error uploading file: {str(e)}")
            return None


if __name__ == "__main__":
    async def main():
        file_service = FileService()
        result = await file_service.upload_file("./test.png")
        print(f"Local file upload result: {result}")
        
        result = await file_service.upload_file_from_url("https://pics6.baidu.com/feed/58ee3d6d55fbb2fb2162aa9ea65104ab4723dc98.jpeg@f_auto?token=9e91174778e579607d534fd43a008025")
        print(f"URL upload result: {result}")

    # 在Windows上需要使用这个事件循环策略
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())