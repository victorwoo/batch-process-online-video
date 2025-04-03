# 批量处理在线视频

一个用于批量下载 YouTube 视频及字幕，整理字幕格式，翻译字幕，合成 mp4 格式的带双语硬字幕的视频的 Python 工具。

## 功能特点

- 支持从 YouTube 下载视频和字幕
- 自动处理字幕格式，提取有效字幕
- 生成双语字幕视频
- 支持从 YouTube 频道批量获取视频链接
- 支持代理服务器配置

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

4. 安装 Ollama 和 LLM

安装 Ollama，然后执行以下命令安装 LLM：

```bash
ollama pull qwen2.5:7b-instruct
```

## 配置

在项目根目录下放置一个 `.env` 文件，内容参考 `example/example.env`

## 使用方法

1. 准备任务文件：
   在 `tasks.txt` 中添加要下载的视频 URL，每行一个。

2. 运行程序：
```bash
python -m batch_process_online_video.main
```

## 目录结构
