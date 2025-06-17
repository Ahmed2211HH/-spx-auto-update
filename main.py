import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import pytesseract
import io
import re

TOKEN = '7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def extract_price_from_text(text):
    match = re.search(r'(\d+\.\d{2})', text)
    return float(match.group(1)) if match else None

def analyze_contract_price(price):
    if price is None:
        return "لم يتم التعرف على السعر من الصورة."
    entry = price
    target1 = round(price * 1.25, 2)
    target2 = round(price * 1.5, 2)
    target3 = round(price * 1.9, 2)
    stop = round(price * 0.7, 2)
    return f'''
📊 تحليل العقد:

🎯 سعر الدخول: {entry}
✅ الهدف ١: {target1}
✅ الهدف ٢: {target2}
✅ الهدف ٣ (ممتد): {target3}
❌ وقف الخسارة: كسر {stop} والثبات تحته

📌 ملاحظة: تأكد من حركة السعر الحالية قبل اتخاذ القرار.
'''

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل صورة العقد (من WeBull) وسأقوم بتحليل السعر وتحديد الأهداف والوقف 🎯")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    photo_bytes = await file.download_as_bytearray()

    image = Image.open(io.BytesIO(photo_bytes))
    text = pytesseract.image_to_string(image)
    price = extract_price_from_text(text)
    result = analyze_contract_price(price)

    await update.message.reply_text(result)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

if __name__ == "__main__":
    app.run_polling()
