import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, OWNER_ID, ADMIN_IDS
from database import (init_db, add_stock, generate_key, get_keys_by_user, 
                      get_all_keys, get_all_stock, get_stock_by_type, get_logs, 
                      delete_all_stock, get_all_key_codes)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_data = {}

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    return user_id in ADMIN_IDS or is_owner(user_id)

def has_access(user_id):
    return is_admin(user_id)

# ============ TIME TYPES ============
TYPE_INFO = {
    '1_hr': {'label': '1 Hour', 'emoji': '⏰'},
    '6_hr': {'label': '6 Hours', 'emoji': '⏰'},
    '1_day': {'label': '1 Day', 'emoji': '📅'},
    '7_day': {'label': '7 Days', 'emoji': '📅'},
    '14_day': {'label': '14 Days', 'emoji': '📅'},
    '30_day': {'label': '30 Days', 'emoji': '📅'},
}

def get_type_keyboard(action):
    keyboard = []
    for stock_type, info in TYPE_INFO.items():
        qty = get_stock_by_type(stock_type)
        button_text = f"{info['emoji']} {info['label']} – {qty} left"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"{action}_{stock_type}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

# ============ MAIN MENU ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not has_access(user_id):
        await update.message.reply_text("❌ Access Denied!")
        return
    
    if is_owner(user_id):
        keyboard = [
            [InlineKeyboardButton("➕ Add Key", callback_data="add_key")],
            [InlineKeyboardButton("🔑 Get Key", callback_data="get_key")],
            [InlineKeyboardButton("📦 View Stock", callback_data="view")],
            [InlineKeyboardButton("🔑 My Keys", callback_data="my_keys")],
            [InlineKeyboardButton("📜 All Keys", callback_data="all_keys")],
            [InlineKeyboardButton("📜 Logs", callback_data="logs")],
        ]
        await update.message.reply_text(
            "👑 Owner Panel\nSelect:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("🔑 Get Key", callback_data="get_key")],
            [InlineKeyboardButton("🔑 My Keys", callback_data="my_keys")],
            [InlineKeyboardButton("📦 View Stock", callback_data="view")],
        ]
        await update.message.reply_text(
            "🔧 Admin Panel\nGet Key:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ============ BUTTON HANDLER ============
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if not has_access(user_id):
        await query.edit_message_text("❌ Access Denied!")
        return
    
    if data == "back":
        if user_id in user_data:
            del user_data[user_id]
        await start_command(update, context, query)
        return
    
    # ============ VIEW STOCK ============
    if data == "view":
        await view_stock(query)
        return
    
    # ============ MY KEYS ============
    if data == "my_keys":
        await view_my_keys(query, user_id)
        return
    
    # ============ ALL KEYS ============
    if data == "all_keys":
        if not is_owner(user_id):
            await query.edit_message_text("❌ Sirf owner!")
            return
        await view_all_keys(query)
        return
    
    # ============ LOGS ============
    if data == "logs":
        if not is_owner(user_id):
            await query.edit_message_text("❌ Sirf owner!")
            return
        await view_logs(query)
        return
    
    # ============ GET KEY ============
    if data == "get_key":
        await query.edit_message_text(
            "🔑 Select Time:",
            reply_markup=get_type_keyboard("get")
        )
        return
    
    # ============ GET KEY - TYPE SELECTED ============
    if data.startswith("get_"):
        stock_type = data.split("_", 1)[1]
        
        key_code, msg = generate_key(stock_type, OWNER_ID, user_id)
        
        if key_code:
            remaining = get_stock_by_type(stock_type)
            info = TYPE_INFO[stock_type]
            
            await query.edit_message_text(
                f"✅ Key Get!\n\n"
                f"⏰ {info['label']}\n"
                f"🔑 {key_code}\n"
                f"📉 Left: {remaining}\n\n"
                f"🎉 Key aa gayi!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Get More", callback_data="get_key")],
                    [InlineKeyboardButton("🔑 My Keys", callback_data="my_keys")]
                ])
            )
        else:
            await query.edit_message_text(msg)
        return
    
    # ============ ADD KEY ============
    if data == "add_key":
        if not is_owner(user_id):
            await query.edit_message_text("❌ Sirf owner!")
            return
        
        await query.edit_message_text(
            "➕ Add Key\n\nSelect Time:",
            reply_markup=get_type_keyboard("add")
        )
        return
    
    # ============ ADD KEY - TYPE SELECTED ============
    if data.startswith("add_"):
        stock_type = data.split("_", 1)[1]
        user_data[user_id] = {"stock_type": stock_type}
        
        info = TYPE_INFO[stock_type]
        await query.edit_message_text(
            f"➕ Add Key\n\n"
            f"⏰ {info['label']}\n\n"
            f"Enter Key Code:"
        )
        return

