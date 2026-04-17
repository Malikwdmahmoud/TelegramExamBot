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

from db import (
    init_db,
    insert_exam,
    get_years,
    get_departments,
    get_subjects,
    get_exams,
)

TOKEN = os.getenv("TOKEN")


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 رفع امتحان", callback_data="upload")],
        [InlineKeyboardButton("📂 تصفح الامتحانات", callback_data="browse")],
    ]

    await update.message.reply_text(
        "أهلاً 👋 اختر:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- BUTTONS ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # رفع امتحان
    if query.data == "upload":
        years = [
            [InlineKeyboardButton(f"السنة {i}", callback_data=f"year_{i}")]
            for i in range(1, 6)
        ]

        await query.edit_message_text(
            "📘 اختر السنة:",
            reply_markup=InlineKeyboardMarkup(years),
        )

    # اختيار السنة (رفع)
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

    # اختيار القسم (رفع)
    elif query.data.startswith("dep_"):
        dep = query.data.split("_")[1]
        context.user_data["department"] = dep

        await query.edit_message_text(
            "📎 الآن أرسل الملف + اكتب اسم المادة في الوصف (caption)"
        )

    # ---------------- BROWSE ----------------
    elif query.data == "browse":
        years = get_years()

        if not years:
            await query.edit_message_text("لا توجد امتحانات حالياً ❌")
            return

        keyboard = [
            [InlineKeyboardButton(f"السنة {y}", callback_data=f"b_year_{y}")]
            for y in years
        ]

        await query.edit_message_text(
            "📚 اختر السنة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # اختيار السنة (تصفح)
    elif query.data.startswith("b_year_"):
        year = query.data.replace("b_year_", "")
        context.user_data["b_year"] = year

        deps = get_departments(year)

        keyboard = [
            [InlineKeyboardButton(d, callback_data=f"b_dep_{d}")]
            for d in deps
        ]

        await query.edit_message_text(
            "🏛️ اختر القسم:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # اختيار القسم (تصفح)
    elif query.data.startswith("b_dep_"):
        dep = query.data.replace("b_dep_", "")
        year = context.user_data.get("b_year")

        context.user_data["b_dep"] = dep

        subjects = get_subjects(year, dep)

        keyboard = [
            [InlineKeyboardButton(s, callback_data=f"b_sub_{s}")]
            for s in subjects
        ]

        await query.edit_message_text(
            "📖 اختر المادة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # عرض الامتحانات
    elif query.data.startswith("b_sub_"):
        subject = query.data.replace("b_sub_", "")
        year = context.user_data.get("b_year")
        dep = context.user_data.get("b_dep")

        exams = get_exams(year, dep, subject)

        if not exams:
            await query.edit_message_text("لا توجد امتحانات ❌")
            return

        await query.edit_message_text("📤 جاري إرسال الامتحانات...")

        for file_id in exams:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=file_id,
                caption=f"📚 {subject} - السنة {year} - قسم {dep}",
            )


# ---------------- FILE HANDLER ----------------
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "year" not in context.user_data:
        await update.message.reply_text("ابدأ من /start أولاً 👈")
        return

    file = update.message.document or update.message.photo[-1]
    file_id = file.file_id

    year = context.user_data.get("year")
    department = context.user_data.get("department", "unknown")
    subject = update.message.caption or "unknown"

    insert_exam(year, department, subject, file_id)

    await update.message.reply_text(
        "تم الحفظ في قاعدة البيانات ✅\n\n"
        f"📘 السنة: {year}\n"
        f"🏛️ القسم: {department}\n"
        f"📚 المادة: {subject}"
    )


# ---------------- MAIN ----------------
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
