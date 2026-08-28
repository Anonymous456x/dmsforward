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

BOT_TOKEN = os.getenv('DM_BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
CHANNEL_LINK = os.getenv('CHANNEL_LINK', 'https://t.me/+vKFF6nhXTzwxNDdl')
PAYMENT_AMOUNT = int(os.getenv('PAYMENT_AMOUNT', 100))

(ADD_ACCOUNT, PHONE_INPUT, OTP_VERIFY, SET_MESSAGE, SET_AUTO_REPLY, SET_ADS, DM_COUNT, REDEEM_CODE, DM_MESSAGE, DM_SEND, PAYMENT_UTR) = range(11)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== START - NO CHANNEL CHECK ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Directly save user and show menu
    db_add_user(user_id, user.username or "Unknown", user.first_name or "User")
    await show_main_menu(update, context)

# ========== MAIN MENU ==========
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
        f"✅ *Welcome, {first_name} 😊!*\n\n"
        f"🆔 *Your ID:* `{user_id}`\n"
        f"👤 *Username:* @{username}\n\n"
        f"🔔 *Tap Add Account to get started!*\n"
        f"📊 *Accounts:* {len(accounts)}\n"
        f"⭐ *Premium:* {'✅ Yes' if is_premium else '❌ No'}\n\n"
        f"📌 *Select an option:*"
    )
    
    if hasattr(update, 'callback_query'):
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

# ========== ADD ACCOUNT ==========
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📱 *Add Account*\n\n🔢 Enter your *Phone Number*:\nFormat: `+91XXXXXXXXXX`\n\n⚠️ *Note:* OTP will be sent to this number", parse_mode="Markdown")
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
    await update.message.reply_text(f"📱 *OTP Sent!*\n\n🔢 Your OTP: `{otp}`\n*(Demo OTP)*\n\n⬇️ Enter OTP to verify:", parse_mode="Markdown")
    return OTP_VERIFY