# ============ START COMMAND HELPER ============
async def start_command(update, context, query=None):
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else query.from_user.id
    
    if is_owner(user_id):
        keyboard = [
            [InlineKeyboardButton("➕ Add Key", callback_data="add_key")],
            [InlineKeyboardButton("🔑 Get Key", callback_data="get_key")],
            [InlineKeyboardButton("📦 View Stock", callback_data="view")],
            [InlineKeyboardButton("🔑 My Keys", callback_data="my_keys")],
            [InlineKeyboardButton("📜 All Keys", callback_data="all_keys")],
            [InlineKeyboardButton("📜 Logs", callback_data="logs")],
        ]
        msg = "👑 Owner Panel\nSelect:"
    else:
        keyboard = [
            [InlineKeyboardButton("🔑 Get Key", callback_data="get_key")],
            [InlineKeyboardButton("🔑 My Keys", callback_data="my_keys")],
            [InlineKeyboardButton("📦 View Stock", callback_data="view")],
        ]
        msg = "🔧 Admin Panel\nGet Key:"
    
    if query:
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ============ VIEW STOCK ============
async def view_stock(query):
    msg = "📦 Stock:\n\n"
    has_stock = False
    
    for stock_type, info in TYPE_INFO.items():
        qty = get_stock_by_type(stock_type)
        if qty > 0:
            msg += f"{info['emoji']} {info['label']} : {qty} left\n"
            has_stock = True
    
    if not has_stock:
        msg = "📦 Stock Empty!"
    
    await query.edit_message_text(msg)

# ============ VIEW KEYS ============
async def view_my_keys(query, user_id):
    keys = get_keys_by_user(user_id)
    
    if not keys:
        await query.edit_message_text("🔑 No keys!")
        return
    
    msg = "🔑 Your Keys:\n\n"
    for key in keys:
        status_emoji = "✅" if key[2] == "claimed" else "🟢"
        info = TYPE_INFO.get(key[1], {'label': key[1]})
        msg += f"{status_emoji} {key[0]}\n"
        msg += f"   ⏰ {info['label']}\n"
        msg += f"   🕐 {key[3]}\n\n"
    
    await query.edit_message_text(msg)

async def view_all_keys(query):
    keys = get_all_keys()
    
    if not keys:
        await query.edit_message_text("🔑 No keys!")
        return
    
    msg = "🔑 All Keys:\n\n"
    for key in keys:
        status = "✅" if key[3] == "claimed" else "🟢"
        info = TYPE_INFO.get(key[1], {'label': key[1]})
        msg += f"{key[0]} | {status}\n"
        msg += f"   ⏰ {info['label']}\n"
        msg += f"   👤 For: {key[2]}\n"
        msg += f"   🕐 {key[4]}\n\n"
    
    await query.edit_message_text(msg)

# ============ VIEW LOGS ============
async def view_logs(query):
    logs = get_logs(20)
    msg = "📜 Logs:\n\n"
    for log in logs:
        msg += f"🕐 {log[4]} | {log[1]} | {log[2]}\n"
    await query.edit_message_text(msg)

# ============ MESSAGE HANDLER ============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not has_access(user_id):
        await update.message.reply_text("❌ Access Denied!")
        return
    
    if user_id not in user_data:
        await update.message.reply_text("⚠️ /start karo aur option select karo.")
        return
    
    stock_type = user_data[user_id].get("stock_type")
    
    if not stock_type:
        await update.message.reply_text("❌ Pehle time select karo!")
        return
    
    key_code = text
    info = TYPE_INFO[stock_type]
    
    # Check duplicate
    all_keys = get_all_key_codes()
    for k, _ in all_keys:
        if k == key_code:
            await update.message.reply_text(f"❌ {key_code} already exists!")
            return
    
    add_stock(key_code, stock_type, user_id)
    total = get_stock_by_type(stock_type)
    
    await update.message.reply_text(
        f"✅ Key Added!\n\n"
        f"🔑 {key_code}\n"
        f"⏰ {info['label']}\n"
        f"📈 Total: {total}\n\n"
        f"✅ Add ho gaya!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add More", callback_data="add_key")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ])
    )
    
    del user_data[user_id]

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    await update.message.reply_text("❌ Cancelled!")

# ============ MAIN ============
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()