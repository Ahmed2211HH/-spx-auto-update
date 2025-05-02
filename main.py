import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from playwright.async_api import async_playwright
from keep_alive import keep_alive

# إعدادات البوت
TOKEN = '7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg'
OWNER_ID = 7123756100
CHANNEL_ID = -1002529600259

# تخزين الإعدادات
settings = {
    "symbol": "",
    "threshold": 0.3,
    "last_price": None
}
monitoring = False

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    keyboard = [
        [InlineKeyboardButton("تحديد العقد", callback_data="set_contract")],
        [InlineKeyboardButton("إيقاف التحديث", callback_data="stop_monitor")]
    ]
    await update.message.reply_text("مرحباً! تحكم في العقد من هنا:", reply_markup=InlineKeyboardMarkup(keyboard))

# اختيار العقد
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "set_contract":
        await query.edit_message_text("أرسل اسم العقد (مثال: SPXW 5740C 02May):")
        return
    elif query.data == "stop_monitor":
        global monitoring
        monitoring = False
        await query.edit_message_text("❌ تم إيقاف التحديث.")

# استقبال اسم العقد
async def set_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    settings["symbol"] = update.message.text.strip()
    await update.message.reply_text("الآن أرسل قيمة التحديث (مثل 0.30):")

# استقبال العتبة
async def set_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    try:
        settings["threshold"] = float(update.message.text.strip())
        await update.message.reply_text("✅ تم بدء المراقبة للعقد...")
        asyncio.create_task(monitor_loop(context))
    except:
        await update.message.reply_text("❌ أدخل رقم صحيح مثل 0.30")

# المراقبة والتحديث
async def monitor_loop(context):
    global monitoring
    monitoring = True
    symbol = settings["symbol"]
    threshold = settings["threshold"]
    last_sent = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.webull.com/quote/option")

        await page.fill("input[placeholder='Search']", symbol)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(3000)

        while monitoring:
            try:
                await page.reload()
                await page.wait_for_timeout(2000)
                element = await page.query_selector("div:has-text('$')")
                price_text = await element.inner_text() if element else None

                if price_text and "$" in price_text:
                    current_price = float(price_text.replace("$", "").strip())

                    if settings["last_price"] is None or abs(current_price - settings["last_price"]) >= threshold:
                        settings["last_price"] = current_price
                        screenshot = await page.screenshot()
                        await context.bot.send_photo(
                            chat_id=CHANNEL_ID,
                            photo=screenshot,
                            caption=f"{symbol} - السعر: ${current_price:.2f}"
                        )
                await asyncio.sleep(10)  # كل 10 ثواني
            except Exception as e:
                logging.error(f"خطأ أثناء المراقبة: {e}")
                await asyncio.sleep(10)

# إعداد التطبيق
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, set_input))
    keep_alive()
    app.run_polling()

# التبديل بين استقبال العقد والعتبة
async def set_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not settings.get("symbol"):
        await set_contract(update, context)
    else:
        await set_threshold(update, context)

if __name__ == "__main__":
    main()
