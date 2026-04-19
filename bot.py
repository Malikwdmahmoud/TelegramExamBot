from multiprocessing import context
import os
from telegram import Update
from admin import (
    admin_panel,
    admin_list,
    admin_exam,
    admin_stats,
    delete_confirm,
    delete_final,
    edit_start,
    edit_save,
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from db import get_exams_by_year, init_db, insert_exam, get_exams, search_exams, delete_exam, update_exam_subject
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

valid_ids = []
for x in ADMIN_IDS.split(","):
    x = x.strip()
    if x.isdigit():
        valid_ids.append(int(x))
    else:
        print(f"⚠️ تجاهل قيمة غير صالحة: {x}")

ADMIN_IDS = valid_ids

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("📥 رفع امتحان", callback_data="upload")],
        [InlineKeyboardButton("📂 تصفح الامتحانات", callback_data="browse")],
        [InlineKeyboardButton("🔎 بحث عن امتحان", callback_data="search")],
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
        years.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")])

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
        departments.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")])

        await query.edit_message_text(
            "🏛️ اختر القسم:",
            reply_markup=InlineKeyboardMarkup(departments),
        )

    elif query.data.startswith("dep_"):
        dep_index = int(query.data.split("_")[1])
        context.user_data["department"] = DEPARTMENTS[dep_index]

        await query.edit_message_text(
            "📎 أرسل الملف الآن",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ رجوع", callback_data="back_upload_year")]
            ]),
        )
    elif query.data == "admin_stats":
        await admin_stats(update, context)
    elif query.data == "search":
        context.user_data["search_active"] = True
        await query.edit_message_text(
            "🔎 اكتب اسم المادة أو كلمة مفتاحية للبحث:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")]
            ]),
        )

    elif query.data == "back_start":
        for key in ["year", "department", "pending_file", "browse_year", "search_active", "search_results"]:
            context.user_data.pop(key, None)

        keyboard = [
            [InlineKeyboardButton("📥 رفع امتحان", callback_data="upload")],
            [InlineKeyboardButton("📂 تصفح الامتحانات", callback_data="browse")],
            [InlineKeyboardButton("🔎 بحث عن امتحان", callback_data="search")],
        ]
        if query.from_user.id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("🧑‍💻 لوحة التحكم", callback_data="admin")])

        await query.edit_message_text(
            "مرحباً بطالب سكول العزيز 🌟\n"
            "نسأل الله لك دوام التوفيق 🤲\n\n"
            "اختر ما يناسبك:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "back_upload_year":
        context.user_data.pop("department", None)
        context.user_data.pop("pending_file", None)
        years = [
            [InlineKeyboardButton(f"المستوى {i}", callback_data=f"year_{i}")]
            for i in range(1, 6)
        ]
        years.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")])

        await query.edit_message_text(
            "📘 اختر المستوى:",
            reply_markup=InlineKeyboardMarkup(years),
        )

    elif query.data == "back_upload_dep":
        context.user_data.pop("pending_file", None)
        year = context.user_data.get("year")
        departments = [
            [InlineKeyboardButton(name, callback_data=f"dep_{i}")]
            for i, name in enumerate(DEPARTMENTS)
        ]
        departments.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_upload_year")])

        await query.edit_message_text(
            "🏛️ اختر القسم:",
            reply_markup=InlineKeyboardMarkup(departments),
        )

    elif query.data == "back_browse":
        years = [
            [InlineKeyboardButton(f"المستوى {i}", callback_data=f"browse_year_{i}")]
            for i in range(1, 6)
        ]
        years.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")])

        await query.edit_message_text(
            "📘 اختر المستوى:",
            reply_markup=InlineKeyboardMarkup(years),
        )

    elif query.data == "back_browse_year":
        year = context.user_data.get("browse_year")
        departments = [
            [InlineKeyboardButton(name, callback_data=f"browse_dep_{i}")]
            for i, name in enumerate(DEPARTMENTS)
        ]
        departments.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_browse")])

        await query.edit_message_text(
            "🏛️ اختر القسم:",
            reply_markup=InlineKeyboardMarkup(departments),
        )

    elif query.data == "back_search":
        context.user_data["search_active"] = True
        await query.edit_message_text(
            "🔎 اكتب اسم المادة أو كلمة مفتاحية للبحث:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")]
            ]),
        )

    elif query.data == "back_admin":
        keyboard = [
            [InlineKeyboardButton("📋 عرض الامتحانات", callback_data="admin_list")],
            [InlineKeyboardButton("🔎 فلترة حسب السنة", callback_data="admin_filter_year")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")],
        ]

        await query.edit_message_text(
            "🧑‍💻 لوحة التحكم:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    # ---------------- التصفح ----------------
    elif query.data == "browse":
        years = [
            [InlineKeyboardButton(f"المستوى {i}", callback_data=f"browse_year_{i}")]
            for i in range(1, 6)
        ]
        years.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")])

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
        departments.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_browse")])

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
        buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_browse_year")])

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

        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=file_id,
            caption=f"📚 {subject}"
        )

    elif query.data.startswith("search_exam_"):
        exam_id = query.data.split("_")[2]
        exams = context.user_data.get("search_results", {})

        if exam_id not in exams:
            await query.answer("❌ خطأ")
            return

        _, year, department, subject, file_id = exams[exam_id]
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=file_id,
            caption=f"📚 {subject} \n📘 المستوى: {year} \n🏛️ القسم: {department}"
        )

    elif query.data == "admin":
        user_id = query.from_user.id

        if user_id not in ADMIN_IDS:
            await query.answer("❌ غير مصرح", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton("📋 عرض الامتحانات", callback_data="admin_list")],
            [InlineKeyboardButton("🔎 فلترة حسب السنة", callback_data="admin_filter_year")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")],
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
            [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_list")],
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

        await query.edit_message_text(
            "✏️ أرسل الاسم الجديد للمادة:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"admin_exam_{exam_id}")]
            ]),
        )

    elif query.data == "admin_filter_year":
        keyboard = [
            [InlineKeyboardButton(f"المستوى {i}", callback_data=f"admin_year_{i}")]
            for i in range(1, 6)
        ]
        keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_admin")])

        await query.edit_message_text(
            "📘 اختر السنة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        
    elif query.data.startswith("admin_year_"):
        year = query.data.split("_")[2]

        exams = get_exams_by_year(year)

        if not exams:
            await query.edit_message_text("❌ لا توجد بيانات")
            return

        buttons = [
            [InlineKeyboardButton(f"{e[3]}", callback_data=f"admin_exam_{e[0]}")]
            for e in exams
    ]

        context.user_data["admin_exams"] = {str(e[0]): e for e in exams}

        await query.edit_message_text(  
            f"📘 امتحانات المستوى {year}:",
            reply_markup=InlineKeyboardMarkup(buttons),
    )
# ---------------- FILE HANDLER ----------------
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # admin edit
    await edit_save(update, context)
    # لازم المستخدم يبدأ رفع
    if "search_active" in context.user_data and update.message.text:
        keyword = update.message.text.strip()
        if not keyword:
            await update.message.reply_text("❌ اكتب كلمة بحث صحيحة.")
            return

        exams = search_exams(keyword)
        context.user_data.pop("search_active", None)

        if not exams:
            await update.message.reply_text("❌ لم يتم العثور على نتائج.")
            return

        buttons = [
            [InlineKeyboardButton(f"{year} | {department} | {subject}", callback_data=f"search_exam_{exam_id}")]
            for exam_id, year, department, subject, _ in exams[:20]
        ]

        context.user_data["search_results"] = {str(e[0]): e for e in exams}

        buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_search")])

        await update.message.reply_text(
            "🔎 نتائج البحث:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

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

        await update.message.reply_text(
            "📚 الآن اكتب اسم المادة:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ رجوع", callback_data="back_upload_dep")]
            ]),
        )
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
