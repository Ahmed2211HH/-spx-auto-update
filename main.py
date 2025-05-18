import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging

# توكن البوت مباشرة
TOKEN = "7966051975:AAH1QsBd0PNrmN80kVwHlLTyeFPRFUbZOUk"

logging.basicConfig(level=logging.INFO)

def generate_analysis(symbol, timeframe):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="5d" if timeframe == "لحظي" else "1mo", interval="5m" if timeframe == "لحظي" else "1d")
    
    if hist.empty:
        return f"لم أتمكن من الحصول على بيانات للسهم {symbol.upper()}"

    close_prices = hist["Close"]
    current_price = close_prices.iloc[-1]
    recent_prices = close_prices[-10:]

    direction = "صاعد" if current_price > recent_prices.mean() else "هابط"
    wave = "موجة دافعة" if abs(current_price - recent_prices[-2]) > 0.01 * current_price else "موجة تصحيحية"
    entry = round(current_price, 2)
    stop_loss = round(entry * 0.97, 2)
    target1 = round(entry * 1.03, 2)
    target2 = round(entry * 1.06, 2)

    return f"""تحليل {symbol.upper()} – {ticker.info.get('shortName', 'السهم')}
⏱️ الفريم: {'4 ساعات' if timeframe == 'لحظي' else 'يومي – أسبوعي'}
📊 الاتجاه العام: {direction}
📈 نوع الموجة: {wave}

نقطة الدخول المقترحة: {entry}
🎯 الهدف 1: {target1}
🎯 الهدف 2: {target2}
❌ وقف الخسارة: {stop_loss}
"""

async def handle_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) == 0:
            await update.message.reply_text("اكتب الأمر بالشكل التالي:\n/تحليل AAPL أسبوعي أو لحظي")
            return
        
        symbol = context.args[0]
        timeframe = context.args[1] if len(context.args) > 1 else "أسبوعي"
        analysis = generate_analysis(symbol, timeframe)
        await update.message.reply_text(analysis)
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("حدث خطأ أثناء التحليل.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("تحليل", handle_analysis))
    app.run_polling()

if __name__ == "__main__":
    main()
