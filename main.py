import yfinance as yf
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import datetime

# إعدادات البوت
TOKEN = "7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg"
OWNER_ID = 7123756100

# تحليل SPX اللحظي
def analyze_spx():
    symbol = "^GSPC"
    data = yf.download(symbol, period="1d", interval="5m")

    if data.empty or len(data) < 2:
        return "لا توجد بيانات كافية للتحليل حالياً."

    closes = data["Close"]
    last_price = round(closes.iloc[-1], 2)
    start_price = round(closes.iloc[0], 2)

    direction = "صاعد" if last_price > start_price else "هابط"
    wave = "موجة دافعة" if abs(last_price - start_price) > 10 else "موجة تصحيحية"
    
    entry = last_price
    target1 = round(entry + 10, 2) if direction == "صاعد" else round(entry - 10, 2)
    target2 = round(entry + 20, 2) if direction == "صاعد" else round(entry - 20, 2)
    stop_loss = round(entry - 8, 2) if direction == "صاعد" else round(entry + 8, 2)

    analysis = f"""
تحليل SPX اللحظي – US500
⏱️ الفريم: 5 دقائق
الاتجاه: {direction}
الموجة: {wave}

نقطة الدخول: {entry}
🎯 الهدف 1: {target1}
🎯 الهدف 2: {target2}
❌ وقف الخسارة: {stop_loss}

استناداً إلى حركة US500 اللحظية.
    """
    return analysis.strip()

# إرسال التحليل عند الضغط على الزر
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    analysis = analyze_spx()
    await context.bot.send_message(chat_id=query.message.chat_id, text=analysis)

# بدء البوت وعرض الزر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("هذا البوت خاص.")
        return

    keyboard = [[InlineKeyboardButton("تحليل SPX الآن", callback_data="analyze_spx")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر من القائمة:", reply_markup=reply_markup)

# تشغيل البوت
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
