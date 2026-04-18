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
from db import init_db, insert_exam, get_exams
from db import init_db, insert_exam
DEPARTMENTS = [
    "علوم الحاسوب",
    "تقانة المعلومات",
    "الإحصاء",
    "الرياضيات",
    "الحاسوب والرياضيات",
    "الحاسوب والإحصاء",
]
# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")
RENDER_URL = os.getenv("RENDER_URL")

if not TOKEN:
    raise ValueError("TOKEN is not set in environment variables")

if not RENDER_URL:
    raise ValueError("RENDER_URL is not set in environment variables")

ADMIN_IDS = os.getenv("ADMIN_IDS", "")

# تحويل النص إلى list أرقام
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS.split(",") if x.strip()]


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("📥 رفع امتحان", callback_data="upload")],
        [InlineKeyboardButton("📂 تصفح الامتحانات", callback_data="browse")],
    ]

    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🧑‍💻 لوحة التحكم", callback_data="admin")])

    await update.message.reply_text(
        "مرحباً بطالب سكول العزيز 🌟\n"
        "نسأل الله لك دوام التوفيق 🤲\n\n"
        "اختر ما يناسبك:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
# ---------------- BUTTONS ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # ---------------- رفع امتحان ----------------
    if query.data == "upload":
        years = [
            [InlineKeyboardButton(f"المستوى {i}", callback_data=f"year_{i}")]
            for i in range(1, 6)
        ]

        await query.edit_message_text(
            "📘 اختر المستوى:",
            reply_markup=InlineKeyboardMarkup(years),
        )

    elif query.data.startswith("year_"):
        year = query.data.split("_")[1]
        context.user_data["year"] = year

        departments = [
            [InlineKeyboardButton(name, callback_data=f"dep_{i}")]
            for i, name in enumerate(DEPARTMENTS)
        ]

        await query.edit_message_text(
            "🏛️ اختر القسم:",
            reply_markup=InlineKeyboardMarkup(departments),
        )

    elif query.data.startswith("dep_"):
        dep_index = int(query.data.split("_")[1])
        context.user_data["department"] = DEPARTMENTS[dep_index]

        await query.edit_message_text(
            "📎 أرسل الملف الآن"
        )

    # ---------------- التصفح ----------------
    elif query.data == "browse":
        years = [
            [InlineKeyboardButton(f"المستوى {i}", callback_data=f"browse_year_{i}")]
            for i in range(1, 6)
        ]

        await query.edit_message_text(
            "📘 اختر المستوى:",
            reply_markup=InlineKeyboardMarkup(years),
        )

    elif query.data.startswith("browse_year_"):
        year = query.data.split("_")[2]
        context.user_data["browse_year"] = year

        departments = [
            [InlineKeyboardButton(name, callback_data=f"browse_dep_{i}")]
            for i, name in enumerate(DEPARTMENTS)
        ]

        await query.edit_message_text(
            "🏛️ اختر القسم:",
            reply_markup=InlineKeyboardMarkup(departments),
        )

    elif query.data.startswith("browse_dep_"):
        dep_index = int(query.data.split("_")[2])
        year = context.user_data.get("browse_year")
        department = DEPARTMENTS[dep_index]

        exams = get_exams(year, department)

        if not exams:
            await query.edit_message_text("❌ لا توجد امتحانات هنا")
            return

        buttons = [
            [InlineKeyboardButton(subject, callback_data=f"exam_{exam_id}")]
            for exam_id, subject, _ in exams
        ]

        context.user_data["exams"] = {str(e[0]): e for e in exams}

        await query.edit_message_text(
            "📚 اختر المادة:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif query.data.startswith("exam_"):
        exam_id = query.data.split("_")[1]
        exams = context.user_data.get("exams", {})

        if exam_id not in exams:
            await query.answer("❌ خطأ")
            return

        _, subject, file_id = exams[exam_id]

        await query.message.reply_document(file_id, caption=f"📚 {subject}")

    elif query.data == "admin":
        user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.answer("❌ غير مصرح", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton("📋 عرض الامتحانات", callback_data="admin_list")],
        [InlineKeyboardButton("🔎 فلترة حسب السنة", callback_data="admin_filter_year")],
    ]

    await query.edit_message_text(
        "🧑‍💻 لوحة التحكم:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

     elif query.data.startswith("admin_exam_"):
         exam_id = query.data.split("_")[2]
         exams = context.user_data.get("admin_exams", {})

         if exam_id not in exams:
            await query.answer("❌ خطأ")
            return

         exam = exams[exam_id]

         keyboard = [
            [InlineKeyboardButton("✏️ تعديل المادة", callback_data=f"edit_{exam_id}")],
            [InlineKeyboardButton("❌ حذف", callback_data=f"delete_{exam_id}")],
        ]

    await query.edit_message_text(
        f"📘 المستوى: {exam[1]}\n"
        f"🏛️ القسم: {exam[2]}\n"
        f"📚 المادة: {exam[3]}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    elif query.data.startswith("delete_"):
        exam_id = query.data.split("_")[1]

        keyboard = [
            [InlineKeyboardButton("✅ نعم", callback_data=f"confirm_delete_{exam_id}")],
            [InlineKeyboardButton("❌ لا", callback_data="admin_list")],
        ]

        await query.edit_message_text(
            "⚠️ هل أنت متأكد من الحذف؟",
            reply_markup=InlineKeyboardMarkup(keyboard),
    )


    elif query.data.startswith("confirm_delete_"):
        exam_id = query.data.split("_")[2]

        delete_exam(exam_id)

        await query.edit_message_text("✅ تم حذف الامتحان بنجاح")
    
    elif query.data.startswith("edit_"):
        exam_id = query.data.split("_")[1]

        context.user_data["edit_exam_id"] = exam_id

        await query.edit_message_text("✏️ أرسل الاسم الجديد للمادة:")
# ---------------- FILE HANDLER ----------------
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # لازم المستخدم يبدأ رفع
    if "year" not in context.user_data:
        return
    # ---------------- تعديل المادة ----------------
    if "edit_exam_id" in context.user_data and update.message.text:
        exam_id = context.user_data["edit_exam_id"]
        new_subject = update.message.text

        update_exam_subject(exam_id, new_subject)

        context.user_data.pop("edit_exam_id", None)

        await update.message.reply_text("✅ تم تعديل اسم المادة")
        return
    # ---------------- استلام الملف ----------------
    if "pending_file" not in context.user_data:

        if update.message.document:
            file = update.message.document
        elif update.message.photo:
            file = update.message.photo[-1]
        else:
            await update.message.reply_text("❌ أرسل ملف أولاً")
            return

        context.user_data["pending_file"] = file.file_id

        await update.message.reply_text("📚 الآن اكتب اسم المادة:")
        return

    # ---------------- استلام اسم المادة ----------------
    if update.message.text:

        file_id = context.user_data["pending_file"]
        subject = update.message.text

        year = context.user_data.get("year")
        dep = context.user_data.get("department")

        insert_exam(year, dep, subject, file_id)

        # تنظيف الحالة
        context.user_data.pop("pending_file", None)

        await update.message.reply_text(
            "✅ تم حفظ الامتحان بنجاح 🎉\n\n"
            f"📘 المستوى: {year}\n"
            f"🏛️ القسم: {dep}\n"
            f"📚 المادة: {subject}"
        )

        return
# ---------------- MAIN ----------------
def main():
    init_db()

    print("🚀 Bot is running...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(
    (filters.Document.ALL | filters.PHOTO | filters.TEXT) & ~filters.COMMAND,
    handle_file
))

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
