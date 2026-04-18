import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from db import init_db, insert_exam

# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")
RENDER_URL = os.getenv("RENDER_URL")

if not TOKEN:
    raise ValueError("TOKEN is not set in environment variables")

if not RENDER_URL:
    raise ValueError("RENDER_URL is not set in environment variables")


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 رفع امتحان", callback_data="upload")],
    ]

    await update.message.reply_text(
        "أهلاً 👋 اختر العملية:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- BUTTONS ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # اختيار رفع امتحان
    if query.data == "upload":
        years = [
            [InlineKeyboardButton(f"المستوى {i}", callback_data=f"year_{i}")]
            for i in range(1, 6)
        ]

        await query.edit_message_text(
            "📘 اختر المستوى:",
            reply_markup=InlineKeyboardMarkup(years),
        )

    # اختيار السنة
    elif query.data.startswith("year_"):
        year = query.data.split("_")[1]
        context.user_data["year"] = year

        departments = [
            [InlineKeyboardButton(f"قسم {i}", callback_data=f"dep_{i}")]
            for i in range(1, 7)
        ]

        await query.edit_message_text(
            "🏛️ اختر القسم:",
            reply_markup=InlineKeyboardMarkup(departments),
        )

    # اختيار القسم
    elif query.data.startswith("dep_"):
        dep = query.data.split("_")[1]
        context.user_data["department"] = dep

        await query.edit_message_text(
            "📎 أرسل الملف الآن + اكتب اسم المادة في الوصف (caption)"
        )


# ---------------- FILE HANDLER ----------------
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "year" not in context.user_data:
        await update.message.reply_text("ابدأ من /start 👈")
        return

    # حماية من الأخطاء
    if update.message.document:
        file = update.message.document
    elif update.message.photo:
        file = update.message.photo[-1]
    else:
        await update.message.reply_text("❌ أرسل ملف أو صورة فقط")
        return

    file_id = file.file_id

    year = context.user_data.get("year")
    dep = context.user_data.get("department", "unknown")
    subject = update.message.caption or "unknown"

    insert_exam(year, dep, subject, file_id)

    await update.message.reply_text(
        "✅ تم الحفظ بنجاح\n\n"
        f"📘 المستوى: {year}\n"
        f"🏛️ القسم: {dep}\n"
        f"📚 المادة: {subject}"
    )


# ---------------- MAIN ----------------
def main():
    init_db()

    print("🚀 Bot is running...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))

    # 🔥 Webhook (Render)
    PORT = int(os.environ.get("PORT", 10000))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{RENDER_URL}/{TOKEN}",
    )


if __name__ == "__main__":
    main()
