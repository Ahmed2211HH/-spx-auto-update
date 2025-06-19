import logging
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import openai

# إعداد المفاتيح
TELEGRAM_TOKEN = "7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg"
OPENAI_API_KEY = "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"

openai.api_key = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)

# تحليل السهم باستخدام GPT
async def analyze_stock(symbol: str) -> str:
    prompt = f"حلل لي سهم {symbol} من السوق الأمريكي بشكل فني مختصر ومباشر يشمل: الاتجاه، الدعم والمقاومة، التوصية، الأهداف المقترحة، ووقف الخسارة، ولا تكرر نفس الرد لكل سهم."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content

# عند استلام رسالة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()
    await update.message.reply_text("🔎 جاري تحليل السهم ...")

    try:
        result = await analyze_stock(symbol)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ أثناء التحليل. حاول مرة أخرى لاحقًا.")

# بدء البوت
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await app.run_polling()

# تشغيل البوت داخل event loop
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
