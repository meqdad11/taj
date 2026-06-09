# بوت التحميل المتكامل

بوت تيليجرام احترافي لتحميل الفيديوهات من مختلف المنصات مع ميزة البحث.

## المميزات

- **إنستغرام** - تحميل Reels وPosts
- **تيك توك** - تحميل بدون علامة مائية
- **يوتيوب** - تحميل فيديو بجودات متعددة (360p, 720p, 1080p) وصوت MP3
- **بحث يوتيوب** - البحث مباشرة داخل البوت
- **أي رابط** - دعم أكثر من 1000 موقع
- **أزرار تنقل** - رجوع وإلغاء في كل خطوة
- **تصميم أنيق** - رسائل منسقة بالكامل

## المتطلبات

- Python 3.9+
- Telegram Bot Token (احصل عليه من @BotFather)
- RapidAPI Key (مجاني)

## التثبيت

1. استنسخ المستودع:
```bash
git clone https://github.com/your-username/download-bot.git
cd download-bot
```

2. ثبّت المتطلبات:
```bash
pip install -r requirements.txt
```

3. انسخ ملف البيئة وعدله:
```bash
cp .env.example .env
nano .env  # عدل المتغيرات
```

4. شغّل البوت:

**وضع Polling (للتطوير المحلي):**
```bash
python app.py polling
```

**وضع Webhook (للإنتاج):**
```bash
python app.py
```

## الإعداد

### الحصول على Telegram Bot Token
1. افتح @BotFather في تيليجرام
2. أرسل `/newbot`
3. اتبع التعليمات واحفظ التوكن

### الحصول على RapidAPI Key
1. سجل في [RapidAPI](https://rapidapi.com)
2. اشترك في APIs المجانية:
   - Instagram Downloader
   - TikTok Video No Watermark
   - YouTube Search Results
3. انسخ الـ X-RapidAPI-Key

## النشر

### Railway
```bash
railway login
railway init
railway up
```

### Render
1. اربط مستودع GitHub
2. اضبط متغيرات البيئة
3. اضبط Start Command: `python app.py`

### Heroku
```bash
heroku create your-bot-name
heroku config:set BOT_TOKEN=your_token
heroku config:set RAPIDAPI_KEY=your_key
git push heroku main
```

## الاستخدام

1. أرسل `/start` للبوت
2. اختر المنصة من القائمة
3. أرسل الرابط أو ابحث
4. استمتع بالتحميل السريع!

## المطور

- Telegram: @dev
- القناة: @channel
