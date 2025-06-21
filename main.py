import os
import logging
import time
import requests
from telegram import Bot, Update
from telegram.ext import CommandHandler, Updater, CallbackContext
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image

# إعدادات التوكن والقناة
TOKEN = '7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg'
CHANNEL_ID = '-1002247064978'
OWNER_ID = 7123756100  # عدل هذا إذا تغير

# متغيرات تخزين الرابط والخطوة الحالية والسعر الأخير
CONTRACT_LINK = ''
STEP = 1.0
LAST_PRICE = 0.0

# تهيئة البوت
bot = Bot(TOKEN)
updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

def start(update: Update, context: CallbackContext):
    if update.effective_user.id == OWNER_ID:
        update.message.reply_text("أهلًا بك، أرسل /set_contract <الرابط> لتحديد العقد.")
    else:
        update.message.reply_text("غير مصرح لك باستخدام هذا البوت.")

def set_contract(update: Update, context: CallbackContext):
    global CONTRACT_LINK
    if update.effective_user.id == OWNER_ID:
        if context.args:
            CONTRACT_LINK = context.args[0]
            update.message.reply_text(f"✅ تم تعيين العقد:
{CONTRACT_LINK}")
        else:
            update.message.reply_text("❌ أرسل الرابط بعد الأمر مثل:
/set_contract https://www.webull.com/quote/...")
    else:
        update.message.reply_text("❌ غير مصرح.")

def set_step(update: Update, context: CallbackContext):
    global STEP
    if update.effective_user.id == OWNER_ID:
        try:
            STEP = float(context.args[0])
            update.message.reply_text(f"✅ تم تحديد التحديث كل {STEP}$")
        except:
            update.message.reply_text("❌ أرسل رقم صحيح مثل:
/set_step 1.0")
    else:
        update.message.reply_text("❌ غير مصرح.")

def get_contract_price():
    try:
        return round(LAST_PRICE + STEP, 2)  # مؤقتاً كل مرة يرتفع
    except:
        return 0.0

def take_screenshot(link):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1200, 900)
    driver.get(link)
    time.sleep(3)
    driver.save_screenshot("screenshot.png")
    driver.quit()

    image = Image.open("screenshot.png")
    cropped = image.crop((100, 200, 1100, 700))
    cropped.save("contract.png")

def monitor_loop():
    global LAST_PRICE
    while True:
        if CONTRACT_LINK:
            current_price = get_contract_price()
            if current_price - LAST_PRICE >= STEP:
                LAST_PRICE = current_price
                take_screenshot(CONTRACT_LINK)
                bot.send_photo(chat_id=CHANNEL_ID, photo=open("contract.png", "rb"), caption=f"📈 السعر الجديد: {LAST_PRICE}$")
        time.sleep(30)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("set_contract", set_contract))
dispatcher.add_handler(CommandHandler("set_step", set_step))

updater.start_polling()
import threading
threading.Thread(target=monitor_loop).start()
