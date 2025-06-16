import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from PIL import Image
import pytesseract
import datetime

# إعدادات
TOKEN = '7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg'
CHANNEL_ID = -1002624628833

logging.basicConfig(level=logging.INFO)

# ✅ أمر الخطة اليومية
async def daily_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now()
    weekday = now.strftime("%A")
    date_text = now.strftime("%d %B %Y")
    price = 6016  # السعر الحالي – يمكن تعديله يدويًا أو ربطه لاحقًا بمصدر حي

    message = f"""📅 الخطة اليومية – تداول SPX
اليوم | {weekday} – {date_text}

⸻

✅ نقطة دخول Call (شراء صعودي) 📈
5,990.0 🟢

• الشرط: ثبات السعر أعلى هذا المستوى على فاصل الساعة
• الأهداف المحتملة 🎯:
 • 6,005.0
 • 6,022.0
 • 6,048.0

📌 الوضع الحالي:
السوق يتداول حاليًا عند {price}
نراقب اختراق 5990 والثبات فوقه لتفعيل الدخول الصعودي.

⸻

🔻 نقطة دخول Put (شراء هبوطي) 📉
5,980.0 🔴

• الشرط: كسر هذا المستوى والثبات أسفله على فاصل الساعة
• الأهداف المحتملة 🎯:
 • 5,962.0
 • 5,940.0
 • 5,915.0

📌 الوضع الحالي:
لم يتم التفعيل بعد، ونترقب كسر واضح أسفل 5980 لتأكيد الهبوط.

⸻

📿 اذكر الله دائماً.

⚠️ ملاحظات هامة:
• الالتزام بإدارة رأس المال وعدم الدخول بكامل السيولة
• لا يتم تفعيل أي صفقة إلا بعد تحقق الشروط الفنية بوضوح
• الأهداف إرشادية ولا تعني الوصول الإجباري، تابع السوق بتأنٍ وتعامل بمرونة
"""

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

# ✅ تحليل صورة العقد
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    file_path = "contract.jpg"
    await file.download_to_drive(file_path)

    # قراءة النص من الصورة
    text = pytesseract.image_to_string(Image.open(file_path))

    # محاولة استخراج البيانات
    try:
        price_lines = [line for line in text.split('\n') if "$" in line]
        prices = []
        for line in price_lines:
            for part in line.split():
                if "$" in part:
                    try:
                        val = float(part.replace("$", "").replace(",", ""))
                        prices.append(val)
                    except:
                        continue
        entry = min(prices)
        target1 = round(entry * 1.30, 2)
        target2 = round(entry * 1.60, 2)
        target3 = round(entry * 2.00, 2)
        stop = round(entry * 0.65, 2)

        result = f"""📊 تحليل العقد المرفق:

💵 سعر الدخول: {entry}
🎯 الأهداف:
• الهدف الأول: {target1}
• الهدف الثاني: {target2}
• الهدف الثالث (ممتد): {target3}

❌ وقف الخسارة: كسر {stop} والثبات تحته
"""
    except:
        result = "❌ لم أتمكن من تحليل العقد من الصورة. تأكد من وضوحها."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)

# ✅ تهيئة البوت
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("الخطة", daily_plan))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("✅ Bot is running...")
    app.run_polling()
