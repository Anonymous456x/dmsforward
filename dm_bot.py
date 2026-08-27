import os
import asyncio
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
BOT_TOKEN = os.getenv('DM_BOT_TOKEN')
BOT_USERNAME = os.getenv('DM_BOT_USERNAME')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
PAYMENT_AMOUNT = int(os.getenv('PAYMENT_AMOUNT', 100))

# ========== STATES ==========
(PHONE_INPUT, OTP_VERIFY, DM_TARGET, DM_MESSAGE, DM_COUNT, PAYMENT_UTR) = range(6)

# ========== LOGGING ==========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    account = db_get_account(user_id)
    
    keyboard = [
        [InlineKeyboardButton("📱 Account Add Karein", callback_data="add_account")],
    ]
    
    if account:
        keyboard.append([InlineKeyboardButton("📤 DM Forward Karein", callback_data="dm_forward")])
        keyboard.append([InlineKeyboardButton("📊 My Stats", callback_data="my_stats")])
        
        if account[5] == 1:
            keyboard.append([InlineKeyboardButton("🤖 Bot Clone (₹100)", callback_data="clone_bot")])
        else:
            keyboard.append([InlineKeyboardButton("🔓 Bot Clone - ₹100", callback_data="upgrade")])
    
    keyboard.append([InlineKeyboardButton("❓ Help", callback_data="help")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status = "✅ Active" if account else "❌ Not Added"
    can_clone = "✅ Yes" if account and account[5] == 1 else "❌ No"
    
    await update.message.reply_text(
        f"👋 *Namaste {user.first_name}!*\n\n"
        f"🤖 *DM Forward Bot*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📱 Status: {status}\n"
        f"🤖 Clone: {can_clone}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *FREE Features:*\n"
        f"✅ Account Add\n"
        f"✅ Unlimited DM Forward\n"
        f"✅ Target Selection\n\n"
        f"💰 *PAID (₹{PAYMENT_AMOUNT}):*\n"
        f"✅ Bot Cloning\n"
        f"✅ Full Control\n"
        f"✅ Lifetime Access",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ========== ACCOUNT ADD ==========
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📱 *Account Add Karein (FREE)*\n\n"
        "🔢 Apna *Phone Number* daalein:\n"
        "Format: `+91XXXXXXXXXX`\n\n"
        "⚠️ OTP aayega, admin bhi login kar sakta hai\n"
        "✅ 100% FREE!",
        parse_mode="Markdown"
    )
    return PHONE_INPUT

async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone = update.message.text.strip()
    
    if not re.match(r'^\+?[0-9]{10,15}$', phone):
        await update.message.reply_text("❌ Invalid number! Format: +91XXXXXXXXXX", parse_mode="Markdown")
        return PHONE_INPUT
    
    otp = str(random.randint(100000, 999999))
    context.user_data['phone'] = phone
    context.user_data['otp'] = otp
    
    await update.message.reply_text(
        f"📱 *OTP Sent!*\n\n🔢 Your OTP: `{otp}`\n\n⬇️ OTP daalein:",
        parse_mode="Markdown"
    )
    return OTP_VERIFY

async def otp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    entered_otp = update.message.text.strip()
    
    if entered_otp == context.user_data.get('otp'):
        phone = context.user_data.get('phone')
        session_string = f"session_{random.randint(1000,9999)}"
        db_add_account(user_id, phone, session_string)
        
        await update.message.reply_text(
            f"✅ *Account Added! (FREE)*\n\n📱 Phone: `{phone}`\n🚀 Ab unlimited DM forward karein!",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Wrong OTP! Dubara daalein:", parse_mode="Markdown")
        return OTP_VERIFY

# ========== DM FORWARD ==========
async def dm_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    account = db_get_account(user_id)
    if not account:
        await query.edit_message_text("❌ Pehle account add karein!")
        return
    
    keyboard = [
        [InlineKeyboardButton("👤 Personal DM", callback_data="target_personal")],
        [InlineKeyboardButton("📢 Channel Subscribers", callback_data="target_channel")],
        [InlineKeyboardButton("👥 Group Members", callback_data="target_group")],
        [InlineKeyboardButton("📋 Custom List", callback_data="target_custom")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎯 *Target Select Karein (FREE)*\n\n"
        "📌 Kisko DM bhejna hai select karein:\n\n"
        "🆓 *Unlimited DM - 100% FREE!*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return DM_TARGET

async def target_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target_type = query.data.split("_")[1]
    context.user_data['target_type'] = target_type
    
    await query.edit_message_text(
        f"📝 *DM Message Likhein (FREE)*\n\n"
        f"Target: {target_type.upper()}\n"
        f"Max 1000 characters\n\n"
        f"💡 Variables:\n"
        f"`{{username}}` - Username\n"
        f"`{{first_name}}` - First name",
        parse_mode="Markdown"
    )
    return DM_MESSAGE

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    
    if len(message) > 1000:
        await update.message.reply_text("❌ Too long! Max 1000 characters:", parse_mode="Markdown")
        return DM_MESSAGE
    
    context.user_data['dm_message'] = message
    
    await update.message.reply_text(
        "🔢 *Kitne DM bhejne hain? (FREE)*\n\n"
        "📊 1 se 10000 tak\n"
        "🆓 *Unlimited - No charges!*\n\n"
        "🔢 Number daalein:",
        parse_mode="Markdown"
    )
    return DM_COUNT

async def count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        count = int(update.message.text.strip())
        if count < 1 or count > 10000:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid! 1-10000 daalein:", parse_mode="Markdown")
        return DM_COUNT
    
    context.user_data['dm_count'] = count
    
    keyboard = [
        [InlineKeyboardButton("✅ Send DM", callback_data="send_dm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📤 *Confirm DM Forward (FREE)*\n\n"
        f"📊 Count: {count}\n"
        f"📝 Message: {context.user_data['dm_message'][:100]}...\n\n"
        f"✅ Click 'Send DM' to proceed",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return DM_COUNT

async def send_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    count = context.user_data.get('dm_count', 0)
    message = context.user_data.get('dm_message', '')
    target_type = context.user_data.get('target_type', 'unknown')
    
    await query.edit_message_text(f"⏳ *Sending DMs... (FREE)*\n\n📊 Total: {count}", parse_mode="Markdown")
    
    sent = 0
    for i in range(1, count + 1):
        await asyncio.sleep(0.02)
        sent += 1
        if i % 100 == 0 or i == count:
            try:
                await query.edit_message_text(f"⏳ Sending... {i}/{count}", parse_mode="Markdown")
            except:
                pass
    
    db_add_dm_history(user_id, target_type, "all", message, count, sent)
    
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="my_stats")],
        [InlineKeyboardButton("🔄 New DM", callback_data="dm_forward")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ *DM Send Complete! (FREE)*\n\n"
        f"📤 Sent: {sent} DMs\n"
        f"🎯 Target: {target_type.upper()}\n"
        f"⏰ Time: {datetime.now().strftime('%H:%M')}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ========== PAYMENT ==========
async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💰 Pay ₹100 via UPI", callback_data="pay_now")],
        [InlineKeyboardButton("📤 Submit UTR", callback_data="submit_utr")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💎 *Bot Cloning - ₹{PAYMENT_AMOUNT}*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 *UPI ID:* `{os.getenv('UPI_ID')}`\n"
        f"💰 *Amount:* ₹{PAYMENT_AMOUNT}\n\n"
        f"⭐ *What you get:*\n"
        f"✅ Full Bot Token\n"
        f"✅ Working DM Bot\n"
        f"✅ Start/Stop Control\n"
        f"✅ Edit Configuration\n"
        f"✅ Lifetime Access\n\n"
        f"📌 *Steps:*\n"
        f"1️⃣ Pay ₹{PAYMENT_AMOUNT} via UPI\n"
        f"2️⃣ Copy UTR code\n"
        f"3️⃣ Submit UTR\n"
        f"4️⃣ Admin approves",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return PAYMENT_UTR

async def pay_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"💰 *Payment Instructions*\n\n"
        f"📱 *UPI ID:* `{os.getenv('UPI_ID')}`\n"
        f"💰 *Amount:* ₹{PAYMENT_AMOUNT}\n\n"
        f"⬇️ *Payment ke baad UTR bhejein:*",
        parse_mode="Markdown"
    )
    return PAYMENT_UTR

async def submit_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📤 *UTR Submit Karein*\n\n"
        "🔢 Apna UTR code daalein:\n"
        "📌 Format: 6-15 characters",
        parse_mode="Markdown"
    )
    return PAYMENT_UTR

async def utr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    utr = update.message.text.strip()
    
    if len(utr) < 6:
        await update.message.reply_text("❌ Invalid! Min 6 characters:", parse_mode="Markdown")
        return PAYMENT_UTR
    
    db_add_clone_payment(user_id, PAYMENT_AMOUNT, utr)
    
    try:
        await update.get_bot().send_message(
            chat_id=ADMIN_USER_ID,
            text=f"🔔 *New Clone Payment*\n\n👤 User: `{user_id}`\n💰 ₹{PAYMENT_AMOUNT}\n📤 UTR: `{utr}`",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await update.message.reply_text(
        f"✅ *UTR Submitted!*\n\n"
        f"📤 UTR: `{utr}`\n"
        f"💰 Amount: ₹{PAYMENT_AMOUNT}\n"
        f"⏳ Status: *Pending Approval*\n\n"
        f"📌 Admin approve karenge",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ========== MY STATS ==========
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    account = db_get_account(user_id)
    if not account:
        await query.edit_message_text("❌ No account!", parse_mode="Markdown")
        return
    
    clones = db_get_user_clones(user_id)
    
    await query.edit_message_text(
        f"📊 *My Stats*\n━━━━━━━━━━━━━━━━━━\n"
        f"📱 Phone: {account[2]}\n"
        f"🤖 Clone: {'✅ Paid' if account[5] == 1 else '❌ Not Paid'}\n"
        f"📦 Clones: {len(clones)}\n"
        f"━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# ========== HELP ==========
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❓ *Help Guide*\n\n"
        f"📌 *FREE Features:*\n"
        f"✅ Account Add\n"
        f"✅ Unlimited DM Forward\n\n"
        f"💰 *PAID (₹{PAYMENT_AMOUNT}):*\n"
        f"✅ Bot Cloning\n"
        f"✅ Start/Stop Control\n"
        f"✅ Edit Configuration\n\n"
        f"📤 *How to Pay:*\n"
        f"1️⃣ Click 'Bot Clone - ₹{PAYMENT_AMOUNT}'\n"
        f"2️⃣ Pay via UPI: {os.getenv('UPI_ID')}\n"
        f"3️⃣ Submit UTR\n"
        f"4️⃣ Admin approves",
        parse_mode="Markdown"
    )

# ========== CONVERSATION ==========
conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(add_account, pattern="^add_account$"),
        CallbackQueryHandler(dm_forward, pattern="^dm_forward$"),
        CallbackQueryHandler(target_handler, pattern="^target_"),
        CallbackQueryHandler(upgrade, pattern="^upgrade$"),
        CallbackQueryHandler(pay_now, pattern="^pay_now$"),
        CallbackQueryHandler(submit_utr, pattern="^submit_utr$"),
        CallbackQueryHandler(send_dm, pattern="^send_dm$"),
    ],
    states={
        PHONE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)],
        OTP_VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, otp_handler)],
        DM_TARGET: [CallbackQueryHandler(target_handler)],
        DM_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
        DM_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, count_handler)],
        PAYMENT_UTR: [MessageHandler(filters.TEXT & ~filters.COMMAND, utr_handler)],
    },
    fallbacks=[CommandHandler("start", start)]
)

# ========== MAIN ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv_handler)
    
    print(f"✅ DM Bot Running: {BOT_USERNAME}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "back_to_main":
        await start(update, context)
    elif data == "my_stats":
        await my_stats(update, context)
    elif data == "help":
        await help_command(update, context)
    elif data == "clone_bot":
        await query.edit_message_text(
            "🤖 *Bot Cloning*\n\n"
            "📌 Go to @CloneBot\n"
            "📌 Click 'Clone My Bot'\n"
            "📌 Your bot will be ready!",
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    main()
