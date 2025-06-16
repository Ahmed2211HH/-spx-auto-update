import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# إعدادات البوت
TOKEN = "7885914349:AAHFM6qMX_CYOOajGwhczwXl3mnLjqRJIAg"
CHANNEL_ID = -1002624628833

# إعداد السجل
logging.basicConfig(level=logging.INFO)

# دالة توليد الخطة اليومية
def generate_daily_plan():
    current_price = 6016  # عدل هذا الرقم حسب سعر السوق
    call_entry = current_price + 10
    put_entry = current_price - 10

    return f"""📅 الخطة اليومية – تداول SPX
اليوم | الثلاثاء – 17 يونيو 2025

⸻

✅ نقطة دخول Call (شراء صعودي) 📈
{call_entry:.1f} 🟢

• الشرط: ثبات السعر أعلى هذا المستوى على فاصل الساعة
• الأهداف المحتملة 🎯:
 • {call_entry + 10:.1f}
 • {call_entry + 25:.1f}
 • {call_entry + 50:.1f}

📌 الوضع الحالي:
السوق يتداول حاليًا عند {current_price}
نراقب اختراق {call_entry:.1f} والثبات فوقه لتفعيل الدخول الصعودي.

⸻

🔻 نقطة دخول Put (شراء هبوطي) 📉
{put_entry:.1f} 🔴

• الشرط: كسر هذا المستوى والثبات أسفله على فاصل الساعة
• الأهداف المحتملة 🎯:
 • {put_entry - 15:.1f}
 • {put_entry - 30:.1f}
 • {put_entry - 55:.1f}

📌 الوضع الحالي:
لم يتم التفعيل بعد، ونترقب كسر واضح أسفل {put_entry:.1f} لتأكيد الهبوط.

⸻
📿 اذكر الله دائماً.

⸻

⚠️ ملاحظات هامة:
• الالتزام بإدارة رأس المال وعدم الدخول بكامل السيولة
• لا يتم تفعيل أي صفقة إلا بعد تحقق الشروط الفنية بوضوح
• الأهداف إرشادية ولا تعني الوصول الإجباري، تابع السوق بتأنٍ وتعامل بمرونة
"""

# دالة تنفيذ الخطة عند كتابة /plan
async def daily_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = generate_daily_plan()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

# دالة تحليل العقد من الصورة
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 تم استلام صورة العقد! جاري تحليلها...")
    # هنا تقدر تضيف الذكاء الاصطناعي لتحليل العقد إذا أردت

# بدء التشغيل
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا بك في بوت الخطة اليومية! أرسل /plan للحصول على خطة اليوم.")

# تشغيل التطبيق
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", daily_plan))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running...")
    app.run_polling()
