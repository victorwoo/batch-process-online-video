import yt_dlp
import os
import subprocess
import sys

def download_and_convert_subs(url: str, output_dir: str = "downloads", lang: str = 'en'):
    """2025.3.25 专属修复：精准匹配后处理器键名"""
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'writesubtitles': True,
        'subtitleslangs': [lang],
        'postprocessors': [],
        'quiet': False,
        'no_warnings': True,
    }

    # 精准匹配 2024.11.28+ 后处理器命名（双 P 后缀）
    pp_key = 'FFmpegSubtitlesConvertorPP'  # 关键修复：双 P 后缀
    try:
        getattr(yt_dlp.postprocessor, pp_key)  # 验证类存在
        ydl_opts['postprocessors'].append({
            'key': pp_key,  # 必须与类名完全一致
            'format': 'srt',
            'when': 'after_dl',
        })
    except AttributeError:
        _diagnose_postprocessor_error()
        return

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'video').replace('/', '_')
            srt_path = f"{output_dir}/{video_title}.{lang}.srt"

            if os.path.exists(srt_path):
                _print_success(srt_path)
            else:
                _print_failure(srt_path, lang)

    except yt_dlp.utils.DownloadError as e:
        _handle_download_error(e, lang)

def _diagnose_postprocessor_error():
    """深度诊断后处理器缺失原因"""
    print("\n🔍 后处理器诊断：")
    print("1. 确认 yt-dlp 版本：", yt_dlp.__version__)
    print("2. 检查后处理器列表：")
    available_pps = [
        p for p in dir(yt_dlp.postprocessor)
        if p.endswith('PP') and p.startswith('FFmpeg')
    ]
    if available_pps:
        print(f"   可用后处理器：{', '.join(available_pps)}")
        print("   提示：请使用上述列表中的键名（去掉 PP 后缀）")
    else:
        print("   无可用字幕处理器，可能安装了精简版 yt-dlp")
    print("3. 推荐修复：")
    print("   pip uninstall -y yt-dlp && pip install yt-dlp[ffmpeg]")
    sys.exit(1)

def _print_success(srt_path):
    """成功提示（含文件信息）"""
    size = os.path.getsize(srt_path)
    print(f"\n🎉 转换成功！SRT 路径：{srt_path}")
    print(f"   大小：{size} 字节 | 更新时间：{os.path.getmtime(srt_path):.0f}")

def _print_failure(srt_path, lang):
    """失败提示（含排查步骤）"""
    print(f"\n🚨 转换失败：未找到 {srt_path}")
    print("排查步骤：")
    print("1. 确认视频包含软字幕（非硬字幕）")
    print("2. 检查语言代码是否正确（当前：{lang}，示例：'en', 'zh-Hans'）")
    print("3. 尝试命令行验证：yt-dlp --write-sub --convert-subs srt {url}")

def _handle_download_error(e, lang):
    """下载错误处理（含字幕排查）"""
    print(f"\n⚠️ 下载失败：{str(e)}")
    if "No subtitles found" in str(e):
        print("字幕排查：")
        print("1. 确认视频有字幕：在 YouTube 网页检查字幕开关")
        print("2. 尝试自动字幕：lang='auto'（需视频支持自动生成）")
    elif "Non-zero exit code" in str(e):
        print("FFmpeg 错误：尝试重新安装 FFmpeg 或更新 yt-dlp")

if __name__ == "__main__":
    # 强制使用双 P 后缀的正确键名
    download_and_convert_subs(
        "https://www.youtube.com/watch?v=p3fkSGSSYVA",
        lang='en'  # 替换为目标语言（如 'zh-Hans'）
    )
