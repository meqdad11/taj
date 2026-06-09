import aiohttp
import re
import yt_dlp
import os
import asyncio
from config import RAPIDAPI_KEY


async def search_youtube(query: str, max_results: int = 10):
    """البحث في يوتيوب"""
    try:
        # Using YouTube Data API v3 via RapidAPI
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "youtube-search-results.p.rapidapi.com"
        }
        
        async with aiohttp.ClientSession() as session:
            api_url = "https://youtube-search-results.p.rapidapi.com/youtube-search"
            params = {"q": query}
            
            async with session.get(api_url, headers=headers, params=params, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("items", [])
                    results = []
                    for item in items[:max_results]:
                        if item.get("type") == "video":
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "thumbnail": item.get("bestThumbnail", {}).get("url", ""),
                                "duration": item.get("duration", ""),
                                "views": item.get("views", ""),
                                "author": item.get("author", {}).get("name", "")
                            })
                    return results
        
        # Fallback: using yt-dlp search
        return await search_with_ytdlp(query, max_results)
    
    except Exception as e:
        return await search_with_ytdlp(query, max_results)


async def search_with_ytdlp(query: str, max_results: int = 10):
    """البحث باستخدام yt-dlp كبديل"""
    try:
        loop = asyncio.get_event_loop()
        
        def _search():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': 'ytsearch',
                'playlistend': max_results,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_query = f"ytsearch{max_results}:{query}"
                result = ydl.extract_info(search_query, download=False)
                
                entries = result.get('entries', [])
                results = []
                for entry in entries:
                    if entry:
                        results.append({
                            'title': entry.get('title', 'Unknown'),
                            'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                            'thumbnail': entry.get('thumbnail', ''),
                            'duration': entry.get('duration', 0),
                            'views': entry.get('view_count', 0),
                            'author': entry.get('uploader', '')
                        })
                return results
        
        return await loop.run_in_executor(None, _search)
    
    except Exception as e:
        return []


async def get_video_info(url: str):
    """الحصول على معلومات الفيديو"""
    try:
        loop = asyncio.get_event_loop()
        
        def _info():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'duration': info.get('duration', 0),
                    'views': info.get('view_count', 0),
                    'author': info.get('uploader', ''),
                    'formats': info.get('formats', [])
                }
        
        return await loop.run_in_executor(None, _info)
    
    except Exception as e:
        return None


async def download_youtube_video(url: str, quality: str = "720", output_path: str = "downloads"):
    """تحميل فيديو يوتيوب بجودة محددة"""
    try:
        os.makedirs(output_path, exist_ok=True)
        loop = asyncio.get_event_loop()
        
        def _download():
            quality_map = {
                "360": "18",
                "720": "22",
                "1080": "137+140"
            }
            format_spec = quality_map.get(quality, "22")
            
            ydl_opts = {
                'format': f'best[height<={quality}]',
                'outtmpl': f'{output_path}/%(title)s_%(height)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Find actual downloaded file
                base = filename.rsplit('.', 1)[0]
                for ext in ['.mp4', '.webm', '.mkv']:
                    if os.path.exists(base + ext):
                        return base + ext
                return filename if os.path.exists(filename) else None
        
        file_path = await loop.run_in_executor(None, _download)
        
        if file_path and os.path.exists(file_path):
            return {"success": True, "file_path": file_path}
        return {"success": False, "error": "فشل في تحميل الفيديو"}
    
    except Exception as e:
        return {"success": False, "error": f"حدث خطأ: {str(e)}"}


async def download_youtube_audio(url: str, bitrate: str = "128", output_path: str = "downloads"):
    """تحميل صوت يوتيوب"""
    try:
        os.makedirs(output_path, exist_ok=True)
        loop = asyncio.get_event_loop()
        
        def _download():
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{output_path}/%(title)s_audio.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # Change extension to mp3
                mp3_file = filename.rsplit('.', 1)[0] + '.mp3'
                return mp3_file if os.path.exists(mp3_file) else filename
        
        file_path = await loop.run_in_executor(None, _download)
        
        if file_path and os.path.exists(file_path):
            return {"success": True, "file_path": file_path}
        return {"success": False, "error": "فشل في تحميل الصوت"}
    
    except Exception as e:
        return {"success": False, "error": f"حدث خطأ: {str(e)}"}


def is_youtube_url(url: str) -> bool:
    """التحقق مما إذا كان الرابط خاصاً باليوتيوب"""
    youtube_regex = r"(youtube\.com|youtu\.be|youtube-nocookie\.com)"
    return bool(re.search(youtube_regex, url))


def extract_video_id(url: str) -> str:
    """استخراج معرف الفيديو"""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
