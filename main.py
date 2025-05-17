import matplotlib.pyplot as plt
import yfinance as yf
import io
import datetime
from PIL import Image
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# إعدادات البوت
TOKEN = '7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg'
OWNER_ID = 7123756100

# دالة تحليل السوق (تلقائي حسب اليوم)
def generate_analysis_image():
    today = datetime.datetime.now().weekday()  # 0=Mon ... 6=Sun
    symbol = "^GSPC"

    if today in [5, 6]:  # السبت أو الأحد
        data = yf.download(symbol, period="5d", interval="15m")
        last_day = data.index[-1].date()
        friday_data = data[data.index.date == last_day]
        title = "تحليل استباقي - US500"
        subtitle = "ليوم الإثنين بناءً على إغلاق الجمعة"
        price_data = friday_data
        trade_type = "استباقية"
        tf = "15 دقيقة"
        strategy = "نهاية الأسبوع"
    else:
        data = yf.download(symbol, period="1d", interval="5m")
        title = "تحليل لحظي - US500"
        subtitle = f"بتاريخ {datetime.datetime.now().date()}"
        price_data = data
        trade_type = "لحظية"
        tf = "5 دقائق"
        strategy = "زخم لحظي"

    current_price = round(price_data["Close"].iloc[-1], 2)
    recent_high = round(price_data["High"].max(), 2)
    recent_low = round(price_data["Low"].min(), 2)

    direction = "صاعد" if current_price > price_data["Close"].iloc[0] else "هابط"
    entry = current_price
    target1 = round(current_price + 15, 2) if direction == "صاعد" else round(current_price - 15, 2)
    target2 = round(current_price + 30, 2) if direction == "صاعد" else round(current_price - 30, 2)
    stop_loss = round(recent_low - 10, 2) if direction == "صاعد" else round(recent_high + 10, 2)

    # رسم الصورة
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axis('off')
    ax.text(0.5, 0.95, title, fontsize=16, ha='center', weight='bold')
    ax.text(0.5, 0.90, subtitle, fontsize=10, ha='center', style='italic')
    ax.text(0.05, 0.75, f"الاتجاه: {direction}", fontsize=12)
    ax.text(0.05, 0.65, f"نقطة الدخول: {entry}", fontsize=12)
    ax.text(0.05, 0.55, f"الهدف الأول: {target1}", fontsize=12)
    ax.text(0.05, 0.45, f"الهدف الثاني: {target2}", fontsize=12)
    ax.text(0.05, 0.35, f"وقف الخسارة: {stop_loss}", fontsize=12)
    ax.text(0.05, 0.25, f"نوع الصفقة: {trade_type}", fontsize=12)
    ax.text(0.05, 0.15, f"الفريم: {tf}", fontsize=12)
    ax.text(0.05, 0.05, f"الاستراتيجية: {strategy}", fontsize=12)

    buf = io.BytesIO()
    plt.savefig(buf, format='PNG', bbox_inches='tight')
    buf.seek(0)
    return Image.open(buf)

# إرسال التحليل كصورة
async def send_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("هذا البوت خاص.")
        return

    image = generate_analysis_image()
    bio = io.BytesIO()
    image.save(bio, format='PNG')
    bio.seek(0)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=bio, caption="تحليل SPX الحالي حسب يوم السوق.")

# لوحة التحكم
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("هذا البوت خاص.")
        return

    keyboard = [[InlineKeyboardButton("تحليل SPX الآن", callback_data='analyze_spx')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر من القائمة:", reply_markup=reply_markup)

# التعامل مع الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'analyze_spx':
        image = generate_analysis_image()
        bio = io.BytesIO()
        image.save(bio, format='PNG')
        bio.seek(0)
        await context.bot.send_photo(chat_id=query.message.chat_id, photo=bio, caption="تحليل SPX الحالي حسب يوم السوق.")

# تشغيل التطبيق
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
