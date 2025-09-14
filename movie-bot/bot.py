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
subscribers = set(load_data(SUBSCRIBERS_FILE))

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
        sub_msg = f"🎊 You're subscriber number *{total_subs}* 🎉\n{random.choice(funny_msgs)}"
    else:
        sub_msg = f"👋 Welcome back! You're part of our *{total_subs}* subscribers community 😄"

    keyboard = [[InlineKeyboardButton("📋 Show Library", callback_data="list")]]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin")])

    await update.message.reply_text(
        f"{sub_msg}\n\n🎬 Send me a *movie/series/anime* name to get links.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
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

# ====== Admin Functions ======
async def addmovie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")

    try:
        text = update.message.text.replace("/addmovie ", "")
        name, thumb, *links = [p.strip() for p in text.split("|")]
        qualities = {l.split("=")[0]: l.split("=")[1] for l in links}

        data.append({"type": "movie", "name": name, "thumbnail": thumb, "links": qualities})
        save_data("movies.json", data)
        await update.message.reply_text(f"✅ Movie *{name}* added!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}\nUsage:\n`/addmovie Name | thumb | 480p=link | 720p=link`", parse_mode="Markdown")

async def addseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")

    try:
        text = update.message.text.replace("/addseries ", "")
        name, thumb, *episodes = [p.strip() for p in text.split("|")]
        episodes_dict = {}
        for ep in episodes:
            ep_name, links_str = ep.split(":")
            links = {l.split("=")[0]: l.split("=")[1] for l in links_str.split(",")}
            episodes_dict[ep_name] = links

        data.append({"type": "series", "name": name, "thumbnail": thumb, "episodes": episodes_dict})
        save_data("movies.json", data)
        await update.message.reply_text(f"✅ Series *{name}* added!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}\nUsage:\n`/addseries Name | thumb | S01E01:480p=link,720p=link`", parse_mode="Markdown")

async def updateitem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    await update.message.reply_text("⚠️ Update logic here (similar to add).")

async def deleteitem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    await update.message.reply_text("⚠️ Delete logic here.")

async def add_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")

    try:
        text = update.message.text.replace("/add_ads ", "")
        parts = [p.strip() for p in text.split("|")]

        ads = load_data("ads.json")
        if parts[0] == "text":
            ads.append({"type": "text", "content": parts[1]})
        elif parts[0] == "image":
            ads.append({"type": "image", "url": parts[1], "caption": parts[2]})

        save_data("ads.json", ads)
        await update.message.reply_text("✅ Ad added!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

async def remove_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    save_data("ads.json", [])
    await update.message.reply_text("✅ All ads removed!")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    msg = update.message.text.replace("/broadcast ", "")
    for uid in subscribers:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
        except:
            pass
    await update.message.reply_text("✅ Broadcast sent!")

async def show_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👥 Total subscribers: {len(subscribers)}")

# ====== Handle Search ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    item = find_item(query)

    if not item:
        return await update.message.reply_text("❌ Not found.")

    if item["type"] == "movie":
        msg = f"🎥 *{item['name']}*\n"
        for q, link in item["links"].items():
            msg += f"🔗 {q}: {link}\n"
        await update.message.reply_photo(item["thumbnail"], caption=msg, parse_mode="Markdown")
    else:
        msg = f"📺 *{item['name']}*\n"
        for ep, links in item["episodes"].items():
            msg += f"\n▶️ {ep}\n"
            for q, link in links.items():
                msg += f"   {q}: {link}\n"
        await update.message.reply_photo(item["thumbnail"], caption=msg, parse_mode="Markdown")

    # Show ad after search
    ad = get_next_ad()
    if ad:
        if ad["type"] == "text":
            await update.message.reply_text(f"📢 {ad['content']}")
        elif ad["type"] == "image":
            await update.message.reply_photo(photo=ad["url"], caption=f"📢 {ad['caption']}")

# ====== Main ======
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_items))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("addmovie", addmovie))
    app.add_handler(CommandHandler("addseries", addseries))
    app.add_handler(CommandHandler("updateitem", updateitem))
    app.add_handler(CommandHandler("deleteitem", deleteitem))
    app.add_handler(CommandHandler("add_ads", add_ads))
    app.add_handler(CommandHandler("remove_ads", remove_ads))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("subscribers", show_subscribers))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is running...")
    app.run_polling()

# ====== Button handler ======
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd = query.data

    if cmd == "list":
        await list_items(update, context)
    elif cmd == "admin":
        await admin(update, context)
    elif cmd == "addmovie":
        await query.edit_message_text("ℹ️ Use `/addmovie Name | thumb | 480p=link | 720p=link`")
    elif cmd == "addseries":
        await query.edit_message_text("ℹ️ Use `/addseries Name | thumb | S01E01:480p=link,720p=link`")
    elif cmd == "updateitem":
        await query.edit_message_text("ℹ️ Use `/updateitem Name | thumb | 480p=newlink`")
    elif cmd == "deleteitem":
        await query.edit_message_text("ℹ️ Use `/deleteitem Name`")
    elif cmd == "add_ads":
        await query.edit_message_text("ℹ️ Use `/add_ads text | msg` or `/add_ads image | url | caption`")
    elif cmd == "remove_ads":
        await query.edit_message_text("ℹ️ Use `/remove_ads`")
    elif cmd == "subscribers":
        await show_subscribers(update, context)
    elif cmd == "broadcast":
        await query.edit_message_text("ℹ️ Use `/broadcast Your message`")

if __name__ == "__main__":
    main()
