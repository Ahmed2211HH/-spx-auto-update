import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
from PIL import Image
import pytesseract
import io

TOKEN = "7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg"
GROUP_ID = -1002624628833

logging.basicConfig(level=logging.INFO)

def generate_plan(spx_price: float) -> str:
    spx_price = round(spx_price)
    call_entry = spx_price + 10
    call_targets = [call_entry + 10, call_entry + 25, call_entry + 50]
    put_entry = spx_price - 10
    put_targets = [put_entry - 15, put_entry - 30, put_entry - 55]
    today = datetime.now().strftime("📅 الخطة اليومية – %A | %d %B %Y")

    return f"""
{today}
⸻

✅ نقطة دخول Call (شراء صعودي) 📈
{call_entry} 🟢
• الأهداف: {call_targets[0]}, {call_targets[1]}, {call_targets[2]}

🔻 نقطة دخول Put (شراء هبوطي) 📉
{put_entry} 🔴
• الأهداف: {put_targets[0]}, {put_targets[1]}, {put_targets[2]}

📌 السعر الحالي: {spx_price}
⸻
⚠️ ملاحظات:
• لا تدخل قبل تحقق الشروط
• إدارة رأس المال مهمة
• تابع السوق ولا تعتمد فقط على الخطة
"""

def analyze_contract_text(text: str) -> str:
    try:
        lines = text.splitlines()
        price_line = next((l for l in lines if "$" in l), None)
        if not price_line:
            return "لم أستطع قراءة بيانات العقد من الصورة."

        name = price_line.split()[0]
        price = float(price_line.split()[1])
        target_1 = round(price * 1.3, 2)
        target_2 = round(price * 1.6, 2)
        stop_loss = round(price * 0.6, 2)

        return f"""🎯 تحليل العقد: {name}
💵 سعر الدخول: {price}
🎯 الأهداف:
• الأول: {target_1}
• الثاني: {target_2}
❌ وقف الخسارة: {stop_loss}"""
    except:
        return "حدث خطأ أثناء تحليل العقد. تأكد من وضوح الصورة."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل 'الخطة اليومية' أو صورة لعقد لتحليلها.")

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # سعر وهمي لمحاكاة SPX الحالي (غير متصل ببيانات حقيقية الآن)
    spx_price = 6016
    message = generate_plan(spx_price)
    await update.message.reply_text(message)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    byte_stream = io.BytesIO()
    await file.download(out=byte_stream)
    byte_stream.seek(0)
    img = Image.open(byte_stream)
    text = pytesseract.image_to_string(img)
    result = analyze_contract_text(text)
    await update.message.reply_text(result)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("الخطة", plan))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
