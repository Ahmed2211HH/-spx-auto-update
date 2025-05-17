import matplotlib.pyplot as plt
import yfinance as yf
import io
import datetime
from PIL import Image
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import pandas as pd

# إعدادات البوت
TOKEN = '7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg'
OWNER_ID = 7123756100

def get_friday_data():
    symbol = "^GSPC"
    data = yf.download(symbol, period="7d", interval="15m")
    if data.empty:
        raise ValueError("لا توجد بيانات متاحة.")
    
    # استخراج بيانات يوم الجمعة الأخير
    data['weekday'] = data.index.to_series().dt.weekday
    friday_data = data[data['weekday'] == 4].drop(columns='weekday')
    if friday_data.empty:
        raise ValueError("بيانات يوم الجمعة غير متوفرة.")
    
    return friday_data

def get_live_data():
    symbol = "^GSPC"
    data = yf.download(symbol, period="1d", interval="5m")
    if data.empty:
        raise ValueError("لا توجد بيانات لحظية حالياً.")
    return data

def generate_analysis_image():
    today = datetime.datetime.now().weekday()  # 0=Mon, ..., 6=Sun
    use_friday = today in [5, 6]  # السبت أو الأحد

    if use_friday:
        price_data = get_friday_data()
        title = "تحليل استباقي - US500"
        subtitle = "بناءً على إغلاق يوم الجمعة"
        tf = "15 دقيقة"
        trade_type = "استباقي"
        strategy = "بيانات الجمعة"
    else:
        price_data = get_live_data()
        title = "تحليل لحظي - US500"
        subtitle = f"بتاريخ {datetime.datetime.now().date()}"
        tf = "5 دقائق"
        trade_type = "لحظي"
        strategy = "تحليل السوق المباشر"

    current_price = round(price_data["Close"].iloc[-1], 2)
    recent_high = round(price_data["High"].max(), 2)
    recent_low = round(price_data["Low"].min(), 2)

    direction = "صاعد" if current_price > price_data["Close"].iloc[0] else "هابط"
    entry = current_price
    target1 = round(entry + 15, 2) if direction == "صاعد" else round(entry - 15, 2)
    target2 = round(entry + 30, 2) if direction == "صاعد" else round(entry - 30, 2)
    stop_loss = round(recent_low - 10, 2) if direction == "صاعد" else round(recent_high + 10, 2)

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

# إرسال التحليل
async def send_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("هذا البوت خاص.")
        return

    try:
        image = generate_analysis_image()
        bio = io.BytesIO()
        image.save(bio, format='PNG')
        bio.seek(0)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=bio, caption="تحليل SPX حسب يوم السوق.")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء التحليل:\n{e}")

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("هذا البوت خاص.")
        return

    keyboard = [[InlineKeyboardButton("تحليل SPX الآن", callback_data='analyze_spx')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر من القائمة:", reply_markup=reply_markup)

# التعامل مع الضغط على الزر
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        image = generate_analysis_image()
        bio = io.BytesIO()
        image.save(bio, format='PNG')
        bio.seek(0)
        await context.bot.send_photo(chat_id=query.message.chat_id, photo=bio, caption="تحليل SPX حسب يوم السوق.")
    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"حدث خطأ أثناء التحليل:\n{e}")

# تشغيل البوت
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
