import aiohttp
import re
import os
from config import RAPIDAPI_KEY


async def extract_instagram_info(url: str):
    """استخراج معلومات الفيديو من إنستغرام"""
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com"
    }
    
    try:
        # Clean URL
        url = url.split("?")[0]
        
        async with aiohttp.ClientSession() as session:
            api_url = "https://instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com/get-info-rapidapi"
            params = {"url": url}
            
            async with session.get(api_url, headers=headers, params=params, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and "download_url" in data:
                        return {
                            "success": True,
                            "title": data.get("caption", ""),
                            "url": data["download_url"],
                            "thumbnail": data.get("cover", ""),
                            "type": "video" if data.get("type") == "video" else "image"
                        }
                
                # Fallback: try alternative API
                alt_api = "https://instagram-scraper-2022.p.rapidapi.com/ig/post_info_v2"
                shortcode = extract_shortcode(url)
                if shortcode:
                    alt_params = {"shortcode": shortcode}
                    async with session.get(alt_api, headers={
                        "X-RapidAPI-Key": RAPIDAPI_KEY,
                        "X-RapidAPI-Host": "instagram-scraper-2022.p.rapidapi.com"
                    }, params=alt_params, timeout=30) as resp2:
                        if resp2.status == 200:
                            data2 = await resp2.json()
                            if data2 and "items" in data2:
                                item = data2["items"][0]
                                video_url = item.get("video_url", "")
                                if video_url:
                                    return {
                                        "success": True,
                                        "title": item.get("caption", {}).get("text", "")[:100],
                                        "url": video_url,
                                        "thumbnail": item.get("image_versions2", {}).get("candidates", [{}])[0].get("url", ""),
                                        "type": "video"
                                    }
        
        return {"success": False, "error": "تعذر تحميل الفيديو. تأكد من أن الرابط عام (Public)."}
    
    except Exception as e:
        return {"success": False, "error": f"حدث خطأ: {str(e)}"}


def extract_shortcode(url: str) -> str:
    """استخراج shortcode من رابط إنستغرام"""
    patterns = [
        r"instagram\.com/(?:p|reel|reels)/([A-Za-z0-9_-]+)",
        r"instagram\.com/tv/([A-Za-z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def is_instagram_url(url: str) -> bool:
    """التحقق مما إذا كان الرابط خاصاً بإنستغرام"""
    return bool(re.search(r"instagram\.com/(p|reel|reels|tv)/", url))