async def otp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    entered_otp = update.message.text.strip()
    if entered_otp == context.user_data.get('otp'):
        phone = context.user_data.get('phone')
        session = f"session_{random.randint(1000,9999)}"
        db_add_account(user_id, phone, session)
        await update.message.reply_text(f"✅ *Account Added Successfully!*\n\n📱 Phone: `{phone}`\n🔐 Status: Active\n\n🚀 Now you can start DM campaigns!", parse_mode="Markdown")
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
        keyboard.append([InlineKeyboardButton(f"📱 {acc[2]}", callback_data=f"remove_acc_{acc[0]}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📱 *Select Account to Remove:*", reply_markup=reply_markup, parse_mode="Markdown")

async def remove_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    account_id = int(query.data.split("_")[2])
    db_remove_account(user_id, account_id)
    await query.edit_message_text("✅ *Account Removed Successfully!*", parse_mode="Markdown")

# ========== MASS DM ==========
async def mass_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = db_get_accounts(query.from_user.id)
    if not accounts:
        await query.edit_message_text("❌ *No accounts added!*\n\n📌 Please add an account first:\n➡️ Click 'Add Account'", parse_mode="Markdown")
        return
    await query.edit_message_text("📤 *Start Mass DM Campaign*\n\n📌 Enter your target:\n➡️ Username or Channel ID\n\nType your target username:", parse_mode="Markdown")
    return DM_COUNT

async def dm_count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text.strip()
    context.user_data['dm_target'] = target
    await update.message.reply_text("📝 *Enter your message:*\n\n💡 Use variables:\n`{username}` - User's username\n`{first_name}` - User's first name\n\nType your message:", parse_mode="Markdown")
    return DM_MESSAGE

async def dm_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    context.user_data['dm_message'] = message
    await update.message.reply_text("🔢 *Enter DM Count:*\n\n📊 How many DMs to send?\n➡️ 1 to 10000\n\nType number:", parse_mode="Markdown")
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
    await update.message.reply_text(f"⏳ *Sending DMs...*\n\n🎯 Target: {target}\n📊 Total: {count}", parse_mode="Markdown")
    sent = 0
    for i in range(1, count + 1):
        await asyncio.sleep(0.01)
        sent += 1
        if i % 100 == 0 or i == count:
            try:
                await update.message.edit_text(f"⏳ *Sending DMs...*\n\n🎯 Target: {target}\n📊 Total: {count}\n✅ Progress: {i}/{count}", parse_mode="Markdown")
            except:
                pass
    db_add_dm_history(user_id, target, message, count, sent)
    await update.message.reply_text(f"✅ *DM Campaign Complete!*\n\n📤 Sent: {sent} DMs\n🎯 Target: {target}\n⏰ Time: {datetime.now().strftime('%H:%M')}", parse_mode="Markdown")
    return ConversationHandler.END

# ========== SET MESSAGE ==========
async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 *Set Default Message*\n\n📌 Enter your default DM message:\n💡 Use variables:\n`{username}` - User's username\n`{first_name}` - User's first name\n\nType your message:", parse_mode="Markdown")
    return SET_MESSAGE

async def set_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    await update.message.reply_text(f"✅ *Message Saved!*\n\n📝 {message[:100]}...", parse_mode="Markdown")
    return ConversationHandler.END

# ========== SET AUTO REPLY ==========
async def set_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🤖 *Set Auto Reply*\n\n📌 Enter your auto-reply message:\n💡 This will reply to all incoming messages\n\nType your auto-reply:", parse_mode="Markdown")
    return SET_AUTO_REPLY

async def set_auto_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    await update.message.reply_text(f"✅ *Auto Reply Saved!*\n\n🤖 {message[:100]}...", parse_mode="Markdown")
    return ConversationHandler.END

# ========== SET ADS ==========
async def set_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📊 *Set Ads*\n\n📌 Enter your ad text:\n💡 You can add images/videos too\n\nType your ad:", parse_mode="Markdown")
    return SET_ADS

async def set_ads_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    await update.message.reply_text(f"✅ *Ad Saved!*\n\n📊 {message[:100]}...", parse_mode="Markdown")
    return ConversationHandler.END

async def ads_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📋 *Ads Logs*\n\nNo ads logs available yet!", parse_mode="Markdown")

async def channel_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📢 *Channel Promo*\n\n📌 Promote your channel here!\nComing soon...", parse_mode="Markdown")

async def preview_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👁️ *Preview Message*\n\n📌 Your default message will appear here!", parse_mode="Markdown")

async def join_request_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📩 *Join Request DM*\n\n📌 Send join requests to users!", parse_mode="Markdown")

# ========== MY STATS ==========
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = db_get_user(user_id)
    accounts = db_get_accounts(user_id)
    clones = db_get_user_clones(user_id)
    stats_text = (
        f"📊 *My Stats*\n━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Username: @{query.from_user.username or 'None'}\n"
        f"📱 Accounts: {len(accounts)}\n"
        f"⭐ Premium: {'✅ Yes' if user[4] else '❌ No'}\n"
        f"🤖 Clones: {len(clones)}\n"
        f"👥 Referrals: {user[5] if user else 0}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n💡 *Upgrade to Premium for more features!*"
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
        f"💎 *Go VIP Premium - ₹{PAYMENT_AMOUNT}*\n━━━━━━━━━━━━━━━━━━\n\n"
        "⭐ *Benefits:*\n✅ Unlimited DM (10000/day)\n✅ Bot Cloning Access\n✅ Priority Support\n✅ No Ads\n✅ Fast Processing\n\n"
        f"💰 *Price: ₹{PAYMENT_AMOUNT} (One-time)*\n\n"
        "📌 *Payment Options:*\n1️⃣ Scan QR Code & Pay\n2️⃣ Submit UTR\n3️⃣ Admin Approves\n4️⃣ Premium Activated!",
        reply_markup=reply_markup, parse_mode="Markdown"
    )

# ========== QR CODE PAYMENT ==========
async def pay_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    upi_id = os.getenv('UPI_ID', 'your@upi')
    amount = PAYMENT_AMOUNT
    name = "Bot Premium"
    try:
        import qrcode
        from io import BytesIO
        upi_link = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
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
            f"💳 *Scan QR Code to Pay ₹{PAYMENT_AMOUNT}*\n━━━━━━━━━━━━━━━━━━\n\n"
            f"📱 *UPI ID:* `{upi_id}`\n💰 *Amount:* ₹{PAYMENT_AMOUNT}\n\n"
            f"📌 *Steps:*\n1️⃣ Scan QR code with any UPI app\n2️⃣ Pay ₹{PAYMENT_AMOUNT}\n3️⃣ Click 'Submit UTR'\n4️⃣ Enter UTR code\n\n"
            f"✅ *After payment, premium will be activated!*",
            reply_markup=reply_markup, parse_mode="Markdown"
        )
        await context.bot.send_photo(chat_id=user_id, photo=bio, caption=f"💳 *Scan to Pay ₹{PAYMENT_AMOUNT}*", parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"❌ *Error generating QR Code!*\n\n📌 Please use UPI ID directly:\n`{os.getenv('UPI_ID')}`\n\n💳 Pay ₹{PAYMENT_AMOUNT} and submit UTR", parse_mode="Markdown")

# ========== SUBMIT UTR ==========
async def submit_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📤 *Submit UTR Code*\n\n🔢 Enter your UTR number:\n📌 Found in your payment receipt\n\n⬇️ Type your UTR:", parse_mode="Markdown")
    return PAYMENT_UTR

async def utr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    utr = update.message.text.strip()
    if len(utr) < 6:
        await update.message.reply_text("❌ *Invalid UTR!*\n📌 UTR should be 6-15 characters\n\n⬇️ Enter again:", parse_mode="Markdown")
        return PAYMENT_UTR
    db_add_clone_payment(user_id, PAYMENT_AMOUNT, utr)
    try:
        await update.get_bot().send_message(chat_id=ADMIN_USER_ID,
            text=f"🔔 *New Payment Received!*\n\n👤 User: `{user_id}`\n💰 Amount: ₹{PAYMENT_AMOUNT}\n📤 UTR: `{utr}`\n📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n✅ Use @{os.getenv('ADMIN_BOT_USERNAME')[1:]} to approve",
            parse_mode="Markdown")
    except:
        pass
    keyboard = [
        [InlineKeyboardButton("📊 Check Status", callback_data="check_payment_status")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"✅ *UTR Submitted Successfully!*\n\n📤 UTR: `{utr}`\n💰 Amount: ₹{PAYMENT_AMOUNT}\n⏳ Status: *Pending Approval*\n\n📌 Admin will verify and approve within 24 hours.", reply_markup=reply_markup, parse_mode="Markdown")
    return ConversationHandler.END

# ========== CHECK PAYMENT STATUS ==========
async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = db_get_user(user_id)
    if user and user[4] == 1:
        await query.edit_message_text(f"✅ *Payment Status: Approved!*\n\n💰 Amount: ₹{PAYMENT_AMOUNT}\n⭐ Status: *Premium Active*\n\n🚀 Clone your bot at @{os.getenv('CLONE_BOT_USERNAME')[1:]}", parse_mode="Markdown")
    else:
        conn = sqlite3.connect('shared.db')
        c = conn.cursor()
        c.execute("SELECT * FROM clone_payments WHERE user_id = ? AND status = 'pending' ORDER BY id DESC LIMIT 1", (user_id,))
        pending = c.fetchone()
        conn.close()
        if pending:
            await query.edit_message_text(f"⏳ *Payment Status: Pending*\n\n💰 Amount: ₹{pending[2]}\n📤 UTR: `{pending[3]}`\n📅 Date: {pending[4][:10]}\n\n📌 Admin will approve soon!", parse_mode="Markdown")
        else:
            await query.edit_message_text(f"❌ *No Payment Found*\n\n💰 Pay ₹{PAYMENT_AMOUNT} to get premium!", parse_mode="Markdown")

# ========== REDEEM CODE ==========
async def redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎫 *Redeem Code*\n\n📌 Enter your redeem code:\n\n💡 Codes are case-sensitive\n⬇️ Type your code:", parse_mode="Markdown")
    return REDEEM_CODE

async def redeem_code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.strip()
    code_data = db_use_redeem_code(code, user_id)
    if code_data:
        if code_data[2] == 'premium':
            db_update_premium(user_id)
            await update.message.reply_text(f"✅ *Code Redeemed Successfully!*\n\n🎁 Reward: Premium Access\n⭐ Status: Active\n\n🚀 Enjoy premium features!", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"✅ *Code Redeemed!*\n\n🎁 Reward: {code_data[2]}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ *Invalid or Used Code!*\n\n📌 Please check and try again.", parse_mode="Markdown")
    return ConversationHandler.END

# ========== ACCEPT PENDING ==========
async def accept_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    requests = db_get_pending_requests(user_id)
    if not requests:
        await query.edit_message_text("✅ No pending requests!", parse_mode="Markdown")
        return
    keyboard = []
    for req in requests:
        keyboard.append([InlineKeyboardButton(f"📩 Accept from {req[1]}", callback_data=f"accept_req_{req[0]}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"📥 *Pending Requests ({len(requests)})*\n\nSelect to accept:", reply_markup=reply_markup, parse_mode="Markdown")

async def accept_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    request_id = int(query.data.split("_")[2])
    db_accept_request(request_id)
    await query.edit_message_text("✅ *Request Accepted!*", parse_mode="Markdown")

# ========== REFER & EARN ==========
async def refer_earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_username = (await context.bot.get_me()).username
    refer_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await query.edit_message_text(
        "👥 *Refer & Earn*\n━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *Share your referral link:*\n`{refer_link}`\n\n"
        "⭐ *Benefits:*\n✅ 5 referrals = 1 month Premium\n✅ 10 referrals = Lifetime Premium\n✅ 20 referrals = ₹100 Cash\n\n"
        "📊 *Your Referrals:* 0\n\n🔗 *Share and earn rewards!*",
        parse_mode="Markdown"
    )

# ========== SUPPORT ==========
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💬 *Support*\n━━━━━━━━━━━━━━━━━━\n\n📌 *Contact Us:*\n👤 Admin: @admin_username\n📧 Email: support@example.com\n\n⏰ *Response Time:*\n24-48 hours\n\n🤖 *Bot Issues:*\nReport with /feedback", parse_mode="Markdown")

# ========== HOW TO USE ==========
async def how_to_use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "❓ *How to Use*\n━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ *Add Account*\n   📱 Enter phone number\n   🔢 Enter OTP\n   ✅ Account added\n\n"
        "2️⃣ *Start DM Campaign*\n   📤 Click 'Start Mass DM'\n   🎯 Enter target\n   📝 Enter message\n   🔢 Enter count\n\n"
        "3️⃣ *Premium Features*\n   💎 Go VIP Premium\n   💳 Scan QR & Pay ₹100\n   🎫 Or use Redeem Code\n\n"
        "4️⃣ *Other Features*\n   🤖 Auto Reply\n   📊 Ads\n   👥 Refer & Earn",
        parse_mode="Markdown"
    )

# ========== BUTTON HANDLER ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "back_to_menu":
        await show_main_menu(update, context)
    elif data.startswith("remove_acc_"):
        await remove_account_callback(update, context)
    elif data == "add_account":
        await add_account(update, context)
    elif data == "remove_account":
        await remove_account(update, context)
    elif data == "mass_dm":
        await mass_dm(update, context)
    elif data == "channel_promo":
        await channel_promo(update, context)
    elif data == "set_auto_reply":
        await set_auto_reply(update, context)
    elif data == "set_ads":
        await set_ads(update, context)
    elif data == "ads_logs":
        await ads_logs(update, context)
    elif data == "set_message":
        await set_message(update, context)
    elif data == "preview_message":
        await preview_message(update, context)
    elif data == "my_stats":
        await my_stats(update, context)
    elif data == "my_account":
        await my_account(update, context)
    elif data == "go_vip":
        await go_vip(update, context)
    elif data == "pay_qr":
        await pay_qr(update, context)
    elif data == "submit_utr":
        await submit_utr(update, context)
    elif data == "check_payment_status":
        await check_payment_status(update, context)
    elif data == "redeem_code":
        await redeem_code(update, context)
    elif data == "accept_pending":
        await accept_pending(update, context)
    elif data.startswith("accept_req_"):
        await accept_request_callback(update, context)
    elif data == "join_request_dm":
        await join_request_dm(update, context)
    elif data == "refer_earn":
        await refer_earn(update, context)
    elif data == "how_to_use":
        await how_to_use(update, context)
    elif data == "support":
        await support(update, context)

# ========== CONVERSATION HANDLER ==========
conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(add_account, pattern="^add_account$"),
        CallbackQueryHandler(set_message, pattern="^set_message$"),
        CallbackQueryHandler(set_auto_reply, pattern="^set_auto_reply$"),
        CallbackQueryHandler(set_ads, pattern="^set_ads$"),
        CallbackQueryHandler(mass_dm, pattern="^mass_dm$"),
        CallbackQueryHandler(redeem_code, pattern="^redeem_code$"),
        CallbackQueryHandler(submit_utr, pattern="^submit_utr$"),
    ],
    states={
        PHONE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)],
        OTP_VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, otp_handler)],
        SET_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_message_handler)],
        SET_AUTO_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_auto_reply_handler)],
        SET_ADS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_ads_handler)],
        DM_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, dm_count_handler)],
        DM_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dm_message_handler)],
        DM_SEND: [MessageHandler(filters.TEXT & ~filters.COMMAND, dm_send_handler)],
        REDEEM_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, redeem_code_handler)],
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
    print(f"✅ DM Increaser Bot Running: {os.getenv('DM_BOT_USERNAME')}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
