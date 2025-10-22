# Markdown图片处理器

AstrBot插件，用于将Markdown格式的图片转换为企业微信可识别的格式。

## 功能特性

- 🔍 自动检测Markdown格式的图片链接
- 📥 下载远程图片到本地
- 🖼️ 将图片发送给企业微信机器人
- 🧹 自动清理临时文件
- 📝 保留原始文本内容

## 使用方法

1. 安装插件到AstrBot
2. 当收到包含Markdown图片的消息时，插件会自动处理
3. 支持的消息格式：
   ```
   ### 标题
   ![](https://example.com/image.png)
   ```

## 测试命令

发送 `/test_image` 来测试插件功能

## 依赖

- aiohttp>=3.8.0
- aiofiles>=23.0.0

## 支持

[帮助文档](https://astrbot.app)
