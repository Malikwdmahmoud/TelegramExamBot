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

TOKEN = os.getenv("TOKEN")


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 رفع امتحان", callback_data="upload")],
    ]

    await update.message.reply_text(
        "أهلاً 👋 اختر:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- BUTTONS ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "upload":
        years = [
            [InlineKeyboardButton(f"السنة {i}", callback_data=f"year_{i}")]
            for i in range(1, 6)
        ]

        await query.edit_message_text(
            "📘 اختر السنة:",
            reply_markup=InlineKeyboardMarkup(years),
        )

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

    elif query.data.startswith("dep_"):
        dep = query.data.split("_")[1]
        context.user_data["department"] = dep

        await query.edit_message_text(
            "📎 أرسل الملف الآن + اكتب اسم المادة في caption"
        )


# ---------------- FILE HANDLER ----------------
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "year" not in context.user_data:
        await update.message.reply_text("ابدأ من /start 👈")
        return

    file = update.message.document or update.message.photo[-1]
    file_id = file.file_id

    year = context.user_data.get("year")
    dep = context.user_data.get("department", "unknown")
    subject = update.message.caption or "unknown"

    insert_exam(year, dep, subject, file_id)

    await update.message.reply_text(
        "✅ تم الحفظ بنجاح\n"
        f"📘 السنة: {year}\n"
        f"🏛️ القسم: {dep}\n"
        f"📚 المادة: {subject}"
    )


# ---------------- WEBHOOK APP ----------------
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))

    # 🔥 Webhook setup (Render compatible)
    PORT = int(os.environ.get("PORT", 10000))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://telegramexambot.onrender.com/{TOKEN}",
    )


if __name__ == "__main__":
    main()
