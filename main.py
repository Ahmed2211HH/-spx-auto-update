import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import openai
import os

# استدعاء المفاتيح من البيئة
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
logging.basicConfig(level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي متخصص في السوق الأمريكي، خصوصًا في تحليل عقود SPX و Nasdaq، وترد باللغة العربية بأسلوب احترافي وسريع وواضح."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = completion.choices[0].message.content
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"حدث خطأ: {str(e)}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
