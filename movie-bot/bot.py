import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, MessageHandler

# ============ CONFIG ============
TOKEN = "8277340119:AAEwZFUHnlKggYNlBj-ZxGn0BtOJQtZdTmg"  # Replace with BotFather token
ADMIN_ID = 1461452255  # Replace with your Telegram user ID

# ====== Helpers to load/save data ======
def load_data():
    try:
        with open("movies.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open("movies.json", "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ====== Utility functions ======
def find_item(name):
    for item in data:
        if name.lower() in item["name"].lower():
            return item
    return None

# ====== Commands ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome!\n\n"
        "Send me a *movie/series/anime* name to get links.\n\n"
        "👉 Admin commands:\n"
        "   /addmovie, /addseries, /updateitem, /deleteitem"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    item = find_item(query)
    if not item:
        await update.message.reply_text("❌ Not found. Try another name.")
        return

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

    if "thumbnail" in item and item["thumbnail"]:
        try:
            await update.message.reply_photo(photo=item["thumbnail"], caption=text, parse_mode="Markdown")
        except:
            await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

# ====== Add movie/series/update ======
async def addmovie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    try:
        args = " ".join(context.args)
        parts = args.split("|")
        name = parts[0].strip()
        thumbnail = parts[1].strip()
        links = {q.strip(): l.strip() for p in parts[2:] if "=" in p for q, l in [p.split("=",1)]}
        new_item = {"name": name, "type": "movie", "thumbnail": thumbnail, "links": links}
        data.append(new_item)
        save_data(data)
        await update.message.reply_text(f"✅ Movie *{name}* added!", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ Usage:\n/addmovie Name | thumbnail | 480p=link | 720p=link")

async def addseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    try:
        args = " ".join(context.args)
        parts = args.split("|")
        name = parts[0].strip()
        thumbnail = parts[1].strip()
        episodes = {}
        for p in parts[2:]:
            if ":" in p:
                ep, qualities = p.split(":", 1)
                q_links = {q.strip(): l.strip() for ql in qualities.split(",") if "=" in ql for q, l in [ql.split("=",1)]}
                episodes[ep.strip()] = q_links
        new_item = {"name": name, "type": "series", "thumbnail": thumbnail, "episodes": episodes}
        data.append(new_item)
        save_data(data)
        await update.message.reply_text(f"✅ Series *{name}* added!", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ Usage:\n/addseries Name | thumbnail | S01E01:480p=link,720p=link")

async def updateitem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    try:
        args = " ".join(context.args)
        parts = args.split("|")
        name = parts[0].strip()
        item = find_item(name)
        if not item:
            await update.message.reply_text(f"❌ Item '{name}' not found.")
            return
        item["thumbnail"] = parts[1].strip()
        if item["type"] == "movie":
            for p in parts[2:]:
                if "=" in p:
                    q,l = p.split("=",1)
                    item["links"][q.strip()] = l.strip()
        else:
            for p in parts[2:]:
                if ":" in p:
                    ep, qualities = p.split(":",1)
                    q_links = {q.strip(): l.strip() for ql in qualities.split(",") if "=" in ql for q,l in [ql.split("=",1)]}
                    item["episodes"][ep.strip()] = q_links
        save_data(data)
        await update.message.reply_text(f"✅ Updated *{name}*!", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ Usage: /updateitem Name | thumbnail | 480p=newlink | S01E01:480p=newlink,...")

# ====== Delete with confirmation ======
CONFIRM_DELETE = range(1)

async def deleteitem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    name = " ".join(context.args).strip()
    item = find_item(name)
    if not item:
        await update.message.reply_text(f"❌ Item '{name}' not found.")
        return
    context.user_data["delete_item"] = item
    await update.message.reply_text(f"⚠️ Are you sure you want to delete *{item['name']}*? Reply YES to confirm.", parse_mode="Markdown")
    return CONFIRM_DELETE

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    item = context.user_data.get("delete_item")
    if not item:
        return ConversationHandler.END
    if text == "yes":
        data.remove(item)
        save_data(data)
        await update.message.reply_text(f"🗑️ Deleted *{item['name']}* successfully!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Deletion cancelled.")
    context.user_data.pop("delete_item", None)
    return ConversationHandler.END

# ====== Main ======
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addmovie", addmovie))
    app.add_handler(CommandHandler("addseries", addseries))
    app.add_handler(CommandHandler("updateitem", updateitem))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Delete conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("deleteitem", deleteitem)],
        states={CONFIRM_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete)]},
        fallbacks=[]
    )
    app.add_handler(conv_handler)

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
