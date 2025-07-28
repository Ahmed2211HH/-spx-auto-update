import json
import asyncio
import pytz
import datetime
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# ======== الإعدادات ========
BOT_TOKEN = '8108628414:AAFhN_p4645YegdMvGGi6ZlEgj1pmqEClsE'
GROUP_ID = -1002789810612
OWNER_ID = 7123756100
TIMEZONE = pytz.timezone('Asia/Riyadh')
SCHEDULE_FILE = 'schedule.json'

DAY, TIME, MESSAGE = range(3)

def convert_day(day_name):
    day_map = {
        "sunday": "sun", "monday": "mon", "tuesday": "tue",
        "wednesday": "wed", "thursday": "thu", "friday": "fri", "saturday": "sat"
    }
    return day_map.get(day_name.lower(), day_name)

def load_schedule():
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_schedule(schedule):
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f)

async def send_scheduled_message(bot: Bot, message: str):
    await bot.send_message(chat_id=GROUP_ID, text=message)

def schedule_all_messages(application):
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    application.bot_data['scheduler'] = scheduler
    bot = application.bot
    schedule = load_schedule()

    for item in schedule:
        trigger = CronTrigger(
            day_of_week=convert_day(item['day']),
            hour=item['hour'],
            minute=item['minute'],
            timezone=TIMEZONE
        )
        scheduler.add_job(
            lambda msg=item['message']: asyncio.run(send_scheduled_message(bot, msg)),
            trigger
        )

    scheduler.start()

# ======== أوامر إدارية ========
async def list_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    schedule = load_schedule()
    if not schedule:
        await update.message.reply_text("لا توجد رسائل مجدولة حالياً.")
        return
    msg = "📅 الرسائل المجدولة:\n"
    for i, item in enumerate(schedule, 1):
        msg += f"{i}. {item['day'].capitalize()} - {item['hour']:02d}:{item['minute']:02d} - {item['message']}\n"
    await update.message.reply_text(msg)

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    schedule = load_schedule()
    if not schedule:
        await update.message.reply_text("لا توجد رسائل لحذفها.")
        return
    msg = "❌ اختر رقم الرسالة لحذفها:\n"
    for i, item in enumerate(schedule, 1):
        msg += f"{i}. {item['day'].capitalize()} - {item['hour']:02d}:{item['minute']:02d} - {item['message']}\n"
    await update.message.reply_text(msg)
    context.user_data['delete_mode'] = True

async def handle_delete_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('delete_mode') and update.effective_user.id == OWNER_ID:
        try:
            index = int(update.message.text) - 1
            schedule = load_schedule()
            if 0 <= index < len(schedule):
                removed = schedule.pop(index)
                save_schedule(schedule)
                await update.message.reply_text(f"✅ تم حذف الرسالة: {removed['message']}")
            else:
                await update.message.reply_text("❌ رقم غير صالح.")
        except:
            await update.message.reply_text("❌ أدخل رقم فقط.")
        context.user_data['delete_mode'] = False

# ======== محادثة الإضافة ========
async def add_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("📆 أدخل الأيام مفصولة بفواصل (مثال: monday,wednesday,friday):")
    return DAY

async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    days = [d.strip().lower() for d in update.message.text.split(',') if d.strip()]
    valid = {"sunday","monday","tuesday","wednesday","thursday","friday","saturday"}
    invalid_days = [d for d in days if d not in valid]
    if invalid_days or not days:
        await update.message.reply_text("❌ أيام غير صحيحة. أعد المحاولة بصيغة مثل: monday,thursday")
        return DAY
    context.user_data['days'] = days
    await update.message.reply_text("⏰ أدخل الوقت بصيغة 24 ساعة HH:MM (مثلاً 14:30):")
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hour, minute = map(int, update.message.text.strip().split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        context.user_data['hour'] = hour
        context.user_data['minute'] = minute
        await update.message.reply_text("📝 أرسل نص الرسالة التي ستتكرر في هذه الأيام:")
        return MESSAGE
    except:
        await update.message.reply_text("❌ صيغة الوقت غير صحيحة. أعد المحاولة (HH:MM).")
        return TIME

async def get_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    schedule = load_schedule()
    for day in context.user_data['days']:
        schedule.append({
            "day": day,
            "hour": context.user_data['hour'],
            "minute": context.user_data['minute'],
            "message": message_text
        })
    save_schedule(schedule)
    await update.message.reply_text("✅ تم إضافة الرسالة لهذه الأيام بنجاح.")
    app = context.application
    scheduler: BackgroundScheduler = app.bot_data.get('scheduler')
    if scheduler:
        scheduler.shutdown(wait=False)
    schedule_all_messages(app)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END

# ======== أدوات مساعدة ========
async def test_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await context.bot.send_message(chat_id=GROUP_ID, text="✅ اختبار: البوت يرسل للقروب بنجاح.")

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        now = datetime.datetime.now(TIMEZONE)
        formatted_time = now.strftime("%A %H:%M:%S")
        await update.message.reply_text(f"🕒 توقيت البوت الآن:\n{formatted_time}")

async def say_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    text = ' '.join(context.args)
    if text:
        await context.bot.send_message(chat_id=GROUP_ID, text=text)
        await update.message.reply_text("✅ تم إرسال الرسالة النصية للقروب.")
    else:
        await update.message.reply_text("❌ استخدم:\n/say نص الرسالة")

async def send_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("📸 أرسل الآن الصورة التي تريد إرسالها إلى القروب مع التعليق (اختياري).")
    context.user_data['awaiting_photo'] = True

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if context.user_data.get('awaiting_photo'):
        photo = update.message.photo[-1]
        caption = update.message.caption or ''
        await context.bot.send_photo(chat_id=GROUP_ID, photo=photo.file_id, caption=caption)
        await update.message.reply_text("✅ تم إرسال الصورة إلى القروب.")
        context.user_data['awaiting_photo'] = False

# ======== التشغيل ========
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    schedule_all_messages(app)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_message)],
        states={
            DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_day)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("list", list_messages))
    app.add_handler(CommandHandler("delete", delete_message))
    app.add_handler(CommandHandler("testsend", test_send))
    app.add_handler(CommandHandler("time", show_time))
    app.add_handler(CommandHandler("say", say_to_group))
    app.add_handler(CommandHandler("sendphoto", send_photo_command))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_choice))

    await app.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
