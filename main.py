# 移除所有第三方依赖和复杂结构
import os
from typing import List
import subprocess
import json
import pysrt
import shlex
import shutil
import ollama
import yt_dlp
import ffmpeg
import mysql.connector
from datetime import datetime

#print(os.environ['BPOV_DB_USER'])

# 硬编码配置
class Config:
    proxy_enabled = True
    proxy_address = "127.0.0.1:7987"
    max_lines = 50  # 新增调试行数限制 (0=全部翻译)
    debug_video_file = ''#'1000 Ideas In Your Pocket.mp4'
    debug_subtitle_file = ''#'1000 Ideas In Your Pocket_orig.srt'
    debug_json_file = ''#'1000 Ideas In Your Pocket_orig.json'

# 数据库配置（需要用户自行填写）
DB_CONFIG = {
    'host': 'home.vichamp.com',
    # 'user': os.environ['BPOV_DB_USER'],          # 从环境变量读取
    # 'password': os.environ['BPOV_DB_PASSWORD'], # 从环境变量读取
    'user': 'smms',          # 从环境变量读取
    'password': 'Xk7#Qp@2!Lm', # 从环境变量读取
    'database': 'youtube',
    'port': 3306
}

def load_tasks(task_file: str) -> List[str]:
    """直接从tasks.txt读取URL"""
    with open(task_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def get_safe_filename(url, template='%(title)s.%(ext)s'):
    ydl_opts = {
        'outtmpl': template,  # 文件名模板
        'simulate': True,  # 模拟模式（不下载）
        'quiet': True,  # 禁用日志输出
        'restrictfilenames': False,  # 关键参数
        'windowsfilenames': True  # 保持默认值（True）
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 获取视频元数据（不下载）
            info = ydl.extract_info(url, download=False)
            # 生成转义后的文件名
            filename = ydl.prepare_filename(info)
            return filename, info
    except yt_dlp.utils.DownloadError as e:
        print(f"错误：{str(e)}")
        return None

# 新增日期格式转换函数
def format_date(date_str):
    return datetime.strptime(date_str, "%Y%m%d").date()

# 新增数据库保存函数
def save_to_database(info: dict):
    """保存视频元数据到数据库"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 插入频道数据
        channel_sql = """
        INSERT INTO channels (
            channel_id, channel_name, channel_url,
            uploader_name, uploader_id, uploader_url
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            channel_name = VALUES(channel_name),
            uploader_name = VALUES(uploader_name)
        """
        channel_values = (
            info['channel_id'],
            info.get('channel', ''),
            info.get('channel_url', ''),
            info.get('uploader', ''),
            info.get('uploader_id', ''),
            info.get('uploader_url', '')
        )
        cursor.execute(channel_sql, channel_values)

        # 插入视频数据
        video_sql = """
        INSERT INTO videos (
            video_id, channel_id, title, fulltitle, description,
            webpage_url, thumbnail_url, upload_date, release_date, language
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description)
        """
        video_values = (
            info['id'],
            info['channel_id'],
            info.get('fulltitle', ''),
            info.get('fulltitle', ''),
            info.get('description', ''),
            info.get('webpage_url', ''),
            info.get('thumbnail', ''),
            format_date(info['upload_date']),
            format_date(info['release_date']),
            info.get('language', 'en')
        )
        cursor.execute(video_sql, video_values)

        # 处理标签数据
        if 'tags' in info:
            tag_insert_sql = "INSERT IGNORE INTO tags (tag_name) VALUES (%s)"
            for tag in info['tags']:
                cursor.execute(tag_insert_sql, (tag,))

            tag_select_sql = "SELECT tag_id FROM tags WHERE tag_name = %s"
            video_tag_sql = "INSERT IGNORE INTO video_tags (video_id, tag_id) VALUES (%s, %s)"
            for tag in info['tags']:
                cursor.execute(tag_select_sql, (tag,))
                if result := cursor.fetchone():
                    cursor.execute(video_tag_sql, (info['id'], result[0]))

        conn.commit()
        print("元数据已保存至数据库")

    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        conn.rollback()
    except Exception as e:
        print(f"保存数据失败: {str(e)}")
        conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# 在 download_video 函数中添加调用
def download_video(url: str, title: str):
    # 配置参数：下载并合并最佳音视频流
    ydl_opts = {
        'format': 'bestvideo+bestaudio',
        'merge_output_format': 'mp4',
        'outtmpl': f'cache/{title}.mp4',  # 修正变量名错误
        'quiet': False,
        'noprogress': False,
        'ignoreerrors': 'only_download',
        'embedthumbnail': True,          # 自动嵌入视频缩略图
        'verbose': True                 # 显示FFmpeg合并过程
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return f'{title}.mp4'
    except yt_dlp.utils.DownloadError as e:
        if "ffmpeg" in str(e).lower():
            print("错误：未检测到 FFmpeg，请通过 brew install ffmpeg 安装")
        else:
            raise e
        return None

def download_subtitle(url: str, title: str):
    """智能字幕下载"""
    try:
        # 获取字幕信息
        cmd = [
            'yt-dlp',
            '--skip-download',
            '--dump-single-json',
            url
        ]

        # 打印可直接执行的命令字符串，以便在终端中调试
        quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
        print(f"执行命令：{quoted_cmd}")

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # 将输出结果保存到 cache
        with open(f"cache/{title}_orig.json", 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        info = json.loads(result.stdout)
        with open(f"cache/{title}_formatted.json", 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=4, ensure_ascii=False)  # 写入格式化后的 JSON 数据
        
        # 选择最佳字幕
        subs = info.get('subtitles') or {}
        auto_subs = info.get('automatic_captions') or {}
        selected = None
        
        # 优先级选择逻辑
        for lang in ['zh', 'en']:
            if lang in subs:
                selected = {'lang': lang, 'is_auto': False}
                break
        if not selected and 'en' in auto_subs:
            selected = {'lang': 'en', 'is_auto': True}
        
        # 下载字幕
        if selected:
            
            print(f"选择的字幕：{selected}")

            # 如果是人工字幕
            # yt-dlp --write-subs --sub-langs "en" --skip-download --convert-subs srt -o subtitles/output.srt "https://www.youtube.com/watch?v=jJ48Z6cQHBM"

            # 如果是自动字幕
            # yt-dlp --write-auto-subs --sub-langs "en" --skip-download --convert-subs srt -o subtitles/output.srt "https://www.youtube.com/watch?v=jJ48Z6cQHBM"

            # 根据字幕类型选择参数
            if selected['is_auto']:
                sub_cmd = '--write-auto-subs'
            else:
                sub_cmd = '--write-subs'

            cmd = [
                'yt-dlp',
                sub_cmd,
                '--sub-langs', selected['lang'],
                '--skip-download',
                '--convert-subs', 'srt',
                '-o', f"cache/{title}.%(ext)s",
                url
            ]

            # 打印可直接执行的命令字符串，以便在终端中调试
            quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
            print(f"执行命令：{quoted_cmd}")

            subprocess.run(cmd, check=True)
            print(f"字幕下载完成：{selected['lang']}")

            return f"{title}.{selected['lang']}.srt"
        else:
            print("没有找到可用的字幕")
            return None
    except Exception as e:
        print(f"字幕下载失败: {str(e)}")

# 定义 optimize_subtitle 函数
def dedupe_subtitle(subtitle_file: str, title: str):
    if subtitle_file:
        try:
            # 新原始文件路径（添加 _orig 后缀）
            orig_path = os.path.join('cache', f"{title}_orig.srt")
            # 去重后文件路径
            dedupe_path = os.path.join('cache', f"{title}_dedupe.srt")
            
            # 先重命名原始文件
            shutil.move(os.path.join('cache', subtitle_file), orig_path)
            
            # 处理重命名后的文件
            subs = pysrt.open(orig_path)
            optimized_subs = []
            prev_sub = None
            
            # 处理每个字幕块
            for sub in subs:
                # 分割字幕行
                lines = sub.text.split('\n')
                
                # 保留最后有效行（示例中的第四行）
                valid_line = lines[-1].strip() if len(lines) >= 2 else sub.text.strip()
                
                # 跳过空行
                if not valid_line:
                    continue
                
                # 合并相同字幕（新增逻辑）
                if prev_sub and valid_line == prev_sub.text:
                    # 合并时间范围：更新前一个条目的结束时间
                    prev_sub.end = sub.end
                else:
                    # 创建新字幕条目
                    new_sub = pysrt.SubRipItem(
                        index=len(optimized_subs)+1,
                        start=sub.start,
                        end=sub.end,
                        text=valid_line
                    )
                    optimized_subs.append(new_sub)
                    prev_sub = new_sub  # 更新前一个条目引用
            
            pysrt.SubRipFile(optimized_subs).save(dedupe_path, encoding='utf-8')
            print(f"字幕优化完成: {dedupe_path}")
            return f"{title}_dedupe.srt"
        except Exception as e:
            print(f"字幕优化失败: {str(e)}")
    else:
        print("没有可用的字幕文件进行优化")

def translate_subtitle(input_srt: str, title: str):
    """生成中英双语及纯中文字幕"""
    subs = pysrt.open(os.path.join('cache', input_srt))
    
    # 生成三个版本的文件名
    cn_srt = f"{title}.cn.srt"
    en_srt = f"{title}.en.srt"
    bilingual_srt = f"{title}.en+cn.srt"
    
    # 创建三个字幕对象
    cn_subs = pysrt.SubRipFile()
    en_subs = pysrt.SubRipFile()
    bilingual_subs = pysrt.SubRipFile()

    total_lines = len(subs)  # 获取总行数用于进度显示

    for idx, sub in enumerate(subs, 1):
        if 0 < Config.max_lines < idx:  # 新增行数检查
            print(f"\n调试模式：已截断前{Config.max_lines}行")
            break

        original_text = sub.text
        translated_text = ""

        try:
            # === 新增翻译核心逻辑 ===
            prompt = f"将以下英文翻译为中文，保持原格式:\n{sub.text}"
            response = ollama.generate(
                model='qwen2.5:7b-instruct',
                prompt=prompt,
                options={'temperature': 0.2}
            )
            translated_text = response['response'].strip()

            # 打印翻译进度
            print(f"[{sub.index}/{total_lines}] {original_text}")
            print(f"[{sub.index}/{total_lines}] {translated_text}\n")

            # 构建三种字幕内容
            bilingual_subs.append(pysrt.SubRipItem(
                index=idx,
                start=sub.start,
                end=sub.end,
                text=f"{original_text}\n{translated_text}"
            ))

            cn_subs.append(pysrt.SubRipItem(
                index=idx,
                start=sub.start,
                end=sub.end,
                text=translated_text
            ))

            en_subs.append(pysrt.SubRipItem(
                index=idx,
                start=sub.start,
                end=sub.end,
                text=original_text
            ))

        except Exception as e:
            print(f"翻译失败 [{sub.index}]: {str(e)}")
            # 错误时保留原文本
            bilingual_subs.append(pysrt.SubRipItem(
                index=idx,
                start=sub.start,
                end=sub.end,
                text=f"{original_text}\n[翻译失败]"
            ))

    # 保存三个版本
    cn_subs.save(os.path.join('cache', cn_srt), encoding='utf-8')
    en_subs.save(os.path.join('cache', en_srt), encoding='utf-8')
    bilingual_subs.save(os.path.join('cache', bilingual_srt), encoding='utf-8')
    
    # 返回包含三个路径的字典
    return {
        'cn': os.path.join('cache', cn_srt),
        'en': os.path.join('cache', en_srt),
        'bilingual': os.path.join('cache', bilingual_srt)
    }


def merge_subtitle(video_file: str, all_subs: dict, output_file: str):
    """使用ffmpeg库合并多语言字幕到视频"""
    try:
        # 构建输入流
        input_video = ffmpeg.input(os.path.join('cache', video_file))
        input_cn = ffmpeg.input(all_subs['cn'])
        input_en = ffmpeg.input(all_subs['en'])
        input_bilingual = ffmpeg.input(all_subs['bilingual'])

        # 构建输出流
        output = ffmpeg.output(
            input_video['v'],  # 视频流
            input_video['a'],  # 音频流
            input_cn['s'],  # 中文字幕流
            input_en['s'],  # 英文字幕流
            input_bilingual['s'],  # 双语字幕流
            os.path.join('cache', output_file),
            vcodec='copy',  # 保持视频编码
            acodec='copy',  # 保持音频编码
            scodec='mov_text',  # 字幕编码格式
            **{
                'metadata:s:s:0': 'language=chi',
                'metadata:s:s:1': 'language=eng',
                'metadata:s:s:2': 'language=bilingual'
            }
        )

        # 执行合并
        output.run(overwrite_output=True)
        print(f"多语言字幕合并完成: {output_file}")
    except ffmpeg.Error as e:
        print(f"字幕合并失败: {e.stderr.decode('utf8')}")
        raise RuntimeError(e.stderr)

def main():
    print("开始执行")
    # 创建目录
    os.makedirs('cache', exist_ok=True)

    # 处理任务
    for url in load_tasks('tasks.txt'):
        try:
            # 获取预期下载的文件名
            if Config.debug_video_file:
                video_file = Config.debug_video_file
                info = None
                with open(Config.debug_json_file, 'r', encoding='utf-8') as file:
                    info = json.load(file)

            else:
                video_file, info = get_safe_filename(url)
            print(f"video_file: {video_file}")

            # 获取安全标题、视频扩展名
            title, video_ext = os.path.splitext(video_file)
            print(f"title: {title}")
            print(f"vide_ext: {video_ext}")

            # 字幕处理逻辑
            if Config.debug_subtitle_file:
                subtitle_file = Config.debug_subtitle_file
            else:
                subtitle_file = download_subtitle(url, title)
            print(f"subtitle_file: {subtitle_file}")

            # 清理多行字幕
            deduped_subtitle_file = dedupe_subtitle(subtitle_file, title)
            print(f"已清理多行字幕 {deduped_subtitle_file}")

            # 翻译字幕
            all_subs = translate_subtitle(deduped_subtitle_file, title)
            print(f"已翻译字幕 {all_subs
            }")

            # 下载视频
            download_video_file = download_video(url, title)
            print(f"已下载视频 {download_video_file}")

            # 合并字幕
            merged_output = f"{title}_with_subs.mp4"
            merge_subtitle(download_video_file, all_subs, merged_output)
            print(f"最终视频已生成: {merged_output}")

            save_to_database(info)
        except Exception as e:
            print(f"处理失败：{e}")

if __name__ == '__main__':
    main()