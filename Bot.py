import telebot
from telebot.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import json
import base64
import io
import os
import tempfile
import subprocess
from PIL import Image

# ========== الإعدادات ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://your-app.vercel.app")

bot = telebot.TeleBot(BOT_TOKEN)

# ========== /start ==========
@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        "🎨 افتح استوديو الملصقات",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))
    bot.send_message(
        message.chat.id,
        "🎨 *مرحباً بك في استوديو الملصقات المميزة*\n\n"
        "صمم ملصقاتك الخاصة بخلفية شفافة، خطوط عربية احترافية، وجودة عالية.\n\n"
        "اضغط الزر أدناه للبدء 👇",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ========== استقبال البيانات ==========
@bot.message_handler(content_types=['web_app_data'])
def handle_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        
        if data['action'] == 'save':
            img_data = data['image'].split(',')[1]
            img_bytes = base64.b64decode(img_data)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            img = img.resize((100, 100), Image.LANCZOS)
            
            # حفظ PNG شفاف
            png_out = io.BytesIO()
            img.save(png_out, format='PNG', optimize=True)
            png_out.seek(0)
            
            # محاولة إنشاء WebM
            webm_ready = False
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    img.save(f.name, "PNG")
                    png_path = f.name
                
                webm_path = png_path.replace(".png", ".webm")
                cmd = [
                    "ffmpeg", "-y", "-loop", "1", "-i", png_path,
                    "-t", "2", "-c:v", "libvpx-vp9",
                    "-pix_fmt", "yuva420p", "-b:v", "200k",
                    webm_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(webm_path):
                    with open(webm_path, "rb") as f:
                        bot.send_document(
                            message.chat.id, f,
                            visible_file_name="premium_emoji.webm",
                            caption="✅ *ملصقك المميز (WebM)*\n📌 أضفه لحزمة ملصقاتك",
                            parse_mode='Markdown'
                        )
                    webm_ready = True
                
                os.unlink(png_path)
                if os.path.exists(webm_path):
                    os.unlink(webm_path)
            except Exception as e:
                print(f"ffmpeg error: {e}")
            
            if not webm_ready:
                bot.send_document(
                    message.chat.id, png_out,
                    visible_file_name="premium_emoji.png",
                    caption="✅ *ملصقك المميز (PNG شفاف)*\n📌 أضفه لحزمة ملصقاتك",
                    parse_mode='Markdown'
                )
            
            bot.send_message(
                message.chat.id,
                "⚠️ *ملاحظة:*\n"
                "لاستخدامه كإيموجي مميز (جنب الاسم أو في الرسائل)\n"
                "تحتاج اشتراك *Telegram Premium*.",
                parse_mode='Markdown'
            )
    
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

# ========== التشغيل ==========
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
