import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from datetime import datetime

BOT_TOKEN = "7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg"
CHAT_ID = "-1002624628833"

def fetch_spx_price():
    url = "https://symbol-search.tradingview.com/symbol_search/"
    params = {"text": "US500", "exchange": "AMEX", "limit": "1"}
    resp = requests.get(url, params=params).json()
    if not resp: return None
    symbol = resp[0]["symbol"]  # ex: "SPX:US500"
    quote_url = f"https://scanner.tradingview.com/america/scan"
    query = {
        "symbols": {"tickers": [symbol], "query": {"types": []}},
        "columns": ["close"]
    }
    res = requests.post(quote_url, json=query).json()
    return res["data"][0]["d"][0]

def build_plan(price):
    entry_call = round(price + 10, 1)
    entry_put = round(price - 10, 1)
    targets_call = [entry_call + 15, entry_call + 30, entry_call + 60]
    targets_put = [entry_put - 15, entry_put - 30, entry_put - 60]
    stop_call = round(entry_call - 5, 1)
    stop_put = round(entry_put + 5, 1)
    return entry_call, targets_call, stop_call, entry_put, targets_put, stop_put

async def plan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    price = fetch_spx_price()
    if price is None:
        await ctx.bot.send_message(chat_id=CHAT_ID,
            text="❌ خطأ في جلب سعر SPX الآن، حاول لاحقًا.")
        return
    ec, tc, sc, ep, tp, sp = build_plan(price)
    text = f"""
📅 *خطة اليوم – تداول SPX*
التاريخ: {datetime.now().strftime('%Y-%m-%d')}

📈 *Call Entry*: {ec}
• أهداف: {tc[0]}, {tc[1]}, {tc[2]}
• وقف خسارة: {sc}

📉 *Put Entry*: {ep}
• أهداف: {tp[0]}, {tp[1]}, {tp[2]}
• وقف خسارة: {sp}

📌 السوق حالياً عند: {price:.2f}  
📿 اذكر الله دائمًا ✨
⚠️ لا تدخل إلا إذا نزل السعر لفاصل ساعة وثبت أعلى/أسفل النقاط.

✅ إدارة رأس المال ضرورية، والأرقام إرشادية فقط.
"""
    await ctx.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("plan", plan))
    app.run_polling()
