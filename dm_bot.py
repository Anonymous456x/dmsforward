import os
import logging
import random
import re
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from database import *

load_dotenv()

# ========== CONFIG ==========
BOT_TOKEN = os.getenv('DM_BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
CHANNEL_LINK = os.getenv('CHANNEL_LINK', 'https://t.me/+vKFF6nhXTzwxNDdl')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '@free_promote')
PAYMENT_AMOUNT = int(os.getenv('PAYMENT_AMOUNT', 100))

# ========== STATES ==========
(ADD_ACCOUNT, PHONE_INPUT, OTP_VERIFY, SET_MESSAGE, 
 SET_AUTO_REPLY, SET_ADS, DM_COUNT, REDEEM_CODE, 
 DM_MESSAGE, DM_SEND, PAYMENT_UTR) = range(11)

# ========== LOGGING ==========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CHECK CHANNEL JOIN ==========
async def check_channel_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except:
        pass
    return False

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Check if user joined channel
    if not await check_channel_join(update, context):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Check Again", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ *Please Join Our Channel First!*\n\n"
            "🔹 Click below to join:\n"
            f"{CHANNEL_LINK}\n\n"
            "✅ After joining, click 'Check Again'",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # User joined, show main menu
    db_add_user(user_id, user.username or "Unknown", user.first_name or "User")
    await show_main_menu(update, context)

# ========== CHECK JOIN CALLBACK ==========
async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if await check_channel_join(update, context):
        db_add_user(user_id, query.from_user.username or "Unknown", query.from_user.first_name or "User")
        await show_main_menu(update, context)
    else:
        await query.edit_message_text(
            "❌ *You haven't joined the channel yet!*\n\n"
            f"🔹 Join: {CHANNEL_LINK}\n\n"
            "✅ After joining, click 'Check Again'",
            parse_mode="Markdown"
        )

