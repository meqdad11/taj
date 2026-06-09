from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu() -> InlineKeyboardMarkup:
    """القائمة الرئيسية"""
    buttons = [
        [
            InlineKeyboardButton(text="📸 إنستغرام", callback_data="menu_instagram"),
            InlineKeyboardButton(text="🎵 تيك توك", callback_data="menu_tiktok"),
        ],
        [
            InlineKeyboardButton(text="📺 يوتيوب", callback_data="menu_youtube"),
            InlineKeyboardButton(text="🔗 أي رابط", callback_data="menu_anylink"),
        ],
        [
            InlineKeyboardButton(text="🔍 بحث يوتيوب", callback_data="search_youtube"),
        ],
        [
            InlineKeyboardButton(text="❓ المساعدة", callback_data="help"),
            InlineKeyboardButton(text="📊 الإحصائيات", callback_data="stats"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def instagram_menu() -> InlineKeyboardMarkup:
    """قائمة إنستغرام"""
    buttons = [
        [
            InlineKeyboardButton(text="🎬 تنزيل Reel", callback_data="ig_reel"),
        ],
        [
            InlineKeyboardButton(text="📷 تنزيل Post", callback_data="ig_post"),
        ],
        [
            InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def tiktok_menu() -> InlineKeyboardMarkup:
    """قائمة تيك توك"""
    buttons = [
        [
            InlineKeyboardButton(text="🎬 تنزيل فيديو", callback_data="tt_video"),
        ],
        [
            InlineKeyboardButton(text="🎵 تنزيل صوت فقط", callback_data="tt_audio"),
        ],
        [
            InlineKeyboardButton(text="🔗 إرسال رابط", callback_data="tt_link"),
        ],
        [
            InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def youtube_menu() -> InlineKeyboardMarkup:
    """قائمة يوتيوب"""
    buttons = [
        [
            InlineKeyboardButton(text="📹 فيديو", callback_data="yt_video"),
            InlineKeyboardButton(text="🎵 صوت فقط", callback_data="yt_audio"),
        ],
        [
            InlineKeyboardButton(text="🔍 بحث في يوتيوب", callback_data="search_youtube"),
        ],
        [
            InlineKeyboardButton(text="🔗 إرسال رابط", callback_data="yt_link"),
        ],
        [
            InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quality_menu(video_url: str, is_audio: bool = False) -> InlineKeyboardMarkup:
    """قائمة جودة يوتيوب"""
    if is_audio:
        buttons = [
            [
                InlineKeyboardButton(text="🎵 MP3 128kbps", callback_data=f"ytaudio|{video_url}|128"),
                InlineKeyboardButton(text="🎵 MP3 320kbps", callback_data=f"ytaudio|{video_url}|320"),
            ],
            [
                InlineKeyboardButton(text="🔙 رجوع", callback_data="back_youtube"),
            ],
        ]
    else:
        buttons = [
            [
                InlineKeyboardButton(text="📱 جودة منخفضة 360p", callback_data=f"ytvid|{video_url}|360"),
            ],
            [
                InlineKeyboardButton(text="📺 جودة متوسطة 720p", callback_data=f"ytvid|{video_url}|720"),
            ],
            [
                InlineKeyboardButton(text="🖥️ جودة عالية 1080p", callback_data=f"ytvid|{video_url}|1080"),
            ],
            [
                InlineKeyboardButton(text="🔙 رجوع", callback_data="back_youtube"),
            ],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_results_keyboard(results: list, query: str) -> InlineKeyboardMarkup:
    """أزرار نتائج البحث"""
    buttons = []
    for i, result in enumerate(results[:10]):
        buttons.append([
            InlineKeyboardButton(
                text=f"{i+1}. {result['title'][:30]}...",
                callback_data=f"ytdl|{result['url']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="🔍 بحث جديد", callback_data="search_youtube"),
        InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def download_options_keyboard(url: str) -> InlineKeyboardMarkup:
    """خيارات التحميل بعد البحث"""
    buttons = [
        [
            InlineKeyboardButton(text="📹 فيديو", callback_data=f"ytdl_video|{url}"),
            InlineKeyboardButton(text="🎵 صوت", callback_data=f"ytdl_audio|{url}"),
        ],
        [
            InlineKeyboardButton(text="🔙 رجوع للبحث", callback_data="search_youtube"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_button(callback_data: str = "back_main") -> InlineKeyboardMarkup:
    """زر رجوع"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 رجوع", callback_data=callback_data)]
    ])


def cancel_button() -> InlineKeyboardMarkup:
    """زر إلغاء"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel")]
    ])
