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
    proxy_enabled = False
    proxy_address = "127.0.0.1:7897"
    max_lines = 0  # 新增调试行数限制 (0=全部翻译)

    debug_use_mock_json = False
    debug_use_mock_subtitle = False
    debug_use_mock_video = False

    debug_safe_title = '1000 Ideas In Your Pocket'
    debug_video_id = 'p3fkSGSSYVA'
    
    debug_video_file = 'example/1000 Ideas In Your Pocket.mp4'
    debug_subtitle_file = 'example/1000 Ideas In Your Pocket_orig.srt'
    debug_json_file = 'example/1000 Ideas In Your Pocket_formatted.json'

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
        return [line.strip() for line in f 
                if line.strip() and not line.startswith('* ')]  # 新增跳过逻辑

# 在 load_tasks 函数下方添加以下函数
def query_if_exists(url: str) -> bool:
    """检查 URL 是否已存在于数据库"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """SELECT COUNT(*) FROM videos 
                WHERE webpage_url = %s 
                AND download_time IS NOT NULL"""  # 新增非空条件
        cursor.execute(query, (url,))
        
        # 获取查询结果
        count = cursor.fetchone()[0]
        return count > 0
        
    except mysql.connector.Error as err:
        print(f"数据库查询错误: {err}")
        return False  # 出错时默认继续处理
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def get_safe_filename(url, template='%(title)s.%(ext)s'):
    ydl_opts = {
        'outtmpl': template,  # 文件名模板
        'simulate': True,  # 模拟模式（不下载）
        'quiet': True,  # 禁用日志输出
        'restrictfilenames': False,  # 关键参数
        'windowsfilenames': True  # 保持默认值（True）
    }
    # 新增代理配置
    if Config.proxy_enabled:
        ydl_opts['proxy'] = Config.proxy_address

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

        # 新视频数据插入
        video_sql = """
        INSERT INTO videos (
            id, description, tags, channel_id, channel_url,
            webpage_url, channel, uploader, uploader_id,
            uploader_url, upload_date, fulltitle, 
            release_date, language, thumbnail, download_time
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            description = VALUES(description),
            tags = VALUES(tags),
            channel = VALUES(channel),
            download_time = VALUES(download_time)
        """
        video_values = (
            info['id'],
            info.get('description', ''),
            json.dumps(info.get('tags', [])),  # 转换列表为JSON字符串
            info['channel_id'],
            info.get('channel_url', ''),
            info.get('webpage_url', ''),
            info.get('channel', ''),
            info.get('uploader', ''),
            info.get('uploader_id', ''),
            info.get('uploader_url', ''),
            format_date(info['upload_date']),
            info.get('fulltitle', ''),
            # format_date(info['release_date']),
            format_date(info['release_date']) if 'release_date' in info else None,
            info.get('language', 'en'),
            info.get('thumbnail', ''),
            datetime.now()
        )
        cursor.execute(video_sql, video_values)
        conn.commit()
        print("元数据已保存至数据库")
        return True
    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"保存数据失败: {str(e)}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# 在 download_video 函数中添加调用
def download_video(url: str, safe_title: str, data_dir: str):
    output_path = os.path.join(data_dir, f'{safe_title}_orig.mp4')
    # 配置参数：下载并合并最佳音视频流
    ydl_opts = {
        'format': 'bestvideo+bestaudio',
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'quiet': False,
        'noprogress': False,
        'ignoreerrors': 'only_download',
        'embedthumbnail': True,          # 自动嵌入视频缩略图
        'verbose': True                 # 显示FFmpeg合并过程
    }
    # 新增代理配置
    if Config.proxy_enabled:
        ydl_opts['proxy'] = Config.proxy_address

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return output_path
    except yt_dlp.utils.DownloadError as e:
        if "ffmpeg" in str(e).lower():
            print("错误：未检测到 FFmpeg，请通过 brew install ffmpeg 安装")
        else:
            raise e
        return None

def download_subtitle(url: str, video_info: dict, safe_title: str, data_dir: str):
    """智能字幕下载"""
    try:
        # 选择最佳字幕
        subs = video_info.get('subtitles') or {}
        auto_subs = video_info.get('automatic_captions') or {}
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
                '-o', f"{data_dir}/{safe_title}.%(ext)s",
                url
            ]

            # 打印可直接执行的命令字符串，以便在终端中调试
            quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
            print(f"执行命令：{quoted_cmd}")

            subprocess.run(cmd, check=True)
            print(f"字幕下载完成：{selected['lang']}")

            source_file_name = f'{safe_title}.en.srt'
            target_file_name =f'{safe_title}.en_origin.srt'
            shutil.move(
                os.path.join(data_dir, source_file_name),
                os.path.join(data_dir, target_file_name))

            return target_file_name
        else:
            print("没有找到可用的字幕")
            return None
    except Exception as e:
        print(f"字幕下载失败: {str(e)}")

# 定义 optimize_subtitle 函数
def dedupe_subtitle(subtitle_file: str, safe_title: str, data_dir: str):
    if subtitle_file:
        try:
            # 新原始文件路径（添加 _orig 后缀）
            orig_path = os.path.join(data_dir, f"{safe_title}_orig.srt")
            # 去重后文件路径
            dedupe_path = os.path.join(data_dir, f"{safe_title}_dedupe.srt")
            
            # 先重命名原始文件
            shutil.move(os.path.join(data_dir, subtitle_file), orig_path)
            
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
            return f"{safe_title}_dedupe.srt"
        except Exception as e:
            print(f"字幕优化失败: {str(e)}")
    else:
        print("没有可用的字幕文件进行优化")

def translate_subtitle(input_srt: str, safe_title: str, data_dir: str):
    """生成中英双语及纯中文字幕"""
    subs = pysrt.open(os.path.join(data_dir, input_srt))
    
    # 生成三个版本的文件名
    cn_srt = f"{safe_title}.cn.srt"
    en_srt = f"{safe_title}.en.srt"
    bilingual_srt = f"{safe_title}.en+cn.srt"
    
    # 创建三个字幕对象
    cn_sub = pysrt.SubRipFile()
    en_sub = pysrt.SubRipFile()
    bilingual_sub = pysrt.SubRipFile()

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
            bilingual_sub.append(pysrt.SubRipItem(
                index=idx,
                start=sub.start,
                end=sub.end,
                text=f"{original_text}\n{translated_text}"
            ))

            cn_sub.append(pysrt.SubRipItem(
                index=idx,
                start=sub.start,
                end=sub.end,
                text=translated_text
            ))

            en_sub.append(pysrt.SubRipItem(
                index=idx,
                start=sub.start,
                end=sub.end,
                text=original_text
            ))

        except Exception as e:
            print(f"翻译失败 [{sub.index}]: {str(e)}")
            # 错误时保留原文本
            bilingual_sub.append(pysrt.SubRipItem(
                index=idx,
                start=sub.start,
                end=sub.end,
                text=f"{original_text}\n[翻译失败]"
            ))

    # 保存三个版本
    cn_sub_path = os.path.join(data_dir, cn_srt)
    en_sub_path = os.path.join(data_dir, en_srt)
    bilingual_sub_path = os.path.join(data_dir, bilingual_srt)

    cn_sub.save(cn_sub_path, encoding='utf-8')
    en_sub.save(en_sub_path, encoding='utf-8')
    bilingual_sub.save(bilingual_sub_path, encoding='utf-8')
    
    # 返回包含三个路径的字典
    return {
        'cn': cn_sub_path,
        'en': en_sub_path,
        'bilingual': bilingual_sub_path
    }

def merge_subtitle(input_video_file_path: str,
                   output_video_file_name: str,
                   all_subs: dict,
                   input_video_dir: str,
                   output_video_dir: str):
    """使用ffmpeg库合并多语言字幕到视频"""
    try:
        # 构建输入流
        input_video = ffmpeg.input(input_video_file_path)
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
            os.path.join(output_video_dir, output_video_file_name),
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
        print(f"多语言字幕合并完成: {output_video_file_name}")
    except ffmpeg.Error as e:
        print(f"字幕合并失败: {e.stderr.decode('utf8')}")
        raise RuntimeError(e.stderr)

def update_task_file(url: str):
    """在任务文件中的URL前添加星号标记"""
    task_file = 'tasks.txt'
    try:
        with open(task_file, 'r+', encoding='utf-8') as f:
            lines = [f'* {line}' if line.strip() == url else line 
                    for line in f.readlines()]
            f.seek(0)
            f.writelines(lines)
            f.truncate()
    except Exception as e:
        print(f"更新任务文件失败: {str(e)}")

def main():
    print("开始执行")
    # 创建目录
    video_dir = 'videos'
    os.makedirs('videos', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    # 处理任务
    for url in load_tasks('tasks.txt'):
        try:
            print(f'--- 开始处理 {url} ---')

            # 查询数据库中是否已有这条记录
            if query_if_exists(url):
                print(f"跳过已存在的任务：{url}")
                update_task_file(url)
                continue

            # 获取预期下载的文件名
            if Config.debug_use_mock_json:
                safe_title = Config.debug_safe_title
                video_ext = '.mp4'
                safe_file_name = safe_title + video_ext
                with open(Config.debug_json_file, 'r', encoding='utf-8') as file:
                    video_info = json.load(file)
            else:
                safe_file_name, video_info = get_safe_filename(url)
                safe_title, video_ext = os.path.splitext(safe_file_name)

            # 获取安全标题、视频扩展名
            print(f"safe_title: {safe_title}")
            print(f"vide_ext: {video_ext}")

            # 生成项目名，并创建数据目录
            item_name = f"{safe_title} [{video_info['id']}]"
            data_dir = os.path.join('data', item_name)
            os.makedirs(data_dir, exist_ok=True)

            # 将 JSON 文件写入到数据目录下
            test_path = os.path.join(data_dir, f'{safe_title}.srt')
            if not os.path.exists(test_path):
                target_json_path = os.path.join(data_dir, f'{safe_title}.json')
                if Config.debug_use_mock_json:
                    shutil.copy(Config.debug_json_file, target_json_path)
                else:
                    with open(target_json_path, 'w', encoding='utf-8') as file:
                        json.dump(video_info, file, ensure_ascii=False, indent=4)

            # 字幕处理逻辑
            test_path = os.path.join(data_dir, f'{safe_title}_orig.srt')
            if os.path.exists(test_path):
                orig_subtitle_file =f'{safe_title}_orig.srt'
            else:
                if Config.debug_use_mock_subtitle:
                    target_subtitle_file = f'{safe_title}_orig.srt'
                    orig_subtitle_file = target_subtitle_file
                    target_subtitle_path = os.path.join(data_dir, target_subtitle_file)
                    shutil.copy(Config.debug_subtitle_file, target_subtitle_path)
                else:
                    orig_subtitle_file = download_subtitle(url, video_info, safe_title, data_dir)
                print(f'orig_subtitle_file: {orig_subtitle_file}')

            # 清理多行字幕
            deduped_subtitle_file = dedupe_subtitle(orig_subtitle_file, safe_title, data_dir)
            print(f"已清理多行字幕 {deduped_subtitle_file}")

            test_path = os.path.join(data_dir, f'{safe_title}.en+cn.srt')
            if os.path.exists(test_path):
                all_subs = {
                    'cn': os.path.join(data_dir, f'{safe_title}.cn.srt'),
                    'en': os.path.join(data_dir, f'{safe_title}.en.srt'),
                    'bilingual': os.path.join(data_dir, f'{safe_title}.en+cn.srt')
                }
            else:
                # 翻译字幕
                all_subs = translate_subtitle(deduped_subtitle_file, safe_title, data_dir)
                print(f"已翻译字幕 {all_subs}")

            # 下载视频
            if Config.debug_use_mock_video:
                downloaded_video_path = os.path.join(data_dir, f'{safe_title}_orig.mp4')
                shutil.copy(Config.debug_video_file, downloaded_video_path)
            else:
                downloaded_video_path = download_video(url, safe_title, data_dir)
            print(f"已下载视频 {downloaded_video_path}")

            # 合并字幕
            merged_video = f"{item_name}.mp4"
            merge_subtitle(downloaded_video_path,
                           merged_video,
                           all_subs,
                           data_dir,
                           video_dir)
            print(f"最终视频已生成: {merged_video}")
            
            # 删除 downloaded_video_path
            os.remove(downloaded_video_path)

            # 保存元数据到数据库
            save_to_database(video_info)

            # 新增标记已完成的URL
            update_task_file(url)
        except Exception as e:
            print(f"处理失败：{e}")

if __name__ == '__main__':
    main()
