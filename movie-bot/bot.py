import json
import random
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
ads_list = load_data("ads.json")  # Stores ads

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
        "   /addmovie, /addseries, /updateitem, /deleteitem\n"
        "   /add_ads, /remove_ads"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    if "thumbnail" in item and item["thumbnail"]:
        try:
            await update.message.reply_photo(photo=item["thumbnail"], caption=text, parse_mode="Markdown")
        except:
            await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

# ====== Add ads (admin) ======
async def add_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    try:
        args = " ".join(context.args)
        parts = args.split("|")
        ad_type = parts[0].strip().lower()

        if ad_type == "text":
            content = parts[1].strip()
            ads_list.append({"type": "text", "content": content})
            save_data("ads.json", ads_list)
            await update.message.reply_text("✅ Text ad added successfully!")

        elif ad_type == "image":
            url = parts[1].strip()
            caption = parts[2].strip() if len(parts) > 2 else ""
            ads_list.append({"type": "image", "url": url, "caption": caption})
            save_data("ads.json", ads_list)
            await update.message.reply_text("✅ Image ad added successfully!")

        else:
            await update.message.reply_text("❌ Invalid ad type. Use `text` or `image`.")

    except:
        await update.message.reply_text(
            "⚠️ Usage:\n"
            "/add_ads text | Your ad message\n"
            "/add_ads image | Image_URL | Optional caption"
        )

# ====== Remove ads (admin) ======
CONFIRM_REMOVE_AD = range(1)

async def remove_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    if not ads_list:
        await update.message.reply_text("⚠️ No ads to remove.")
        return
    # Show ads with index
    msg = "🗑️ Current Ads:\n"
    for idx, ad in enumerate(ads_list, start=1):
        if ad["type"] == "text":
            msg += f"{idx}. [Text] {ad['content']}\n"
        else:
            msg += f"{idx}. [Image] {ad['url']} - {ad.get('caption', '')}\n"
    msg += "\nReply with the number of the ad to remove."
    await update.message.reply_text(msg)
    return CONFIRM_REMOVE_AD

async def confirm_remove_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        idx = int(text) - 1
        if 0 <= idx < len(ads_list):
            removed = ads_list.pop(idx)
            save_data("ads.json", ads_list)
            await update.message.reply_text(f"🗑️ Removed ad ({removed['type']}) successfully!")
        else:
            await update.message.reply_text("❌ Invalid number.")
    except:
        await update.message.reply_text("❌ Please enter a valid number.")
    return ConversationHandler.END

# ====== Movie/Series/Add/Update/Delete commands (unchanged) ======
# Copy your existing addmovie, addseries, updateitem, deleteitem, confirm_delete here

# ====== Main ======
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addmovie", addmovie))
    app.add_handler(CommandHandler("addseries", addseries))
    app.add_handler(CommandHandler("updateitem", updateitem))
    app.add_handler(CommandHandler("add_ads", add_ads))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    conv_handler_delete = ConversationHandler(
        entry_points=[CommandHandler("deleteitem", deleteitem)],
        states={CONFIRM_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete)]},
        fallbacks=[]
    )
    app.add_handler(conv_handler_delete)

    conv_handler_ads = ConversationHandler(
        entry_points=[CommandHandler("remove_ads", remove_ads)],
        states={CONFIRM_REMOVE_AD: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_remove_ad)]},
        fallbacks=[]
    )
    app.add_handler(conv_handler_ads)

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