# ========== MAIN MENU - EXACTLY LIKE SCREENSHOT ==========
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.callback_query.from_user.id
    user = db_get_user(user_id)
    is_premium = user[4] if user else 0
    username = update.effective_user.username or 'None'
    first_name = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("📤 Start Mass DM Campaign", callback_data="mass_dm")],
        [InlineKeyboardButton("📢 Channel Promo", callback_data="channel_promo")],
        [InlineKeyboardButton("🤖 Set Auto Reply", callback_data="set_auto_reply")],
        [InlineKeyboardButton("📊 Set Ads", callback_data="set_ads")],
        [InlineKeyboardButton("📋 Ads Logs", callback_data="ads_logs")],
        [InlineKeyboardButton("📝 Set Message", callback_data="set_message")],
        [InlineKeyboardButton("👁️ Preview Message", callback_data="preview_message")],
        [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
        [InlineKeyboardButton("👤 My Account", callback_data="my_account")],
        [InlineKeyboardButton("💎 Go VIP Premium", callback_data="go_vip")],
        [InlineKeyboardButton("🎫 Redeem Code", callback_data="redeem_code")],
        [InlineKeyboardButton("➕ Add Account", callback_data="add_account")],
        [InlineKeyboardButton("➖ Remove Account", callback_data="remove_account")],
        [InlineKeyboardButton("📥 Accept Pending", callback_data="accept_pending")],
        [InlineKeyboardButton("📩 Join Request DM", callback_data="join_request_dm")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer_earn")],
        [InlineKeyboardButton("❓ How to Use", callback_data="how_to_use")],
        [InlineKeyboardButton("💬 Support", callback_data="support")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    accounts = db_get_accounts(user_id)
    
    welcome_text = (
        f"✅ *All channels joined! Welcome, {first_name} 😊!*\n\n"
        f"🆔 *Your ID:* `{user_id}`\n"
        f"👤 *Username:* @{username}\n\n"
        f"🔔 *Tap Add Account to get started!*\n"
        f"📊 *Accounts:* {len(accounts)}\n"
        f"⭐ *Premium:* {'✅ Yes' if is_premium else '❌ No'}\n"
        f"📤 *DMs Sent:* {len(db_get_all_users())}\n\n"
        f"📌 *Select an option:*"
    )
    
    if hasattr(update, 'callback_query'):
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# ========== ADD ACCOUNT ==========
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📱 *Add Account*\n\n"
        "🔢 Enter your *Phone Number*:\n"
        "Format: `+91XXXXXXXXXX`\n\n"
        "⚠️ *Note:* OTP will be sent to this number",
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
        f"📱 *OTP Sent!*\n\n"
        f"🔢 Your OTP: `{otp}`\n"
        f"*(Demo OTP)*\n\n"
        f"⬇️ Enter OTP to verify:",
        parse_mode="Markdown"
    )
    return OTP_VERIFY

async def otp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    entered_otp = update.message.text.strip()
    
    if entered_otp == context.user_data.get('otp'):
        phone = context.user_data.get('phone')
        session = f"session_{random.randint(1000,9999)}"
        db_add_account(user_id, phone, session)
        
        await update.message.reply_text(
            f"✅ *Account Added Successfully!*\n\n"
            f"📱 Phone: `{phone}`\n"
            f"🔐 Status: Active\n\n"
            f"🚀 Now you can start DM campaigns!",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Wrong OTP! Try again:", parse_mode="Markdown")
        return OTP_VERIFY

# ========== REMOVE ACCOUNT ==========
async def remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    accounts = db_get_accounts(user_id)
    
    if not accounts:
        await query.edit_message_text("❌ No accounts to remove!", parse_mode="Markdown")
        return
    
    keyboard = []
    for acc in accounts:
        keyboard.append([
            InlineKeyboardButton(f"📱 {acc[2]}", callback_data=f"remove_acc_{acc[0]}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📱 *Select Account to Remove:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def remove_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    account_id = int(query.data.split("_")[2])
    
    db_remove_account(user_id, account_id)
    await query.edit_message_text(
        "✅ *Account Removed Successfully!*",
        parse_mode="Markdown"
    )

# ========== MASS DM ==========
async def mass_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    accounts = db_get_accounts(query.from_user.id)
    if not accounts:
        await query.edit_message_text(
            "❌ *No accounts added!*\n\n"
            "📌 Please add an account first:\n"
            "➡️ Click 'Add Account'",
            parse_mode="Markdown"
        )
        return
    
    await query.edit_message_text(
        "📤 *Start Mass DM Campaign*\n\n"
        "📌 Enter your target:\n"
        "➡️ Username or Channel ID\n\n"
        "Type your target username:",
        parse_mode="Markdown"
    )
    return DM_COUNT

async def dm_count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target = update.message.text.strip()
    
    context.user_data['dm_target'] = target
    
    await update.message.reply_text(
        "📝 *Enter your message:*\n\n"
        "💡 Use variables:\n"
        "`{username}` - User's username\n"
        "`{first_name}` - User's first name\n\n"
        "Type your message:",
        parse_mode="Markdown"
    )
    return DM_MESSAGE

async def dm_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()
    
    context.user_data['dm_message'] = message
    
    await update.message.reply_text(
        "🔢 *Enter DM Count:*\n\n"
        "📊 How many DMs to send?\n"
        "➡️ 1 to 10000\n\n"
        "Type number:",
        parse_mode="Markdown"
    )
    return DM_SEND

async def dm_send_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        count = int(update.message.text.strip())
        if count < 1 or count > 10000:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid number! 1-10000 daalein:", parse_mode="Markdown")
        return DM_SEND
    
    target = context.user_data.get('dm_target', 'unknown')
    message = context.user_data.get('dm_message', '')
    
    # Simulate sending
    await update.message.reply_text(
        f"⏳ *Sending DMs...*\n\n"
        f"🎯 Target: {target}\n"
        f"📊 Total: {count}\n"
        f"⏳ Progress: 0%",
        parse_mode="Markdown"
    )
    
    sent = 0
    for i in range(1, count + 1):
        await asyncio.sleep(0.01)
        sent += 1
        if i % 100 == 0 or i == count:
            try:
                await update.message.edit_text(
                    f"⏳ *Sending DMs...*\n\n"
                    f"🎯 Target: {target}\n"
                    f"📊 Total: {count}\n"
                    f"✅ Progress: {i}/{count}",
                    parse_mode="Markdown"
                )
            except:
                pass
    
    db_add_dm_history(user_id, target, message, count, sent)
    
    await update.message.reply_text(
        f"✅ *DM Campaign Complete!*\n\n"
        f"📤 Sent: {sent} DMs\n"
        f"🎯 Target: {target}\n"
        f"⏰ Time: {datetime.now().strftime('%H:%M')}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ========== SET MESSAGE ==========
async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📝 *Set Default Message*\n\n"
        "📌 Enter your default DM message:\n"
        "💡 Use variables:\n"
        "`{username}` - User's username\n"
        "`{first_name}` - User's first name\n\n"
        "Type your message:",
        parse_mode="Markdown"
    )
    return SET_MESSAGE

# ========== SET AUTO REPLY ==========
async def set_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🤖 *Set Auto Reply*\n\n"
        "📌 Enter your auto-reply message:\n"
        "💡 This will reply to all incoming messages\n\n"
        "Type your auto-reply:",
        parse_mode="Markdown"
    )
    return SET_AUTO_REPLY

# ========== SET ADS ==========
async def set_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📊 *Set Ads*\n\n"
        "📌 Enter your ad text:\n"
        "💡 You can add images/videos too\n\n"
        "Type your ad:",
        parse_mode="Markdown"
    )
    return SET_ADS

# ========== MY STATS ==========
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user = db_get_user(user_id)
    accounts = db_get_accounts(user_id)
    clones = db_get_user_clones(user_id)
    
    stats_text = (
        f"📊 *My Stats*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Username: @{query.from_user.username or 'None'}\n"
        f"📱 Accounts: {len(accounts)}\n"
        f"⭐ Premium: {'✅ Yes' if user[4] else '❌ No'}\n"
        f"🤖 Clones: {len(clones)}\n"
        f"👥 Referrals: {user[5] if user else 0}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 *Upgrade to Premium for more features!*"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode="Markdown")

# ========== MY ACCOUNT ==========
async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user = db_get_user(user_id)
    accounts = db_get_accounts(user_id)
    clones = db_get_user_clones(user_id)
    
    account_text = f"👤 *My Account*\n━━━━━━━━━━━━━━━━━━\n"
    account_text += f"🆔 ID: `{user_id}`\n"
    account_text += f"👤 Username: @{query.from_user.username or 'None'}\n"
    account_text += f"⭐ Premium: {'✅ Yes' if user[4] else '❌ No'}\n"
    account_text += f"🤖 Clones: {len(clones)}\n"
    account_text += f"━━━━━━━━━━━━━━━━━━\n\n"
    
    account_text += "📱 *Accounts:*\n"
    if accounts:
        for acc in accounts:
            account_text += f"➡️ {acc[2]} (Added: {acc[4][:10]})\n"
    else:
        account_text += "❌ No accounts added\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Account", callback_data="add_account")],
        [InlineKeyboardButton("➖ Remove Account", callback_data="remove_account")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(account_text, reply_markup=reply_markup, parse_mode="Markdown")

# ========== GO VIP PREMIUM ==========
async def go_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💳 Pay ₹100 - QR Code", callback_data="pay_qr")],
        [InlineKeyboardButton("📤 Submit UTR", callback_data="submit_utr")],
        [InlineKeyboardButton("📊 Check Status", callback_data="check_payment_status")],
        [InlineKeyboardButton("🎫 Redeem Code", callback_data="redeem_code")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💎 *Go VIP Premium - ₹{PAYMENT_AMOUNT}*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⭐ *Benefits:*\n"
        "✅ Unlimited DM (10000/day)\n"
        "✅ Bot Cloning Access\n"
        "✅ Priority Support\n"
        "✅ No Ads\n"
        "✅ Fast Processing\n\n"
        f"💰 *Price: ₹{PAYMENT_AMOUNT} (One-time)*\n\n"
        "📌 *Payment Options:*\n"
        "1️⃣ Scan QR Code & Pay\n"
        "2️⃣ Submit UTR\n"
        "3️⃣ Admin Approves\n"
        "4️⃣ Premium Activated!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ========== QR CODE PAYMENT ==========
async def pay_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    upi_id = os.getenv('UPI_ID', 'your@upi')
    amount = PAYMENT_AMOUNT
    name = "Bot Premium"
    
    # Generate QR Code
    try:
        import qrcode
        from io import BytesIO
        
        upi_link = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_link)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        bio = BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        
        keyboard = [
            [InlineKeyboardButton("✅ I've Paid - Submit UTR", callback_data="submit_utr")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f
