import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============ CONFIG ============
TOKEN = "8277340119:AAEwZFUHnlKggYNlBj-ZxGn0BtOJQtZdTmg"  # Replace with BotFather token
ADMIN_ID = 1461452255  # Replace with your Telegram user ID (from @userinfobot)

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

# Search function
def find_item(name):
    for item in data:
        if name.lower() in item["name"].lower():
            return item
    return None

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome!\n\n"
        "Send me a *movie/series/anime* name to get links.\n\n"
        "👉 Admin can add with /additem"
    )

# Handle user search
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    item = find_item(query)

    if not item:
        await update.message.reply_text("❌ Not found. Try another name.")
        return

    if item["type"] == "movie":
        text = f"🎥 *{item['name']}* (Movie)\n\n"
        for quality, link in item["links"].items():
            text += f"🔗 {quality}: {link}\n"

    else:
        text = f"📺 *{item['name']}* ({item['type'].capitalize()})\n\n"
        for ep, links in item["episodes"].items():
            text += f"▶️ {ep}\n"
            for quality, link in links.items():
                text += f"   🔗 {quality}: {link}\n"
            text += "\n"

    if "thumbnail" in item and item["thumbnail"]:
        await update.message.reply_photo(photo=item["thumbnail"], caption=text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

# Admin command to add item
async def additem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    try:
        # Format:
        # /additem movie | Name | thumbnail | 480p=link | 720p=link
        # /additem webseries | Name | thumbnail | S01E01:480p=link,720p=link | S01E02:480p=link
        args = " ".join(context.args)
        parts = args.split("|")

        item_type = parts[0].strip().lower()
        name = parts[1].strip()
        thumbnail = parts[2].strip()

        new_item = {"name": name, "type": item_type, "thumbnail": thumbnail}

        if item_type == "movie":
            links = {}
            for p in parts[3:]:
                if "=" in p:
                    q, l = p.split("=", 1)
                    links[q.strip()] = l.strip()
            new_item["links"] = links

        else:  # series/anime/tv
            episodes = {}
            for p in parts[3:]:
                if ":" in p:
                    ep, qualities = p.split(":", 1)
                    q_links = {}
                    for ql in qualities.split(","):
                        if "=" in ql:
                            q, l = ql.split("=", 1)
                            q_links[q.strip()] = l.strip()
                    episodes[ep.strip()] = q_links
            new_item["episodes"] = episodes

        data.append(new_item)
        save_data(data)

        await update.message.reply_text(f"✅ Added *{name}* successfully!", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Usage:\n"
            "/additem movie | Name | thumbnail | 480p=link | 720p=link\n"
            "/additem webseries | Name | thumbnail | S01E01:480p=link,720p=link | S01E02:480p=link"
        )

# Main runner
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("additem", additem))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
