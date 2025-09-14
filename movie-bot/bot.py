import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes,
    ConversationHandler, CallbackQueryHandler
)

# ============ CONFIG ============
TOKEN = "8277340119:AAEwZFUHnlKggYNlBj-ZxGn0BtOJQtZdTmg"
ADMIN_ID = 1461452255

# ====== Helpers to load/save data ======
def load_data(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

data = load_data("movies.json")

# ====== Subscribers ======
SUBSCRIBERS_FILE = "subscribers.json"
subscribers = set(load_data(SUBSCRIBERS_FILE))  # store as set for uniqueness

# ====== Ad rotation index ======
ad_index = 0

# ====== Utility functions ======
def find_item(name):
    for item in data:
        if name.lower() in item["name"].lower():
            return item
    return None

def get_next_ad():
    """Reload ads.json each time and cycle them in order"""
    global ad_index
    ads = load_data("ads.json")
    if not ads:
        return None
    ad = ads[ad_index % len(ads)]
    ad_index += 1
    return ad

# ====== Commands ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    new_subscriber = False

    if user_id not in subscribers:
        subscribers.add(user_id)
        save_data(SUBSCRIBERS_FILE, list(subscribers))
        new_subscriber = True

    total_subs = len(subscribers)

    funny_msgs = [
        "🍿 Grab some popcorn, you're in!",
        "😎 Cool beans! You made it!",
        "🎉 Party time! You're officially awesome!",
        "🛸 Welcome aboard, space traveler!",
        "🐱‍👤 Ninja vibes activated! Welcome!",
        "💃 Shake it off! You're a star subscriber!",
        "🥳 Hooray! Another legend joins the club!"
    ]
    
    if new_subscriber:
        sub_msg = f"🎊 Hahaha! You're subscriber number *{total_subs}* 🤣\n" \
                  f"{random.choice(funny_msgs)}"
    else:
        sub_msg = f"👋 Welcome back! You're already part of our *{total_subs}* subscribers community 😄"

    # 🎯 User menu buttons
    keyboard = [
        [InlineKeyboardButton("📋 Show Library", callback_data="list")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{sub_msg}\n\n🎬 Send me a *movie/series/anime* name to get links.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data:
        await update.message.reply_text("⚠️ No movies or series added yet.")
        return

    movies = [item["name"] for item in data if item["type"] == "movie"]
    series = [item["name"] for item in data if item["type"] != "movie"]

    msg = "📋 *Available Library:*\n\n"
    if movies:
        msg += "🎥 *Movies:*\n"
        for m in movies:
            msg += f"   • {m}\n"
        msg += "\n"
    if series:
        msg += "📺 *Series/Anime/TV Shows:*\n"
        for s in series:
            msg += f"   • {s}\n"
        msg += "\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# ====== Admin Menu ======
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return

    keyboard = [
        [InlineKeyboardButton("🎥 Add Movie", callback_data="addmovie")],
        [InlineKeyboardButton("📺 Add Series", callback_data="addseries")],
        [InlineKeyboardButton("✏️ Update Item", callback_data="updateitem")],
        [InlineKeyboardButton("🗑️ Delete Item", callback_data="deleteitem")],
        [InlineKeyboardButton("➕ Add Ad", callback_data="add_ads")],
        [InlineKeyboardButton("➖ Remove Ad", callback_data="remove_ads")],
        [InlineKeyboardButton("👥 Subscribers", callback_data="subscribers")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("⚙️ *Admin Panel* – Choose an action:", parse_mode="Markdown", reply_markup=reply_markup)

# ====== Handle button clicks ======
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd = query.data

    if cmd == "list":
        await list_items(update, context)
    elif cmd == "admin":
        await admin(update, context)
    elif cmd == "addmovie":
        await query.edit_message_text("ℹ️ Use manually:\n`/addmovie Name | thumbnail | 480p=link | 720p=link`", parse_mode="Markdown")
    elif cmd == "addseries":
        await query.edit_message_text("ℹ️ Use manually:\n`/addseries Name | thumbnail | S01E01:480p=link,720p=link`", parse_mode="Markdown")
    elif cmd == "updateitem":
        await query.edit_message_text("ℹ️ Use manually:\n`/updateitem Name | thumbnail | 480p=newlink`", parse_mode="Markdown")
    elif cmd == "deleteitem":
        await query.edit_message_text("ℹ️ Use manually:\n`/deleteitem Name`", parse_mode="Markdown")
    elif cmd == "add_ads":
        await query.edit_message_text("ℹ️ Use manually:\n`/add_ads text | msg` or `/add_ads image | url | caption`", parse_mode="Markdown")
    elif cmd == "remove_ads":
        await query.edit_message_text("ℹ️ Use manually:\n`/remove_ads`", parse_mode="Markdown")
    elif cmd == "subscribers":
        await show_subscribers(update, context)
    elif cmd == "broadcast":
        await query.edit_message_text("ℹ️ Use manually:\n`/broadcast Your message`", parse_mode="Markdown")

# (keep your handle_message, addmovie, addseries, updateitem, deleteitem, ads functions, broadcast, etc. EXACTLY the same as before)

# ====== Main ======
def main():
    app = Application.builder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_items))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("addmovie", addmovie))
    app.add_handler(CommandHandler("addseries", addseries))
    app.add_handler(CommandHandler("updateitem", updateitem))
    app.add_handler(CommandHandler("add_ads", add_ads))
    app.add_handler(CommandHandler("remove_ads", remove_ads))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("subscribers", show_subscribers))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Delete conversation
    conv_delete = ConversationHandler(
        entry_points=[CommandHandler("deleteitem", deleteitem)],
        states={CONFIRM_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete)]},
        fallbacks=[]
    )
    app.add_handler(conv_delete)

    # Remove ad conversation
    conv_remove_ads = ConversationHandler(
        entry_points=[CommandHandler("remove_ads", remove_ads)],
        states={CONFIRM_REMOVE_AD: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_remove_ad)]},
        fallbacks=[]
    )
    app.add_handler(conv_remove_ads)

    # Button handler
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
