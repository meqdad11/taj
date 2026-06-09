import yt_dlp
import os
import asyncio


async def download_generic(url: str, audio_only: bool = False, output_path: str = "downloads"):
    """تحميل من أي رابط مدعوم"""
    try:
        os.makedirs(output_path, exist_ok=True)
        loop = asyncio.get_event_loop()
        
        def _download():
            ydl_opts = {
                'outtmpl': f'{output_path}/%(title)s_%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
            }
            
            if audio_only:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                ydl_opts['format'] = 'best[filesize<50M]'
                ydl_opts['merge_output_format'] = 'mp4'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Check for actual file
                if audio_only:
                    mp3_file = filename.rsplit('.', 1)[0] + '.mp3'
                    if os.path.exists(mp3_file):
                        return mp3_file
                
                if os.path.exists(filename):
                    return filename
                    
                # Try alternative extensions
                base = filename.rsplit('.', 1)[0]
                for ext in ['.mp4', '.webm', '.mkv', '.mp3', '.m4a']:
                    alt = base + ext
                    if os.path.exists(alt):
                        return alt
                
                return filename
        
        file_path = await loop.run_in_executor(None, _download)
        
        if file_path and os.path.exists(file_path):
            # Get file size
            file_size = os.path.getsize(file_path)
            if file_size > 2 * 1024 * 1024 * 1024:  # 2GB limit
                os.remove(file_path)
                return {"success": False, "error": "حجم الملف كبير جداً (أكبر من 2GB). حاول فيديو أقصر."}
            
            return {"success": True, "file_path": file_path, "size": file_size}
        
        return {"success": False, "error": "فشل في تحميل الملف"}
    
    except Exception as e:
        error_msg = str(e)
        if "Unsupported URL" in error_msg:
            return {"success": False, "error": "عذراً، هذا الموقع غير مدعوم حالياً.\nالمواقع المدعومة: يوتيوب، إنستغرام، تيك توك، فيسبوك، تويتر، ريديت، بينتريست، وأكثر من 1000 موقع آخر."}
        elif "Private video" in error_msg or "private" in error_msg.lower():
            return {"success": False, "error": "هذا الفيديو خاص. تأكد من أنه عام (Public)."}
        elif "geo-bypass" in error_msg.lower() or "unavailable" in error_msg.lower():
            return {"success": False, "error": "هذا الفيديو غير متاح في منطقتك."}
        return {"success": False, "error": f"حدث خطأ أثناء التحميل: {error_msg[:200]}"}
