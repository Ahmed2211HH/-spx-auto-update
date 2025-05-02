import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from playwright.async_api import async_playwright

# إعدادات البوت
TOKEN = '7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg'
OWNER_ID = 7123756100
CHANNEL_ID = -1002529600259

# تخزين بيانات العقد والمتابعة
contract_url = ""
refresh_interval = 2  # عدد الثواني بين كل تحديث

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    keyboard = [
        [InlineKeyboardButton("اختيار رابط العقد", callback_data="set_contract")],
        [InlineKeyboardButton("بدء التحديث", callback_data="start_monitoring")],
        [InlineKeyboardButton("إيقاف التحديث", callback_data="stop_monitoring")]
    ]
    await update.message.reply_text("مرحبًا! تحكم بالبوت من الأزرار:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != OWNER_ID:
        return
    if query.data == "set_contract":
        await query.edit_message_text("أرسل رابط العقد من Webull:")
        return 1
    elif query.data == "start_monitoring":
        if not contract_url:
            await query.edit_message_text("❌ لم يتم تحديد رابط العقد بعد.")
            return
        await query.edit_message_text("✅ تم بدء التحديث التلقائي...")
        context.bot_data["monitoring"] = True
        asyncio.create_task(start_monitoring(context))
    elif query.data == "stop_monitoring":
        context.bot_data["monitoring"] = False
        await query.edit_message_text("⛔ تم إيقاف التحديث.")
    return -1

async def receive_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global contract_url
    contract_url = update.message.text.strip()
    await update.message.reply_text("✅ تم حفظ رابط العقد.")
    return -1

async def start_monitoring(context):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        await page.goto(contract_url)
        await page.wait_for_timeout(3000)
        while context.bot_data.get("monitoring", False):
            try:
                await page.reload()
                await page.wait_for_timeout(1000)
                image_path = "contract.png"
                await page.screenshot(path=image_path)
                with open(image_path, "rb") as photo:
                    await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo)
            except Exception as e:
                print("خطأ أثناء التحديث:", e)
            await asyncio.sleep(refresh_interval)
        await browser.close()

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(user_id=OWNER_ID), receive_contract))
    app.run_polling()

if __name__ == "__main__":
    main()
