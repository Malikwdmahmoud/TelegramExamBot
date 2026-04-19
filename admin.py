from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from db import get_all_exams, delete_exam, update_exam_subject

import os

# قراءة الأدمن من env
ADMIN_IDS = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS.split(",") if x.strip().isdigit()]


def is_admin(user_id):
    return user_id in ADMIN_IDS


# ---------------- لوحة التحكم ----------------
async def admin_panel(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    if not is_admin(user_id):
        await query.answer("❌ غير مصرح", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton("📋 عرض الامتحانات", callback_data="admin_list")],
    ]

    await query.edit_message_text(
        "🧑‍💻 لوحة التحكم:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- عرض الامتحانات ----------------
async def admin_list(update, context):
    query = update.callback_query

    exams = get_all_exams()

    if not exams:
        await query.edit_message_text("❌ لا توجد بيانات")
        return

    buttons = [
        [
            InlineKeyboardButton(
                f"{e[1]} | {e[2]} | {e[3]}",
                callback_data=f"admin_exam_{e[0]}"
            )
        ]
        for e in exams[:20]
    ]

    context.user_data["admin_exams"] = {str(e[0]): e for e in exams}

    await query.edit_message_text(
        "📋 اختر امتحان:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ---------------- تفاصيل الامتحان ----------------
async def admin_exam(update, context):
    query = update.callback_query
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


# ---------------- تأكيد الحذف ----------------
async def delete_confirm(update, context):
    query = update.callback_query
    exam_id = query.data.split("_")[1]

    keyboard = [
        [InlineKeyboardButton("✅ نعم", callback_data=f"confirm_delete_{exam_id}")],
        [InlineKeyboardButton("❌ لا", callback_data="admin_list")],
    ]

    await query.edit_message_text(
        "⚠️ هل أنت متأكد من الحذف؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def delete_final(update, context):
    query = update.callback_query
    exam_id = query.data.split("_")[2]

    delete_exam(exam_id)

    await query.edit_message_text("✅ تم حذف الامتحان")


# ---------------- تعديل المادة ----------------
async def edit_start(update, context):
    query = update.callback_query
    exam_id = query.data.split("_")[1]

    context.user_data["edit_exam_id"] = exam_id

    await query.edit_message_text("✏️ أرسل الاسم الجديد للمادة:")


async def edit_save(update, context):
    if "edit_exam_id" not in context.user_data:
        return

    exam_id = context.user_data["edit_exam_id"]
    new_subject = update.message.text

    update_exam_subject(exam_id, new_subject)

    context.user_data.pop("edit_exam_id", None)

    await update.message.reply_text("✅ تم تعديل اسم المادة")