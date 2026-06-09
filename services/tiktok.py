import aiohttp
import re
from config import RAPIDAPI_KEY


async def download_tiktok(url: str, audio_only: bool = False):
    """تحميل فيديو أو صوت تيك توك بدون علامة مائية"""
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "tiktok-video-no-watermark2.p.rapidapi.com"
    }
    
    try:
        # Clean URL
        url = url.split("?")[0]
        
        async with aiohttp.ClientSession() as session:
            api_url = "https://tiktok-video-no-watermark2.p.rapidapi.com/"
            params = {"url": url, "hd": "1"}
            
            async with session.get(api_url, headers=headers, params=params, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and data.get("code") == 0:
                        result = data.get("data", {})
                        
                        if audio_only:
                            return {
                                "success": True,
                                "title": result.get("title", "TikTok Audio"),
                                "url": result.get("music", ""),
                                "thumbnail": result.get("cover", ""),
                                "type": "audio",
                                "author": result.get("author", {}).get("nickname", "")
                            }
                        else:
                            return {
                                "success": True,
                                "title": result.get("title", "TikTok Video"),
                                "url": result.get("play", ""),
                                "hd_url": result.get("hdplay", result.get("play", "")),
                                "thumbnail": result.get("cover", ""),
                                "type": "video",
                                "author": result.get("author", {}).get("nickname", ""),
                                "duration": result.get("duration", 0),
                                "views": result.get("play_count", 0)
                            }
                
                # Fallback API
                alt_headers = {
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": "tiktok-download-video-no-watermark.p.rapidapi.com"
                }
                alt_api = "https://tiktok-download-video-no-watermark.p.rapidapi.com/vid/index"
                alt_params = {"url": url}
                
                async with session.get(alt_api, headers=alt_headers, params=alt_params, timeout=30) as resp2:
                    if resp2.status == 200:
                        data2 = await resp2.json()
                        if data2 and "video" in data2:
                            return {
                                "success": True,
                                "title": data2.get("description", "TikTok Video"),
                                "url": data2["video"][0] if isinstance(data2["video"], list) else data2["video"],
                                "thumbnail": data2.get("cover", [""])[0] if isinstance(data2.get("cover"), list) else data2.get("cover", ""),
                                "type": "video",
                                "author": data2.get("author", "")
                            }
        
        return {"success": False, "error": "تعذر تحميل الفيديو. تأكد من صحة الرابط."}
    
    except Exception as e:
        return {"success": False, "error": f"حدث خطأ: {str(e)}"}


def is_tiktok_url(url: str) -> bool:
    """التحقق مما إذا كان الرابط خاصاً بتيك توك"""
    return bool(re.search(r"(tiktok\.com|vm\.tiktok\.com)", url))
