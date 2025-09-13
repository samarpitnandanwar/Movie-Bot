import json
import random
import time
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes,
    ConversationHandler
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
ads_list = load_data("ads.json")

# ====== Track users ======
users = load_data("users.json")  # {"total": [], "active": {}}
if not users:
    users = {"total": [], "active": {}}

def save_users():
    save_data("users.json", users)

def update_user_activity(user_id):
    now = int(time.time())
    if user_id not in users["total"]:
        users["total"].append(user_id)
    users["active"][str(user_id)] = now
    save_users()

def get_user_stats():
    now = int(time.time())
    active_cutoff = now - 300  # active if used in last 5 minutes
    active_users = [uid for uid, ts in users["active"].items() if ts >= active_cutoff]
    return len(users["total"]), len(active_users)

# ====== Utility functions ======
def find_item(name):
    for item in data:
        if name.lower() in item["name"].lower():
            return item
    return None

# ====== Commands ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user_activity(update.message.from_user.id)
    total, active = get_user_stats()
    await update.message.reply_text(
        f"🎬 Welcome!\n\n"
        f"Send me a *movie/series/anime* name to get links.\n\n"
        f"👉 Admin commands:\n"
        f"   /addmovie, /addseries, /updateitem, /deleteitem\n"
        f"   /add_ads, /remove_ads\n"
        f"👉 User command:\n"
        f"   /list (see all available movies & series)\n\n"
        f"👥 Users: {total} total | 🔴 {active} live"
    )

async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user_activity(update.message.from_user.id)
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

    total, active = get_user_stats()
    msg += f"\n👥 *Users:* {total} total | 🔴 {active} live"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user_activity(update.message.from_user.id)
    query = update.message.text.strip()
    item = find_item(query)
    if not item:
        await update.message.reply_text("❌ Not found. Try another name.")
        return

    # Display random ad (30% chance)
    if ads_list and random.random() < 0.3:
        ad = random.choice(ads_list)
        if ad["type"] == "text":
            await update.message.reply_text(ad["content"])
        elif ad["type"] == "image":
            try:
                await update.message.reply_photo(photo=ad["url"], caption=ad.get("caption", ""))
            except:
                pass

    # Send item info
    if item["type"] == "movie":
        text = f"🎥 *{item['name']}* (Movie)\n\n"
        for quality, link in item.get("links", {}).items():
            text += f"🔗 {quality}: {link}\n"
    else:
        text = f"📺 *{item['name']}* ({item['type'].capitalize()})\n\n"
        for ep, links in item.get("episodes", {}).items():
            text += f"▶️ {ep}\n"
            for quality, link in links.items():
                text += f"   🔗 {quality}: {link}\n"
            text += "\n"

    total, active = get_user_stats()
    text += f"\n👥 *Users:* {total} total | 🔴 {active} live"

    if "thumbnail" in item and item["thumbnail"]:
        try:
            await update.message.reply_photo(photo=item["thumbnail"], caption=text, parse_mode="Markdown")
        except:
            await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

# ====== (Rest of your add/update/delete/ads functions stay unchanged) ======

# ====== Main ======
def main():
    app = Application.builder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_items))
    app.add_handler(CommandHandler("addmovie", addmovie))
    app.add_handler(CommandHandler("addseries", addseries))
    app.add_handler(CommandHandler("updateitem", updateitem))
    app.add_handler(CommandHandler("add_ads", add_ads))
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

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
