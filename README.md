# 批量处理在线视频

一个用于批量下载 YouTube 视频及字幕，整理字幕格式，翻译字幕，合成 mp4 格式的带双语硬字幕的视频的 Python 工具。

## 功能特点

- 支持从 YouTube 下载视频和字幕
- 自动处理字幕格式，提取有效字幕
- 支持使用 Google Translate API 翻译字幕
- 生成双语字幕视频
- 支持从 YouTube 频道批量获取视频链接
- 使用 SQLite 数据库存储元数据
- 支持代理服务器配置
- 支持单元测试

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/batch-process-online-video.git
cd batch-process-online-video
```

2. 创建虚拟环境并激活：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 配置

1. 复制 `config.yaml.example` 为 `config.yaml`
2. 编辑 `config.yaml` 文件，填入必要的配置信息：
   - Google Translate API 密钥
   - 代理服务器设置（如果需要）
   - 输出目录设置

## 使用方法

1. 准备任务文件：
   在 `tasks.txt` 中添加要下载的视频 URL，每行一个。

2. 运行程序：
```bash
python -m batch_process_online_video.main
```

3. 运行测试：
```bash
pytest
```

## 目录结构

```
batch-process-online-video/
├── batch_process_online_video/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── video_downloader.py
│   ├── subtitle_processor.py
│   └── main.py
├── tests/
│   └── test_channel_extractor.py
├── config.yaml
├── tasks.txt
├── requirements.txt
└── README.md
```

## 许可证

MIT License
