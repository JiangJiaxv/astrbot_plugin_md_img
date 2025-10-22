from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import re
import aiohttp
import aiofiles
import os
import tempfile
from urllib.parse import urlparse
import asyncio

@register("markdown_image_processor", "YourName", "将Markdown图片转换为企业微信可识别的格式", "1.0.0")
class MarkdownImageProcessor(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.temp_dir = None

    async def initialize(self):
        """插件初始化，创建临时目录"""
        self.temp_dir = tempfile.mkdtemp(prefix="astrbot_images_")
        logger.info(f"图片处理插件初始化完成，临时目录: {self.temp_dir}")

    async def terminate(self):
        """插件销毁，清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info("已清理临时文件")

    def extract_image_urls(self, text: str) -> list:
        """从Markdown文本中提取图片URL"""
        # 匹配Markdown图片格式: ![](url) 或 ![alt](url)
        pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
        urls = re.findall(pattern, text)
        logger.info(f"提取到 {len(urls)} 个图片URL: {urls}")
        return urls

    async def download_image(self, url: str) -> str:
        """下载图片到临时目录"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # 获取文件扩展名
                        parsed_url = urlparse(url)
                        path = parsed_url.path
                        ext = os.path.splitext(path)[1] or '.jpg'
                        
                        # 生成临时文件名
                        import uuid
                        filename = f"{uuid.uuid4()}{ext}"
                        filepath = os.path.join(self.temp_dir, filename)
                        
                        # 保存文件
                        async with aiofiles.open(filepath, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        logger.info(f"图片下载成功: {url} -> {filepath}")
                        return filepath
                    else:
                        logger.error(f"下载图片失败，状态码: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"下载图片时出错: {e}")
            return None

    def convert_markdown_to_wechat(self, text: str, image_paths: list) -> str:
        """将Markdown文本转换为企业微信格式"""
        # 移除Markdown图片语法，替换为纯文本描述
        # 保留图片描述文本
        pattern = r'!\[(.*?)\]\([^\)]+\)'
        result = re.sub(pattern, r'\1', text)
        
        # 如果成功下载了图片，添加提示信息
        if image_paths:
            result += f"\n\n📷 已处理 {len(image_paths)} 张图片"
        
        return result

    @filter.message
    async def process_markdown_images(self, event: AstrMessageEvent):
        """处理包含Markdown图片的消息"""
        message_str = event.message_str
        
        # 检查是否包含Markdown图片
        image_urls = self.extract_image_urls(message_str)
        
        if not image_urls:
            # 没有图片，直接返回原消息
            return
        
        logger.info(f"检测到Markdown图片消息，开始处理...")
        
        # 下载所有图片
        downloaded_images = []
        for url in image_urls:
            image_path = await self.download_image(url)
            if image_path:
                downloaded_images.append(image_path)
        
        # 转换消息格式
        converted_message = self.convert_markdown_to_wechat(message_str, downloaded_images)
        
        # 发送转换后的文本消息
        yield event.plain_result(converted_message)
        
        # 发送下载的图片
        for image_path in downloaded_images:
            if os.path.exists(image_path):
                try:
                    yield event.image_result(image_path)
                    logger.info(f"已发送图片: {image_path}")
                except Exception as e:
                    logger.error(f"发送图片失败: {e}")
        
        # 清理临时图片文件
        for image_path in downloaded_images:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                logger.error(f"清理临时文件失败: {e}")

    @filter.command("test_image")
    async def test_image_processing(self, event: AstrMessageEvent):
        """测试图片处理功能"""
        test_message = """### 测试图片
![](https://fastgpt.hz.flexiblecircuit.cn/api/common/file/read/685b6e7fe92629b53a08d36b-1761093814000.svg?token=test)"""
        
        yield event.plain_result("发送测试消息...")
        yield event.plain_result(test_message)
