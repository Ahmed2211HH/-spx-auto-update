import logging
import openai
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ✅ مفاتيح الوصول
TELEGRAM_TOKEN = "7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg"
OPENAI_API_KEY = "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"

openai.api_key = OPENAI_API_KEY

# ✅ تشغيل اللوق لتتبع الأخطاء
logging.basicConfig(level=logging.INFO)

# ✅ أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا بك في مساعد التداول الذكي 🤖\n\nاكتب أي سؤال أو اطلب تحليل العقد، وسأرد عليك مباشرة!")

# ✅ الرد على أي رسالة باستخدام OpenAI
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "أنت مساعد متخصص في التداول، تعطي تحليلات فنية، أهداف العقود، الوقف، ونصائح بناءً على محتوى السؤال."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.6
        )
        reply = response['choices'][0]['message']['content']
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("حدث خطأ أثناء معالجة الطلب. حاول لاحقًا.")

# ✅ تشغيل البوت
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
