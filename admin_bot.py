import os
import logging
import random
import re
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from database import *

load_dotenv()

# ========== CONFIG ==========
BOT_TOKEN = os.getenv('ADMIN_BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
BOT_USERNAME = os.getenv('ADMIN_BOT_USERNAME')
PAYMENT_AMOUNT = int(os.getenv('PAYMENT_AMOUNT', 100))

# ========== STATES ==========
ADMIN_ADD_BOT, ADMIN_LOGIN_OTP = range(2)

# ========== LOGGING ==========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized! Admin only.")
        return
    
    await show_admin_panel(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update) and update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query
    else:
        message = update.message
    
    accounts = db_get_all_accounts()
    payments = db_get_pending_payments()
    
    total_users = len(accounts)
    can_clone = sum(1 for acc in accounts if acc[2] == 1)
    
    keyboard = [
        [InlineKeyboardButton(f"👤 Users: {total_users}", callback_data="admin_stats")],
        [InlineKeyboardButton(f"🤖 Can Clone: {can_clone}", callback_data="admin_stats")],
        [InlineKeyboardButton(f"⏳ Payments: {len(payments)}", callback_data="admin_payments")],
        [InlineKeyboardButton("🔐 Login Any Account", callback_data="admin_login")],
        [InlineKeyboardButton("✅ Approve Payments", callback_data="admin_approve")],
        [InlineKeyboardButton("🤖 Add Clone Bot", callback_data="admin_add_bot")],
        [InlineKeyboardButton("📊 DM History", callback_data="admin_history")],
        [InlineKeyboardButton("📋 All Users", callback_data="admin_users")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔐 *Admin Panel*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *Statistics:*\n"
        f"👤 Total Users: {total_users}\n"
        f"🤖 Can Clone: {can_clone}\n"
        f"⏳ Pending Payments: {len(payments)}\n"
        f"💰 Amount: ₹{PAYMENT_AMOUNT}\n\n"
        f"🔽 *Actions:*"
    )
    
    if isinstance(message, update.callback_query):
        await message.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ========== VIEW PAYMENTS ==========
async def view_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    payments = db_get_pending_payments()
    
    if not payments:
        await query.edit_message_text("✅ No pending payments!", parse_mode="Markdown")
        return
    
    text = f"📤 *Pending Payments (₹{PAYMENT_AMOUNT})*\n\n"
    for p in payments[:10]:
        text += f"🆔 {p[0]} | 👤 `{p[1]}` | ₹{p[2]} | UTR: `{p[3]}`\n"
        text += f"📅 {p[4][:10]}\n━━━━━━━━━━━━━━\n"
    
    keyboard = [
        [InlineKeyboardButton("✅ Approve First", callback_data="admin_approve_one")],
        [InlineKeyboardButton("✅ Approve All", callback_data="admin_approve_all")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ========== APPROVE PAYMENT ==========
async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    payments = db_get_pending_payments()
    
    if not payments:
        await query.edit_message_text("✅ No pending payments!", parse_mode="Markdown")
        return
    
    payment_id = payments[0][0]
    user_id = db_approve_payment(payment_id)
    
    try:
        await query.get_bot().send_message(
            chat_id=user_id,
            text=f"🎉 *Clone Access Approved!*\n\n"
                 f"✅ Payment of ₹{PAYMENT_AMOUNT} approved!\n"
                 f"🤖 Now clone your bot at @CloneBot",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await query.edit_message_text(
        f"✅ *Payment Approved!*\n\n"
        f"👤 User: `{user_id}`\n"
        f"🤖 Clone Access Granted!",
        parse_mode="Markdown"
    )

# ========== APPROVE ALL ==========
async def approve_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    payments = db_get_pending_payments()
    
    if not payments:
        await query.edit_message_text("✅ No pending payments!", parse_mode="Markdown")
        return
    
    for p in payments:
        user_id = db_approve_payment(p[0])
        try:
            await query.get_bot().send_message(
                chat_id=user_id,
                text=f"🎉 *Clone Access Approved!*\n\n✅ Payment approved!\n🤖 Clone your bot now!",
                parse_mode="Markdown"
            )
        except:
            pass
    
    await query.edit_message_text(
        f"✅ *All Payments Approved!*\n\nTotal: {len(payments)} users got clone access!",
        parse_mode="Markdown"
    )

# ========== ADD CLONE BOT ==========
async def add_clone_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🤖 *Add Clone Bot*\n\n"
        "Bot Token bhejein:\n"
        "Format: `123456:ABC-DEF`\n\n"
        "📌 BotFather se token lo",
        parse_mode="Markdown"
    )
    return ADMIN_ADD_BOT

async def add_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    
    bot_token = update.message.text.strip()
    
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', bot_token):
        await update.message.reply_text("❌ Invalid token! Format: `123456:ABC-DEF`", parse_mode="Markdown")
        return ADMIN_ADD_BOT
    
    bot_username = f"@clone_{random.randint(1000,9999)}"
    db_add_available_bot(bot_token, bot_username)
    
    await update.message.reply_text(
        f"✅ *Bot Added!*\n\n"
        f"🔑 Token: `{bot_token}`\n"
        f"📱 Username: {bot_username}\n\n"
        f"📌 Available for cloning!",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ========== LOGIN ANY ACCOUNT ==========
async def login_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    accounts = db_get_all_accounts()
    
    if not accounts:
        await query.edit_message_text("❌ No accounts!", parse_mode="Markdown")
        return
    
    keyboard = []
    for acc in accounts[:20]:
        user_id, phone, can_clone = acc
        keyboard.append([
            InlineKeyboardButton(
                f"{phone} {'🤖' if can_clone else '🆓'}",
                callback_data=f"admin_login_{user_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔐 *Select Account*\n\nClick to login as user:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def login_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    
    query = update.callback_query
    await query.answer()
    
    target_user_id = int(query.data.split("_")[2])
    otp = str(random.randint(100000, 999999))
    
    context.user_data['admin_login_otp'] = otp
    context.user_data['admin_login_target'] = target_user_id
    
    await query.edit_message_text(
        f"🔐 *Login OTP*\n\n"
        f"👤 Target User: `{target_user_id}`\n"
        f"🔢 OTP: `{otp}`\n\n"
        f"⬇️ OTP daalein:",
        parse_mode="Markdown"
    )
    return ADMIN_LOGIN_OTP

async def verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    
    entered_otp = update.message.text.strip()
    stored_otp = context.user_data.get('admin_login_otp')
    target_user = context.user_data.get('admin_login_target')
    
    if entered_otp == stored_otp:
        account = db_get_account(target_user)
        
        await update.message.reply_text(
            f"✅ *Logged in as User {target_user}*\n\n"
            f"📱 Phone: {account[2]}\n"
            f"🤖 Clone Access: {'Yes' if account[5] == 1 else 'No'}",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Wrong OTP! Dubara daalein:", parse_mode="Markdown")
        return ADMIN_LOGIN_OTP

# ========== ALL USERS ==========
async def all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    accounts = db_get_all_accounts()
    
    text = "👥 *All Users*\n\n"
    for i, acc in enumerate(accounts[:50], 1):
        text += f"{i}. `{acc[0]}` | {acc[1]} | {'🤖 Clone' if acc[2] else '🆓 Free'}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ========== ADMIN BACK ==========
async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_admin_panel(update, context)

# ========== CONVERSATION ==========
conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(add_clone_bot, pattern="^admin_add_bot$"),
        CallbackQueryHandler(login_otp, pattern="^admin_login_"),
    ],
    states={
        ADMIN_ADD_BOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bot_handler)],
        ADMIN_LOGIN_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_otp)],
    },
    fallbacks=[CommandHandler("start", start)]
)

# ========== MAIN ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv_handler)
    
    print(f"✅ Admin Bot Running: {BOT_USERNAME}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "admin_payments":
        await view_payments(update, context)
    elif data == "admin_approve":
        await approve_payment(update, context)
    elif data == "admin_approve_all":
        await approve_all(update, context)
    elif data == "admin_approve_one":
        await approve_payment(update, context)
    elif data == "admin_login":
        await login_account(update, context)
    elif data == "admin_users":
        await all_users(update, context)
    elif data == "admin_back":
        await admin_back(update, context)
    elif data == "admin_stats":
        await query.edit_message_text("📊 Stats updated!", parse_mode="Markdown")
    elif data == "admin_history":
        await query.edit_message_text("📊 DM History view karein!", parse_mode="Markdown")

if __name__ == "__main__":
    main()
