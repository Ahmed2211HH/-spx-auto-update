import logging
import openai
import telegram
from telegram.ext import Application, MessageHandler, filters, CommandHandler
import asyncio

# إعدادات البوت
BOT_TOKEN = '7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg'
OPENAI_API_KEY = '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'

openai.api_key = OPENAI_API_KEY
logging.basicConfig(level=logging.INFO)

# دالة التحليل
async def analyze_symbol(symbol):
    prompt = f"""
    حلل لي السهم {symbol} بشكل احترافي وباللغة العربية. 
    أعطني:
    1. الاتجاه الحالي.
    2. الدعم والمقاومة.
    3. التوصية (شراء أو انتظار أو بيع).
    4. الأهداف المتوقعة.
    5. وقف الخسارة.
    لا تكتب اسم ChatGPT.
    """

    try:
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ حدث خطأ أثناء التحليل: {e}"

# الرد على أي رسالة تحتوي رمز سهم
async def handle_message(update, context):
    text = update.message.text.strip().upper()
    if len(text) <= 6 and text.isalnum():
        await update.message.reply_text("⏳ جاري تحليل السهم، لحظة فقط...")
        result = await analyze_symbol(text)
        await update.message.reply_text(result)
    else:
        await update.message.reply_text("📌 أرسل رمز السهم فقط مثل: TSLA أو AAPL")

# أمر البدء
async def start(update, context):
    await update.message.reply_text("👋 مرحبًا بك، أرسل رمز السهم مثل: TSLA وسأقوم بتحليله لك.")

# تشغيل البوت
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
