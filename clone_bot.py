import os
import logging
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from database import *

load_dotenv()

# ========== CONFIG ==========
BOT_TOKEN = os.getenv('CLONE_BOT_TOKEN')
BOT_USERNAME = os.getenv('CLONE_BOT_USERNAME')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
PAYMENT_AMOUNT = int(os.getenv('PAYMENT_AMOUNT', 100))

# ========== STATES ==========
EDIT_BOT_TOKEN, EDIT_BOT_USERNAME, EDIT_UPI, EDIT_AMOUNT = range(4)

# ========== LOGGING ==========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    user_data = db_get_user(user_id)
    
    keyboard = []
    
    if user_data and user_data[4] == 1:
        keyboard.append([InlineKeyboardButton("🤖 Clone My Bot", callback_data="clone_now")])
        keyboard.append([InlineKeyboardButton("📦 My Clones", callback_data="my_clones")])
        keyboard.append([InlineKeyboardButton("📊 Check Status", callback_data="check_status")])
    else:
        keyboard.append([
            InlineKeyboardButton(f"💰 Pay ₹{PAYMENT_AMOUNT}", url=f"https://t.me/{os.getenv('DM_BOT_USERNAME')[1:]}")
        ])
        keyboard.append([
            InlineKeyboardButton("📤 Check Payment Status", callback_data="check_payment")
        ])
    
    keyboard.append([InlineKeyboardButton("❓ Help", callback_data="help")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if user_data and user_data[4] == 1:
        await update.message.reply_text(
            f"🤖 *Bot Cloning*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ *Access Granted!*\n"
            f"💰 Payment: ₹{PAYMENT_AMOUNT} (Paid)\n\n"
            f"📌 *Features:*\n"
            f"✅ Clone your own DM bot\n"
            f"✅ Start/Stop bot anytime\n"
            f"✅ Edit configuration\n"
            f"✅ Full control\n\n"
            f"🚀 *Ready to clone?*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"🤖 *Bot Cloning*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ *Access Required!*\n\n"
            f"💰 Pay ₹{PAYMENT_AMOUNT} to get:\n"
            f"✅ Your own DM Bot\n"
            f"✅ Start/Stop control\n"
            f"✅ Edit configuration\n"
            f"✅ Lifetime Access\n\n"
            f"📌 *How to Pay:*\n"
            f"1️⃣ Pay via UPI: {os.getenv('UPI_ID')}\n"
            f"2️⃣ Submit UTR in DM Bot\n"
            f"3️⃣ Admin approves\n"
            f"4️⃣ Come back & clone!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# ========== CLONE NOW ==========
async def clone_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user = db_get_user(user_id)
    if not user or user[4] != 1:
        await query.edit_message_text(
            f"❌ *Access Denied!*\n\n💰 Pay ₹{PAYMENT_AMOUNT} first",
            parse_mode="Markdown"
        )
        return
    
    bot = db_get_available_bots()
    
    if not bot:
        await query.edit_message_text(
            "❌ *No bots available!*\n\n📌 Admin se contact karein",
            parse_mode="Markdown"
        )
        return
    
    bot_id, bot_token, bot_username, status = bot
    
    db_mark_bot_used(bot_id)
    
    default_env = {
        "BOT_TOKEN": bot_token,
        "BOT_USERNAME": bot_username,
        "ADMIN_USER_ID": str(user_id),
        "UPI_ID": os.getenv('UPI_ID', 'your@upi'),
        "PAYMENT_AMOUNT": str(PAYMENT_AMOUNT)
    }
    
    db_add_clone(user_id, bot_token, bot_username)
    db_update_clone_env(user_id, bot_token, default_env)
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start Bot", callback_data=f"start_bot_{bot_token}")],
        [InlineKeyboardButton("📦 My Clones", callback_data="my_clones")],
        [InlineKeyboardButton("⚙️ Edit Config", callback_data=f"edit_bot_{bot_token}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎉 *Bot Cloned Successfully!*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 *Bot:* {bot_username}\n"
        f"🔑 *Token:* `{bot_token}`\n\n"
        f"📌 *Controls:*\n"
        f"✅ Start Bot - Run your bot\n"
        f"✅ Stop Bot - Stop your bot\n"
        f"✅ Edit Config - Change settings",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ========== START BOT ==========
async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_token = query.data.replace("start_bot_", "")
    
    clone = db_get_clone_by_token(user_id, bot_token)
    if not clone:
        await query.edit_message_text("❌ You don't own this bot!", parse_mode="Markdown")
        return
    
    db_update_clone_status(user_id, bot_token, "running")
    
    await query.edit_message_text(
        f"✅ *Bot Started!*\n\n"
        f"🤖 Your bot is now running!\n"
        f"📌 Use 'Stop Bot' to stop it\n\n"
        f"🔗 {clone[3]}",
        parse_mode="Markdown"
    )

# ========== STOP BOT ==========
async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_token = query.data.replace("stop_bot_", "")
    
    clone = db_get_clone_by_token(user_id, bot_token)
    if not clone:
        await query.edit_message_text("❌ You don't own this bot!", parse_mode="Markdown")
        return
    
    db_update_clone_status(user_id, bot_token, "stopped")
    
    await query.edit_message_text(
        f"⏹️ *Bot Stopped!*\n\n"
        f"🤖 Your bot has been stopped\n"
        f"📌 Use 'Start Bot' to run again",
        parse_mode="Markdown"
    )

# ========== MY CLONES ==========
async def my_clones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    clones = db_get_user_clones(user_id)
    
    if not clones:
        await query.edit_message_text(
            "❌ *No clones yet!*\n\n📌 Click 'Clone My Bot' to get your first bot!",
            parse_mode="Markdown"
        )
        return
    
    text = "🤖 *Your Clones*\n━━━━━━━━━━━━━━━━━━\n\n"
    keyboard = []
    
    for i, clone in enumerate(clones[:10], 1):
        bot_token = clone[0]
        bot_username = clone[1]
        created_date = clone[2]
        status = clone[3] if len(clone) > 3 else "stopped"
        
        status_emoji = "🟢" if status == "running" else "🔴"
        text += f"{i}. {bot_username}\n"
        text += f"   🔑 `{bot_token[:20]}...`\n"
        text += f"   📅 {created_date[:10]}\n"
        text += f"   {status_emoji} Status: {status}\n\n"
        
        keyboard.extend([
            [
                InlineKeyboardButton(f"▶️ Start", callback_data=f"start_bot_{bot_token}"),
                InlineKeyboardButton(f"⏹️ Stop", callback_data=f"stop_bot_{bot_token}")
            ],
            [
                InlineKeyboardButton(f"⚙️ Edit Config", callback_data=f"edit_bot_{bot_token}")
            ]
        ])
    
    keyboard.append([InlineKeyboardButton("🔄 Clone New Bot", callback_data="clone_now")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ========== EDIT BOT ==========
async def edit_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_token = query.data.replace("edit_bot_", "")
    
    clone = db_get_clone_by_token(user_id, bot_token)
    if not clone:
        await query.edit_message_text("❌ You don't own this bot!", parse_mode="Markdown")
        return
    
    env_data = db_get_clone_env(user_id, bot_token)
    
    keyboard = [
        [InlineKeyboardButton("🔑 Edit Bot Token", callback_data=f"edit_token_{bot_token}")],
        [InlineKeyboardButton("📱 Edit Username", callback_data=f"edit_username_{bot_token}")],
        [InlineKeyboardButton("💳 Edit UPI ID", callback_data=f"edit_upi_{bot_token}")],
        [InlineKeyboardButton("💰 Edit Amount", callback_data=f"edit_amount_{bot_token}")],
        [InlineKeyboardButton("📋 View Config", callback_data=f"view_config_{bot_token}")],
        [InlineKeyboardButton("🔙 Back", callback_data="my_clones")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"⚙️ *Edit Configuration*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 Bot: {clone[3]}\n\n"
        f"🔑 Token: `{env_data.get('BOT_TOKEN', 'N/A')[:20]}...`\n"
        f"📱 Username: {env_data.get('BOT_USERNAME', 'N/A')}\n"
        f"💳 UPI: {env_data.get('UPI_ID', 'N/A')}\n"
        f"💰 Amount: ₹{env_data.get('PAYMENT_AMOUNT', '100')}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ========== VIEW CONFIG ==========
async def view_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_token = query.data.replace("view_config_", "")
    
    env_data = db_get_clone_env(user_id, bot_token)
    clone = db_get_clone_by_token(user_id, bot_token)
    
    config_text = f"📋 *Current Configuration*\n━━━━━━━━━━━━━━━━━━\n\n"
    config_text += f"🤖 Bot: {clone[3]}\n\n"
    for key, value in env_data.items():
        if key == "BOT_TOKEN":
            config_text += f"🔑 {key}: `{value[:20]}...`\n"
        else:
            config_text += f"📌 {key}: `{value}`\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data=f"edit_bot_{bot_token}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(config_text, reply_markup=reply_markup, parse_mode="Markdown")

# ========== EDIT HANDLERS ==========
async def edit_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_token = query.data.replace("edit_token_", "")
    
    context.user_data['editing_bot_token'] = bot_token
    context.user_data['edit_field'] = 'BOT_TOKEN'
    
    await query.edit_message_text(
        f"🔑 *Edit Bot Token*\n\n"
        f"📌 New Token daalein:\n"
        f"Format: `123456:ABC-DEF`\n\n"
        f"⬇️ Type karke bhejein:",
        parse_mode="Markdown"
    )
    return EDIT_BOT_TOKEN

async def edit_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_token = query.data.replace("edit_username_", "")
    
    context.user_data['editing_bot_token'] = bot_token
    context.user_data['edit_field'] = 'BOT_USERNAME'
    
    await query.edit_message_text(
        f"📱 *Edit Bot Username*\n\n"
        f"📌 New Username daalein:\n"
        f"Format: `@YourBotUsername`\n\n"
        f"⬇️ Type karke bhejein:",
        parse_mode="Markdown"
    )
    return EDIT_BOT_USERNAME

async def edit_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_token = query.data.replace("edit_upi_", "")
    
    context.user_data['editing_bot_token'] = bot_token
    context.user_data['edit_field'] = 'UPI_ID'
    
    await query.edit_message_text(
        f"💳 *Edit UPI ID*\n\n"
        f"📌 New UPI ID daalein:\n"
        f"Format: `your@upi`\n\n"
        f"⬇️ Type karke bhejein:",
        parse_mode="Markdown"
    )
    return EDIT_UPI

async def edit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_token = query.data.replace("edit_amount_", "")
    
    context.user_data['editing_bot_token'] = bot_token
    context.user_data['edit_field'] = 'PAYMENT_AMOUNT'
    
    await query.edit_message_text(
        f"💰 *Edit Payment Amount*\n\n"
        f"📌 New Amount daalein:\n"
        f"Format: `150` (Number only)\n\n"
        f"⬇️ Type karke bhejein:",
        parse_mode="Markdown"
    )
    return EDIT_AMOUNT

async def edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_token = context.user_data.get('editing_bot_token')
    field = context.user_data.get('edit_field')
    new_value = update.message.text.strip()
    
    if not bot_token:
        await update.message.reply_text("❌ Session expired!", parse_mode="Markdown")
        return ConversationHandler.END
    
    env_data = db_get_clone_env(user_id, bot_token)
    
    if field == 'PAYMENT_AMOUNT':
        try:
            new_value = str(int(new_value))
            if int(new_value) < 1:
                raise ValueError
        except:
            await update.message.reply_text("❌ Invalid amount! Number daalein:", parse_mode="Markdown")
            return EDIT_AMOUNT
    elif field == 'BOT_TOKEN':
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', new_value):
            await update.message.reply_text("❌ Invalid token format!", parse_mode="Markdown")
            return EDIT_BOT_TOKEN
    
    env_data[field] = new_value
    db_update_clone_env(user_id, bot_token, env_data)
    
    await update.message.reply_text(
        f"✅ *{field} Updated!*\n\n"
        f"📌 New Value: `{new_value}`\n"
        f"🔄 Restart bot for changes to take effect",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ========== CHECK PAYMENT ==========
async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user = db_get_user(user_id)
    
    if user and user[4] == 1:
        await query.edit_message_text(
            f"✅ *Payment Status: Approved!*\n\n"
            f"💰 Amount: ₹{PAYMENT_AMOUNT}\n"
            f"🤖 Access: Granted\n\n"
            f"📌 Click 'Clone My Bot' now!",
            parse_mode="Markdown"
        )
    else:
        conn = sqlite3.connect('shared.db')
        c = conn.cursor()
        c.execute("SELECT * FROM clone_payments WHERE user_id = ? AND status = 'pending'", (user_id,))
        pending = c.fetchone()
        conn.close()
        
        if pending:
            await query.edit_message_text(
                f"⏳ *Payment Status: Pending*\n\n"
                f"💰 Amount: ₹{PAYMENT_AMOUNT}\n"
                f"📤 UTR: {pending[3]}\n\n"
                f"📌 Admin will approve soon",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"❌ *No Payment Found*\n\n"
                f"💰 Pay ₹{PAYMENT_AMOUNT} to get clone access",
                parse_mode="Markdown"
            )

# ========== HELP ==========
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❓ *Help Guide*\n\n"
        f"💰 *Pay ₹{PAYMENT_AMOUNT}*\n"
        f"📱 UPI: {os.getenv('UPI_ID')}\n\n"
        f"🤖 *After Cloning:*\n"
        f"✅ Start Bot - Run your bot\n"
        f"✅ Stop Bot - Stop your bot\n"
        f"✅ Edit Config - Change settings\n\n"
        f"⚙️ *Edit Options:*\n"
        f"🔑 Bot Token\n"
        f"📱 Bot Username\n"
        f"💳 UPI ID\n"
        f"💰 Payment Amount",
        parse_mode="Markdown"
    )

# ========== BUTTON HANDLER ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "clone_now":
        await clone_now(update, context)
    elif data == "my_clones":
        await my_clones(update, context)
    elif data.startswith("start_bot_"):
        await start_bot(update, context)
    elif data.startswith("stop_bot_"):
        await stop_bot(update, context)
    elif data.startswith("edit_bot_"):
        await edit_bot(update, context)
    elif data.startswith("edit_token_"):
        await edit_token(update, context)
    elif data.startswith("edit_username_"):
        await edit_username(update, context)
    elif data.startswith("edit_upi_"):
        await edit_upi(update, context)
    elif data.startswith("edit_amount_"):
        await edit_amount(update, context)
    elif data.startswith("view_config_"):
        await view_config(update, context)
    elif data == "check_payment":
        await check_payment(update, context)
    elif data == "check_status":
        await check_payment(update, context)
    elif data == "help":
        await help_command(update, context)
    elif data == "back":
        await start(update, context)

# ========== CONVERSATION ==========
conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(edit_token, pattern="^edit_token_"),
        CallbackQueryHandler(edit_username, pattern="^edit_username_"),
        CallbackQueryHandler(edit_upi, pattern="^edit_upi_"),
        CallbackQueryHandler(edit_amount, pattern="^edit_amount_"),
    ],
    states={
        EDIT_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_handler)],
        EDIT_BOT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_handler)],
        EDIT_UPI: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_handler)],
        EDIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_handler)],
    },
    fallbacks=[CommandHandler("start", start)]
)

# ========== MAIN ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv_handler)
    
    print(f"✅ Clone Bot Running: {BOT_USERNAME}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
