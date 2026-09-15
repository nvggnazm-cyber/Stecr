import telebot
from telebot.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import json
import base64
import io
import os
import re
import time
import random
import string
from PIL import Image

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("افتح الاستوديو", web_app=WebAppInfo(url=WEBAPP_URL)))

    bot.send_message(
        message.chat.id,
        "استوديو الملصقات\n\n"
        "صمم حزم ملصقاتك الخاصة بخطوط عربية أصلية، وأنشئ حزمة حقيقية في تليجرام.\n\n"
        "كيف يعمل؟\n"
        "١. افتح الاستوديو\n"
        "٢. صمم ملصقك\n"
        "٣. أضفه إلى الحزمة\n"
        "٤. اكتب اسم الحزمة\n"
        "٥. استلم الرابط الحقيقي\n\n"
        "اضغط الزر أدناه للبدء:",
        reply_markup=markup
    )


@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "المساعدة\n\n"
        "تصميم الملصق:\n"
        "افتح الاستوديو، اكتب النص، اختر الخط واللون والحجم.\n\n"
        "إنشاء الحزمة:\n"
        "أضف ملصقاً أو أكثر للحزمة، ثم اكتب اسم الحزمة بالإنجليزية (مثل: toe7e)، واضغط إرسال.\n\n"
        "سيصلك رابط حقيقي:\n"
        "t.me/addstickers/اسمك_by_البوت\n\n"
        "ملاحظة:\n"
        "اسم الحزمة يجب أن يكون بالإنجليزية فقط، من ٣ إلى ٢٥ حرفاً."
    )


@bot.message_handler(content_types=['web_app_data'])
def handle_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get('action') == 'create_pack':
            create_pack(message, data)
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, f"حدث خطأ: {str(e)}")


def clean_pack_name(name):
    name = re.sub(r'[^a-zA-Z0-9_]', '', name).lower()
    if not name or len(name) < 3:
        name = "pack_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return name[:25]


def prepare_sticker(image_data):
    img_bytes = base64.b64decode(image_data.split(',')[1])
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    img = img.resize((512, 512), Image.LANCZOS)
    output = io.BytesIO()
    img.save(output, format='PNG', optimize=True)
    output.seek(0)
    return output


def create_pack(message, data):
    stickers = data.get('stickers', [])
    pack_name_raw = data.get('pack_name', 'my_pack')
    pack_title = data.get('pack_title', 'My Stickers')
    user_id = message.from_user.id

    if not stickers:
        bot.send_message(message.chat.id, "لا توجد ملصقات.")
        return

    clean_name = clean_pack_name(pack_name_raw)
    full_name = f"{clean_name}_by_{BOT_USERNAME}"

    bot.send_message(
        message.chat.id,
        f"جاري إنشاء الحزمة...\n\n"
        f"عدد الملصقات: {len(stickers)}\n"
        f"اسم الحزمة: {full_name}"
    )

    try:
        first = prepare_sticker(stickers[0])
        result = bot.create_new_sticker_set(
            user_id=user_id,
            name=full_name,
            title=pack_title,
            emojis="🎨",
            png_sticker=first
        )

        if not result:
            bot.send_message(
                message.chat.id,
                "فشل إنشاء الحزمة.\n"
                "قد يكون الاسم مستخدماً، جرب اسماً آخر."
            )
            return

        success = 1
        for sticker_data in stickers[1:]:
            try:
                s = prepare_sticker(sticker_data)
                bot.add_sticker_to_set(
                    user_id=user_id,
                    name=full_name,
                    emojis="🎨",
                    png_sticker=s
                )
                success += 1
                time.sleep(0.3)
            except Exception as e:
                print(f"Error: {e}")

        link = f"https://t.me/addstickers/{full_name}"

        bot.send_message(
            message.chat.id,
            f"تم إنشاء الحزمة بنجاح.\n\n"
            f"عدد الملصقات: {success}\n"
            f"اسم الحزمة: {full_name}\n\n"
            f"رابط الحزمة:\n{link}"
        )

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إضافة الحزمة لتليجرام", url=link))
        bot.send_message(
            message.chat.id,
            "اضغط الزر لإضافة الحزمة:",
            reply_markup=markup
        )

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"خطأ في إنشاء الحزمة:\n{str(e)}\n\nجرب اسماً مختلفاً."
        )


if __name__ == "__main__":
    print("Bot running...")
    bot.infinity_polling()
