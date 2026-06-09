import os
import asyncio
import tempfile
import aiohttp
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import WELCOME_MESSAGE, HELP_MESSAGE, ABOUT_MESSAGE
from utils.keyboards import (
    main_menu, instagram_menu, tiktok_menu, youtube_menu,
    quality_menu, search_results_keyboard, download_options_keyboard,
    back_button, cancel_button
)
from services.instagram import extract_instagram_info, is_instagram_url
from services.tiktok import download_tiktok, is_tiktok_url
from services.youtube import (
    search_youtube, download_youtube_video, download_youtube_audio,
    get_video_info, is_youtube_url
)
from services.generic import download_generic

router = Router()

# Stats tracking
user_stats = {"users": set(), "downloads": 0}


class BotStates(StatesGroup):
    waiting_for_instagram_url = State()
    waiting_for_tiktok_url = State()
    waiting_for_youtube_url = State()
    waiting_for_search_query = State()
    waiting_for_generic_url = State()
    waiting_for_youtube_quality = State()


# ═══════════════════════════════════════════════════════════
# الأوامر الأساسية
# ═══════════════════════════════════════════════════════════

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """أمر البداية"""
    user_stats["users"].add(message.from_user.id)
    await state.clear()
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    """أمر المساعدة"""
    await state.clear()
    await message.answer(
        HELP_MESSAGE,
        reply_markup=back_button("back_main"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery, state: FSMContext):
    """زر المساعدة"""
    await state.clear()
    await callback.message.edit_text(
        HELP_MESSAGE,
        reply_markup=back_button("back_main"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "stats")
async def callback_stats(callback: CallbackQuery, state: FSMContext):
    """الإحصائيات"""
    users_count = len(user_stats["users"])
    downloads_count = user_stats["downloads"]
    
    stats_msg = f"""
📊 <b>إحصائيات البوت</b>

┌────────────────────────
│ 👥 عدد المستخدمين: {users_count}
│ 📥 إجمالي التحميلات: {downloads_count}
│ ⚡️ الحالة: يعمل بنجاح
└────────────────────────

💡 البوت يدعم تحميل من 1000+ موقع!
"""
    await callback.message.edit_text(
        stats_msg,
        reply_markup=back_button("back_main"),
        parse_mode="HTML"
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# القائمة الرئيسية والتنقل
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """العودة للقائمة الرئيسية"""
    await state.clear()
    await callback.message.edit_text(
        WELCOME_MESSAGE,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "menu_instagram")
async def menu_instagram(callback: CallbackQuery, state: FSMContext):
    """قائمة إنستغرام"""
    await state.clear()
    text = """
📸 <b>إنستغرام داونلودر</b>

┌────────────────────────
│ 🎬 تنزيل Reels
│ 📷 تنزيل Posts
│ ✅ جودة عالية
└────────────────────────

⚡️ <b>أرسل رابط الفيديو الآن:</b>

<code>https://instagram.com/reel/ABC123</code>
"""
    await callback.message.edit_text(text, reply_markup=instagram_menu(), parse_mode="HTML")
    await state.set_state(BotStates.waiting_for_instagram_url)
    await callback.answer()


@router.callback_query(F.data == "menu_tiktok")
async def menu_tiktok(callback: CallbackQuery, state: FSMContext):
    """قائمة تيك توك"""
    await state.clear()
    text = """
🎵 <b>تيك توك داونلودر</b>

┌────────────────────────
│ ✅ بدون علامة مائية
│ ✅ جودة HD
│ 🎵 استخراج الصوت
└────────────────────────

⚡️ <b>أرسل رابط التيك توك الآن:</b>

<code>https://tiktok.com/@user/video/123</code>
"""
    await callback.message.edit_text(text, reply_markup=tiktok_menu(), parse_mode="HTML")
    await state.set_state(BotStates.waiting_for_tiktok_url)
    await callback.answer()


@router.callback_query(F.data == "menu_youtube")
async def menu_youtube(callback: CallbackQuery, state: FSMContext):
    """قائمة يوتيوب"""
    await state.clear()
    text = """
📺 <b>يوتيوب داونلودر</b>

┌────────────────────────
│ 📹 فيديو بجودات متعددة
│ 🎵 صوت MP3 عالي الجودة
│ 🔍 بحث مباشر داخل البوت
└────────────────────────

⚡️ <b>اختر خياراً:</b>
"""
    await callback.message.edit_text(text, reply_markup=youtube_menu(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu_anylink")
async def menu_anylink(callback: CallbackQuery, state: FSMContext):
    """أي رابط"""
    await state.clear()
    text = """
🔗 <b>تحميل من أي رابط</b>

┌────────────────────────
│ 📺 يوتيوب
│ 📸 إنستغرام
│ 🎵 تيك توك
│ 👍 فيسبوك
│ 🐦 تويتر / X
│ 🔴 ريديت
│ 📌 بينتريست
│ 🌐 +1000 موقع آخر
└────────────────────────

⚡️ <b>أرسل الرابط الآن:</b>
"""
    await callback.message.edit_text(text, reply_markup=cancel_button(), parse_mode="HTML")
    await state.set_state(BotStates.waiting_for_generic_url)
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# إنستغرام
# ═══════════════════════════════════════════════════════════

@router.message(BotStates.waiting_for_instagram_url)
async def process_instagram_url(message: Message, state: FSMContext, bot: Bot):
    """معالجة رابط إنستغرام"""
    url = message.text.strip()
    
    if not is_instagram_url(url):
        await message.answer(
            "❌ <b>رابط إنستغرام غير صالح!</b>\n\n"
            "📌 <b>الروابط المدعومة:</b>\n"
            "• https://instagram.com/reel/ABC\n"
            "• https://instagram.com/p/ABC\n\n"
            "🔁 <b>أرسل رابطاً صحيحاً أو اضغط رجوع:</b>",
            reply_markup=instagram_menu(),
            parse_mode="HTML"
        )
        return
    
    processing_msg = await message.answer(
        "⏳ <b>جاري تحميل من إنستغرام...</b>\n"
        "<i>قد يستغرق بضع ثوانٍ</i>",
        parse_mode="HTML"
    )
    
    try:
        result = await extract_instagram_info(url)
        
        if result["success"]:
            user_stats["downloads"] += 1
            
            caption = f"""
📸 <b>تم التحميل من إنستغرام!</b>

{result['title'][:300] if result['title'] else '🎬 فيديو إنستغرام'}

⚡️ @DownloaderBot
"""
            await processing_msg.delete()
            
            if result["type"] == "image":
                await message.answer_photo(
                    photo=result["url"],
                    caption=caption,
                    reply_markup=instagram_menu(),
                    parse_mode="HTML"
                )
            else:
                try:
                    await message.answer_video(
                        video=result["url"],
                        caption=caption,
                        reply_markup=instagram_menu(),
                        parse_mode="HTML",
                        supports_streaming=True,
                        thumbnail=result.get("thumbnail")
                    )
                except Exception:
                    # If video sending fails, try as document
                    await message.answer_document(
                        document=result["url"],
                        caption=caption,
                        reply_markup=instagram_menu(),
                        parse_mode="HTML"
                    )
        else:
            await processing_msg.edit_text(
                f"❌ <b>خطأ:</b> {result['error']}\n\n"
                "🔁 <b>حاول مرة أخرى:</b>",
                reply_markup=instagram_menu(),
                parse_mode="HTML"
            )
    
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ <b>حدث خطأ:</b> {str(e)[:200]}\n\n"
            "🔁 <b>حاول مرة أخرى:</b>",
            reply_markup=instagram_menu(),
            parse_mode="HTML"
        )


# ═══════════════════════════════════════════════════════════
# تيك توك
# ═══════════════════════════════════════════════════════════

@router.message(BotStates.waiting_for_tiktok_url)
async def process_tiktok_url(message: Message, state: FSMContext, bot: Bot):
    """معالجة رابط تيك توك"""
    url = message.text.strip()
    data = await state.get_data()
    audio_only = data.get("audio_only", False)
    
    if not is_tiktok_url(url):
        await message.answer(
            "❌ <b>رابط تيك توك غير صالح!</b>\n\n"
            "📌 <b>أمثلة صحيحة:</b>\n"
            "• https://tiktok.com/@user/video/123\n"
            "• https://vm.tiktok.com/ABC123\n\n"
            "🔁 <b>أرسل رابطاً صحيحاً:</b>",
            reply_markup=tiktok_menu(),
            parse_mode="HTML"
        )
        return
    
    processing_msg = await message.answer(
        "⏳ <b>جاري التحميل من تيك توك...</b>\n"
        f"<i>{'استخراج الصوت...' if audio_only else 'بدون علامة مائية...'}</i>",
        parse_mode="HTML"
    )
    
    try:
        result = await download_tiktok(url, audio_only=audio_only)
        
        if result["success"]:
            user_stats["downloads"] += 1
            
            if audio_only:
                caption = f"""
🎵 <b>تم استخراج الصوت!</b>

🎬 <b>{result['title'][:150]}</b>
👤 <b>المؤلف:</b> {result['author']}

⚡️ @DownloaderBot
"""
                await processing_msg.delete()
                
                try:
                    await message.answer_audio(
                        audio=result["url"],
                        caption=caption,
                        reply_markup=tiktok_menu(),
                        parse_mode="HTML",
                        title=result['title'][:50],
                        performer=result['author']
                    )
                except Exception:
                    await message.answer_document(
                        document=result["url"],
                        caption=caption,
                        reply_markup=tiktok_menu(),
                        parse_mode="HTML"
                    )
            else:
                caption = f"""
🎵 <b>تم التحميل من تيك توك!</b>

🎬 <b>{result['title'][:150]}</b>
👤 <b>المؤلف:</b> {result['author']}
⏱️ <b>المدة:</b> {result.get('duration', 'N/A')} ثانية
👁️ <b>المشاهدات:</b> {result.get('views', 'N/A')}

✅ بدون علامة مائية
⚡️ @DownloaderBot
"""
                await processing_msg.delete()
                
                video_url = result.get("hd_url", result["url"]) or result["url"]
                
                try:
                    await message.answer_video(
                        video=video_url,
                        caption=caption,
                        reply_markup=tiktok_menu(),
                        parse_mode="HTML",
                        supports_streaming=True,
                        thumbnail=result.get("thumbnail")
                    )
                except Exception:
                    await message.answer_document(
                        document=video_url,
                        caption=caption,
                        reply_markup=tiktok_menu(),
                        parse_mode="HTML"
                    )
        else:
            await processing_msg.edit_text(
                f"❌ <b>خطأ:</b> {result['error']}\n\n"
                "🔁 <b>حاول مرة أخرى:</b>",
                reply_markup=tiktok_menu(),
                parse_mode="HTML"
            )
    
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ <b>حدث خطأ:</b> {str(e)[:200]}\n\n"
            "🔁 <b>حاول مرة أخرى:</b>",
            reply_markup=tiktok_menu(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("tt_"))
async def tiktok_options(callback: CallbackQuery, state: FSMContext):
    """خيارات تيك توك"""
    action = callback.data
    
    if action == "tt_video":
        text = """
🎬 <b>تحميل فيديو تيك توك</b>

┌────────────────────────
│ ✅ بدون علامة مائية
│ ✅ جودة عالية HD
└────────────────────────

⚡️ <b>أرسل رابط الفيديو الآن:</b>
"""
        await state.clear()
        await state.set_state(BotStates.waiting_for_tiktok_url)
    
    elif action == "tt_audio":
        await state.clear()
        await state.update_data(audio_only=True)
        await state.set_state(BotStates.waiting_for_tiktok_url)
        text = """
🎵 <b>تحميل صوت تيك توك</b>

┌────────────────────────
│ 🎵 استخراج الصوت فقط
│ ✅ جودة عالية
└────────────────────────

⚡️ <b>أرسل رابط الفيديو الآن:</b>
"""
    elif action == "tt_link":
        text = """
🔗 <b>إرسال رابط تيك توك</b>

⚡️ <b>أرسل الرابط الآن:</b>
"""
        await state.clear()
        await state.set_state(BotStates.waiting_for_tiktok_url)
    
    await callback.message.edit_text(text, reply_markup=tiktok_menu(), parse_mode="HTML")
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# يوتيوب - البحث
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "search_youtube")
async def search_youtube_start(callback: CallbackQuery, state: FSMContext):
    """بدء البحث في يوتيوب"""
    await state.set_state(BotStates.waiting_for_search_query)
    text = """
🔍 <b>البحث في يوتيوب</b>

📝 <b>اكتب ما تريد البحث عنه:</b>

<code>مثال: أغنية حماسية</code>
<code>مثال: دورة برمجة بايثون</code>
"""
    await callback.message.edit_text(text, reply_markup=cancel_button(), parse_mode="HTML")
    await callback.answer()


@router.message(BotStates.waiting_for_search_query)
async def process_search_query(message: Message, state: FSMContext, bot: Bot):
    """معالجة استعلام البحث"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer(
            "❌ <b>استعلام البحث قصير جداً!</b>\n\n"
            "📝 <b>اكتب كلمة بحث أطول:</b>",
            reply_markup=cancel_button(),
            parse_mode="HTML"
        )
        return
    
    processing_msg = await message.answer(
        f"🔍 <b>جاري البحث عن:</b> <i>{query[:50]}</i>\n"
        "<i>قد يستغرق بضع ثوانٍ...</i>",
        parse_mode="HTML"
    )
    
    try:
        results = await search_youtube(query, max_results=10)
        
        if results:
            await state.update_data(search_results=results, search_query=query)
            
            text = f"🔍 <b>نتائج البحث عن:</b> <i>{query[:40]}</i>\n\n"
            for i, result in enumerate(results[:10], 1):
                duration = result.get('duration', '')
                if isinstance(duration, int):
                    mins, secs = divmod(duration, 60)
                    duration = f"{mins}:{secs:02d}"
                elif not duration:
                    duration = "N/A"
                
                author = result.get('author', '')
                text += f"{i}. <b>{result['title'][:45]}</b>\n   👤 {author[:20]} | ⏱ {duration}\n\n"
            
            await processing_msg.delete()
            await message.answer(
                text,
                reply_markup=search_results_keyboard(results, query),
                parse_mode="HTML"
            )
        else:
            await processing_msg.edit_text(
                "❌ <b>لم يتم العثور على نتائج!</b>\n\n"
                "🔍 <b>جرب بحثاً مختلفاً:</b>",
                reply_markup=back_button("search_youtube"),
                parse_mode="HTML"
            )
    
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ <b>حدث خطأ أثناء البحث:</b> {str(e)[:200]}\n\n"
            "🔍 <b>حاول مرة أخرى:</b>",
            reply_markup=back_button("search_youtube"),
            parse_mode="HTML"
        )


# ═══════════════════════════════════════════════════════════
# يوتيوب - التحميل
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "yt_video")
async def yt_video_option(callback: CallbackQuery, state: FSMContext):
    """تحميل فيديو يوتيوب"""
    await state.clear()
    await state.set_state(BotStates.waiting_for_youtube_url)
    text = """
📹 <b>تحميل فيديو يوتيوب</b>

⚡️ <b>أرسل رابط الفيديو الآن:</b>

<code>https://youtube.com/watch?v=ABC123</code>
<code>https://youtu.be/ABC123</code>
"""
    await callback.message.edit_text(text, reply_markup=cancel_button(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "yt_audio")
async def yt_audio_option(callback: CallbackQuery, state: FSMContext):
    """تحميل صوت يوتيوب"""
    await state.clear()
    await state.set_state(BotStates.waiting_for_youtube_url)
    await state.update_data(is_audio=True)
    text = """
🎵 <b>تحميل صوت يوتيوب (MP3)</b>

┌────────────────────────
│ 🎵 صيغة MP3
│ ✅ جودة عالية
│ ⬇️ حجم صغير
└────────────────────────

⚡️ <b>أرسل رابط الفيديو الآن:</b>

<code>https://youtube.com/watch?v=ABC123</code>
"""
    await callback.message.edit_text(text, reply_markup=cancel_button(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "yt_link")
async def yt_link_option(callback: CallbackQuery, state: FSMContext):
    """إرسال رابط يوتيوب"""
    await state.clear()
    await state.set_state(BotStates.waiting_for_youtube_url)
    text = """
🔗 <b>إرسال رابط يوتيوب</b>

⚡️ <b>أرسل الرابط الآن:</b>
"""
    await callback.message.edit_text(text, reply_markup=cancel_button(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_youtube")
async def back_youtube(callback: CallbackQuery, state: FSMContext):
    """العودة لقائمة يوتيوب"""
    await state.clear()
    text = """
📺 <b>يوتيوب داونلودر</b>

┌────────────────────────
│ 📹 فيديو بجودات متعددة
│ 🎵 صوت MP3 بجودة عالية
│ 🔍 بحث مباشر
└────────────────────────

⚡️ <b>اختر خياراً:</b>
"""
    await callback.message.edit_text(text, reply_markup=youtube_menu(), parse_mode="HTML")
    await callback.answer()


@router.message(BotStates.waiting_for_youtube_url)
async def process_youtube_url(message: Message, state: FSMContext, bot: Bot):
    """معالجة رابط يوتيوب"""
    url = message.text.strip()
    
    if not is_youtube_url(url):
        await message.answer(
            "❌ <b>رابط يوتيوب غير صالح!</b>\n\n"
            "📌 <b>أمثلة صحيحة:</b>\n"
            "• https://youtube.com/watch?v=ABC\n"
            "• https://youtu.be/ABC\n\n"
            "🔁 <b>أرسل رابطاً صحيحاً:</b>",
            reply_markup=cancel_button(),
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    is_audio = data.get("is_audio", False)
    
    if is_audio:
        # Direct audio download
        processing_msg = await message.answer(
            "🎵 <b>جاري تحميل الصوت...</b>\n"
            "<i>قد يستغرق بضع ثوانٍ...</i>",
            parse_mode="HTML"
        )
        
        try:
            result = await download_youtube_audio(url, bitrate="192")
            
            if result["success"]:
                user_stats["downloads"] += 1
                file_path = result["file_path"]
                
                info = await get_video_info(url)
                title = info["title"] if info else "YouTube Audio"
                author = info["author"] if info else "YouTube"
                
                caption = f"""
🎵 <b>{title[:100]}</b>

✅ تم التحميل بنجاح!
⚡️ @DownloaderBot
"""
                await processing_msg.delete()
                
                audio_file = FSInputFile(file_path)
                await message.answer_audio(
                    audio=audio_file,
                    caption=caption,
                    reply_markup=youtube_menu(),
                    parse_mode="HTML",
                    title=title[:50],
                    performer=author
                )
                
                # Cleanup
                try:
                    os.remove(file_path)
                except:
                    pass
            else:
                await processing_msg.edit_text(
                    f"❌ <b>خطأ:</b> {result['error']}\n\n"
                    "🔁 <b>حاول مرة أخرى:</b>",
                    reply_markup=youtube_menu(),
                    parse_mode="HTML"
                )
        except Exception as e:
            await processing_msg.edit_text(
                f"❌ <b>حدث خطأ:</b> {str(e)[:200]}\n\n"
                "🔁 <b>حاول مرة أخرى:</b>",
                reply_markup=youtube_menu(),
                parse_mode="HTML"
            )
    else:
        # Show quality options
        processing_msg = await message.answer(
            "⏳ <b>جاري جلب معلومات الفيديو...</b>",
            parse_mode="HTML"
        )
        
        try:
            info = await get_video_info(url)
            
            if info:
                title = info["title"]
                thumbnail = info["thumbnail"]
                duration = info["duration"]
                mins, secs = divmod(duration, 60)
                
                text = f"""
📺 <b>{title[:100]}</b>

⏱ <b>المدة:</b> {mins}:{secs:02d}
👁️ <b>المشاهدات:</b> {info['views']:,}
👤 <b>القناة:</b> {info['author']}

📌 <b>اختر الجودة:</b>
"""
                await processing_msg.delete()
                await message.answer_photo(
                    photo=thumbnail,
                    caption=text,
                    reply_markup=quality_menu(url, is_audio=False),
                    parse_mode="HTML"
                )
                await state.update_data(youtube_url=url)
            else:
                await processing_msg.edit_text(
                    "❌ <b>تعذر جلب معلومات الفيديو!</b>\n\n"
                    "🔁 <b>حاول مرة أخرى:</b>",
                    reply_markup=youtube_menu(),
                    parse_mode="HTML"
                )
        except Exception as e:
            await processing_msg.edit_text(
                f"❌ <b>حدث خطأ:</b> {str(e)[:200]}\n\n"
                "🔁 <b>حاول مرة أخرى:</b>",
                reply_markup=youtube_menu(),
                parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("ytvid|"))
async def download_yt_video(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """تحميل فيديو يوتيوب بجودة محددة"""
    parts = callback.data.split("|")
    if len(parts) != 3:
        await callback.answer("❌ خطأ في البيانات", show_alert=True)
        return
    
    url = parts[1]
    quality = parts[2]
    
    await callback.answer(f"⏳ جاري التحميل بجودة {quality}p...")
    
    try:
        processing_msg = await callback.message.edit_caption(
            caption=f"⏳ <b>جاري التحميل بجودة {quality}p...</b>\n"
                    "<i>قد يستغرق بضع دقائق للفيديوهات الطويلة</i>",
            reply_markup=cancel_button(),
            parse_mode="HTML"
        )
    except Exception:
        processing_msg = await callback.message.answer(
            f"⏳ <b>جاري التحميل بجودة {quality}p...</b>",
            parse_mode="HTML"
        )
    
    try:
        result = await download_youtube_video(url, quality=quality)
        
        if result["success"]:
            user_stats["downloads"] += 1
            file_path = result["file_path"]
            
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            info = await get_video_info(url)
            title = info["title"] if info else "YouTube Video"
            
            caption = f"""
📺 <b>{title[:100]}</b>

📊 <b>الجودة:</b> {quality}p
📦 <b>الحجم:</b> {size_mb:.1f} MB

✅ تم التحميل بنجاح!
⚡️ @DownloaderBot
"""
            try:
                await processing_msg.delete()
            except:
                pass
            
            video_file = FSInputFile(file_path)
            await callback.message.answer_video(
                video=video_file,
                caption=caption,
                reply_markup=youtube_menu(),
                parse_mode="HTML",
                supports_streaming=True
            )
            
            # Cleanup
            try:
                os.remove(file_path)
            except:
                pass
        else:
            error_text = (
                f"❌ <b>خطأ:</b> {result['error']}\n\n"
                "🔁 <b>حاول بجودة أقل أو رابط آخر:</b>"
            )
            try:
                await processing_msg.edit_text(
                    error_text,
                    reply_markup=youtube_menu(),
                    parse_mode="HTML"
                )
            except:
                await callback.message.answer(
                    error_text,
                    reply_markup=youtube_menu(),
                    parse_mode="HTML"
                )
    except Exception as e:
        error_text = (
            f"❌ <b>حدث خطأ:</b> {str(e)[:200]}\n\n"
            "🔁 <b>حاول مرة أخرى:</b>"
        )
        try:
            await processing_msg.edit_text(
                error_text,
                reply_markup=youtube_menu(),
                parse_mode="HTML"
            )
        except:
            await callback.message.answer(
                error_text,
                reply_markup=youtube_menu(),
                parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("ytaudio|"))
async def download_yt_audio(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """تحميل صوت يوتيوب"""
    parts = callback.data.split("|")
    if len(parts) != 3:
        await callback.answer("❌ خطأ في البيانات", show_alert=True)
        return
    
    url = parts[1]
    bitrate = parts[2]
    
    await callback.answer(f"⏳ جاري تحميل الصوت بجودة {bitrate}kbps...")
    
    processing_msg = await callback.message.answer(
        f"🎵 <b>جاري تحميل الصوت بجودة {bitrate}kbps...</b>\n"
        "<i>قد يستغرق بضع ثوانٍ...</i>",
        parse_mode="HTML"
    )
    
    try:
        result = await download_youtube_audio(url, bitrate=bitrate)
        
        if result["success"]:
            user_stats["downloads"] += 1
            file_path = result["file_path"]
            
            info = await get_video_info(url)
            title = info["title"] if info else "YouTube Audio"
            author = info["author"] if info else "YouTube"
            
            caption = f"""
🎵 <b>{title[:100]}</b>

✅ تم التحميل بنجاح!
⚡️ @DownloaderBot
"""
            await processing_msg.delete()
            
            audio_file = FSInputFile(file_path)
            await callback.message.answer_audio(
                audio=audio_file,
                caption=caption,
                reply_markup=youtube_menu(),
                parse_mode="HTML",
                title=title[:50],
                performer=author
            )
            
            # Cleanup
            try:
                os.remove(file_path)
            except:
                pass
        else:
            await processing_msg.edit_text(
                f"❌ <b>خطأ:</b> {result['error']}\n\n"
                "🔁 <b>حاول مرة أخرى:</b>",
                reply_markup=youtube_menu(),
                parse_mode="HTML"
            )
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ <b>حدث خطأ:</b> {str(e)[:200]}\n\n"
            "🔁 <b>حاول مرة أخرى:</b>",
            reply_markup=youtube_menu(),
            parse_mode="HTML"
        )


# ═══════════════════════════════════════════════════════════
# نتائج البحث - تحميل
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("ytdl|"))
async def download_search_result(callback: CallbackQuery, state: FSMContext):
    """تحميل نتيجة بحث"""
    url = callback.data.split("|", 1)[1]
    
    await state.update_data(selected_video=url)
    
    processing_msg = await callback.message.answer(
        "⏳ <b>جاري جلب المعلومات...</b>",
        parse_mode="HTML"
    )
    
    try:
        info = await get_video_info(url)
        if info:
            title = info["title"]
            thumbnail = info["thumbnail"]
            duration = info["duration"]
            mins, secs = divmod(duration, 60)
            
            text = f"""
📺 <b>{title[:100]}</b>

⏱ <b>المدة:</b> {mins}:{secs:02d}
👁️ <b>المشاهدات:</b> {info['views']:,}
👤 <b>القناة:</b> {info['author']}

📌 <b>اختر نوع التحميل:</b>
"""
            await processing_msg.delete()
            await callback.message.answer_photo(
                photo=thumbnail,
                caption=text,
                reply_markup=download_options_keyboard(url),
                parse_mode="HTML"
            )
        else:
            await processing_msg.delete()
            await callback.message.answer(
                "📌 <b>اختر نوع التحميل:</b>",
                reply_markup=download_options_keyboard(url),
                parse_mode="HTML"
            )
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ <b>خطأ:</b> {str(e)[:200]}",
            reply_markup=youtube_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("ytdl_video|"))
async def download_search_video(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """تحميل فيديو من نتيجة بحث"""
    url = callback.data.split("|", 1)[1]
    
    await callback.answer("⏳ جاري جلب خيارات الجودة...")
    
    try:
        info = await get_video_info(url)
        if info:
            title = info["title"]
            thumbnail = info["thumbnail"]
            duration = info["duration"]
            mins, secs = divmod(duration, 60)
            
            text = f"""
📺 <b>{title[:100]}</b>

⏱ <b>المدة:</b> {mins}:{secs:02d}
👁️ <b>المشاهدات:</b> {info['views']:,}

📌 <b>اختر الجودة:</b>
"""
            await callback.message.answer_photo(
                photo=thumbnail,
                caption=text,
                reply_markup=quality_menu(url, is_audio=False),
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                "📌 <b>اختر الجودة:</b>",
                reply_markup=quality_menu(url, is_audio=False),
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.message.answer(
            f"❌ <b>خطأ:</b> {str(e)[:200]}",
            reply_markup=youtube_menu(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("ytdl_audio|"))
async def download_search_audio(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """تحميل صوت من نتيجة بحث"""
    url = callback.data.split("|", 1)[1]
    
    await callback.answer("⏳ جاري تحميل الصوت...")
    
    processing_msg = await callback.message.answer(
        "🎵 <b>جاري تحميل الصوت...</b>\n"
        "<i>قد يستغرق بضع ثوانٍ...</i>",
        parse_mode="HTML"
    )
    
    try:
        result = await download_youtube_audio(url, bitrate="192")
        
        if result["success"]:
            user_stats["downloads"] += 1
            file_path = result["file_path"]
            
            info = await get_video_info(url)
            title = info["title"] if info else "YouTube Audio"
            author = info["author"] if info else "YouTube"
            
            caption = f"""
🎵 <b>{title[:100]}</b>

✅ تم التحميل بنجاح!
⚡️ @DownloaderBot
"""
            await processing_msg.delete()
            
            audio_file = FSInputFile(file_path)
            await callback.message.answer_audio(
                audio=audio_file,
                caption=caption,
                reply_markup=youtube_menu(),
                parse_mode="HTML",
                title=title[:50],
                performer=author
            )
            
            try:
                os.remove(file_path)
            except:
                pass
        else:
            await processing_msg.edit_text(
                f"❌ <b>خطأ:</b> {result['error']}",
                reply_markup=youtube_menu(),
                parse_mode="HTML"
            )
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ <b>حدث خطأ:</b> {str(e)[:200]}",
            reply_markup=youtube_menu(),
            parse_mode="HTML"
        )


# ═══════════════════════════════════════════════════════════
# أي رابط
# ═══════════════════════════════════════════════════════════

@router.message(BotStates.waiting_for_generic_url)
async def process_generic_url(message: Message, state: FSMContext, bot: Bot):
    """معالجة أي رابط"""
    url = message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer(
            "❌ <b>الرابط غير صالح!</b>\n\n"
            "📌 يجب أن يبدأ الرابط بـ http:// أو https://\n"
            "🔁 <b>أرسل رابطاً صحيحاً:</b>",
            reply_markup=cancel_button(),
            parse_mode="HTML"
        )
        return
    
    processing_msg = await message.answer(
        "⏳ <b>جاري تحليل الرابط...</b>\n"
        "<i>يتم التعرف على نوع الموقع تلقائياً</i>",
        parse_mode="HTML"
    )
    
    try:
        # Detect platform and route
        if is_instagram_url(url):
            await processing_msg.delete()
            await state.set_state(BotStates.waiting_for_instagram_url)
            await process_instagram_url(message, state, bot)
            return
        
        if is_tiktok_url(url):
            await processing_msg.delete()
            await state.set_state(BotStates.waiting_for_tiktok_url)
            await process_tiktok_url(message, state, bot)
            return
        
        if is_youtube_url(url):
            await processing_msg.delete()
            await state.set_state(BotStates.waiting_for_youtube_url)
            await process_youtube_url(message, state, bot)
            return
        
        # Generic download
        await processing_msg.edit_text(
            "⏳ <b>جاري التحميل...</b>\n"
            "<i>قد يستغرق بعض الوقت للملفات الكبيرة</i>",
            parse_mode="HTML"
        )
        
        result = await download_generic(url)
        
        if result["success"]:
            user_stats["downloads"] += 1
            file_path = result["file_path"]
            file_size = result.get("size", os.path.getsize(file_path))
            size_mb = file_size / (1024 * 1024)
            
            caption = f"""
✅ <b>تم التحميل بنجاح!</b>

📦 <b>الحجم:</b> {size_mb:.1f} MB
⚡️ @DownloaderBot
"""
            await processing_msg.delete()
            
            # Determine file type and send accordingly
            ext = os.path.splitext(file_path)[1].lower()
            media_file = FSInputFile(file_path)
            
            if ext in ('.mp3', '.m4a', '.ogg', '.wav', '.aac', '.flac'):
                await message.answer_audio(
                    audio=media_file,
                    caption=caption,
                    reply_markup=main_menu(),
                    parse_mode="HTML"
                )
            elif ext in ('.mp4', '.webm', '.mkv', '.mov', '.avi'):
                await message.answer_video(
                    video=media_file,
                    caption=caption,
                    reply_markup=main_menu(),
                    parse_mode="HTML",
                    supports_streaming=True
                )
            elif ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'):
                await message.answer_photo(
                    photo=media_file,
                    caption=caption,
                    reply_markup=main_menu(),
                    parse_mode="HTML"
                )
            else:
                await message.answer_document(
                    document=media_file,
                    caption=caption,
                    reply_markup=main_menu(),
                    parse_mode="HTML"
                )
            
            # Cleanup
            try:
                os.remove(file_path)
            except:
                pass
        else:
            await processing_msg.edit_text(
                f"❌ <b>خطأ:</b> {result['error']}",
                reply_markup=main_menu(),
                parse_mode="HTML"
            )
    
    except Exception as e:
        error_msg = str(e)
        if "entity too large" in error_msg.lower() or "file is too big" in error_msg.lower():
            await processing_msg.edit_text(
                "❌ <b>الملف كبير جداً!</b>\n\n"
                "📌 حد أقصى لحجم الملف: 2GB\n"
                "🔁 <b>جرب ملفاً أصغر:</b>",
                reply_markup=main_menu(),
                parse_mode="HTML"
            )
        else:
            await processing_msg.edit_text(
                f"❌ <b>حدث خطأ:</b> {error_msg[:300]}",
                reply_markup=main_menu(),
                parse_mode="HTML"
            )


# ═══════════════════════════════════════════════════════════
# إلغاء
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """إلغاء العملية"""
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>تم الإلغاء</b>\n\n"
        "📌 اختر من القائمة:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# معالجة الرسائل النصية العامة
# ═══════════════════════════════════════════════════════════

@router.message()
async def handle_text(message: Message, state: FSMContext, bot: Bot):
    """معالجة أي رسالة نصية - التحقق من الروابط"""
    text = message.text.strip()
    current_state = await state.get_state()
    
    # Skip if we're waiting for specific input in a state
    if current_state:
        return
    
    # Check if it's a URL
    if text.startswith("http://") or text.startswith("https://"):
        await message.answer(
            "🔍 <b>تم اكتشاف رابط!</b>\n"
            "⏳ <b>جاري المعالجة...</b>",
            parse_mode="HTML"
        )
        
        if is_instagram_url(text):
            await state.set_state(BotStates.waiting_for_instagram_url)
            await process_instagram_url(message, state, bot)
        elif is_tiktok_url(text):
            await state.set_state(BotStates.waiting_for_tiktok_url)
            await process_tiktok_url(message, state, bot)
        elif is_youtube_url(text):
            await state.set_state(BotStates.waiting_for_youtube_url)
            await process_youtube_url(message, state, bot)
        else:
            await state.set_state(BotStates.waiting_for_generic_url)
            await process_generic_url(message, state, bot)
    else:
        # Not a URL, show main menu
        await message.answer(
            "🤔 <b>لم أفهم طلبك!</b>\n\n"
            "📌 <b>أرسل رابط فيديو مباشرة</b>\n"
            "أو اختر من القائمة:",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
