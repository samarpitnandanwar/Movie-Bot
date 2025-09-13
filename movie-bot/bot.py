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

    await update.message.reply_text(
        f"{sub_msg}\n\n"
        "🎬 Send me a *movie/series/anime* name to get links.\n\n"
        "👉 Admin commands:\n"
        "   /addmovie, /addseries, /updateitem, /deleteitem\n"
        "   /add_ads, /remove_ads, /subscribers, /broadcast\n"
        "👉 User command:\n"
        "   /list (see all available movies & series)",
        parse_mode="Markdown"
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    item = find_item(query)
    if not item:
        await update.message.reply_text("❌ Not found. Try another name.")
        return

    # ✅ Always display ad before result
    ad = get_next_ad()
    if ad:
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
        save_data("movies.json", data)
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
        save_data("movies.json", data)
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
        save_data("movies.json", data)
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
        save_data("movies.json", data)
        await update.message.reply_text(f"🗑️ Deleted *{item['name']}* successfully!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Deletion cancelled.")
    context.user_data.pop("delete_item", None)
    return ConversationHandler.END

# ====== Add ads (admin) ======
async def add_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    try:
        args = " ".join(context.args)
        parts = args.split("|")
        ad_type = parts[0].strip().lower()

        ads_list = load_data("ads.json")

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
    ads_list = load_data("ads.json")
    if not ads_list:
        await update.message.reply_text("⚠️ No ads to remove.")
        return
    msg = "🗑️ Current Ads:\n"
    for idx, ad in enumerate(ads_list, start=1):
        if ad["type"] == "text":
            msg += f"{idx}. [Text] {ad['content']}\n"
        else:
            msg += f"{idx}. [Image] {ad['url']} - {ad.get('caption', '')}\n"
    msg += "\nReply with the number of the ad to remove."
    context.user_data["ads_list"] = ads_list
    await update.message.reply_text(msg)
    return CONFIRM_REMOVE_AD

async def confirm_remove_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    ads_list = context.user_data.get("ads_list", [])
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

# ====== Broadcast (admin only) ======
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    try:
        message = " ".join(context.args)
        count = 0
        for user_id in subscribers:
            try:
                await context.bot.send_message(chat_id=user_id, text=message)
                count += 1
            except:
                pass
        await update.message.reply_text(f"✅ Broadcast sent to {count} subscribers.")
    except:
        await update.message.reply_text("⚠️ Usage: /broadcast Your message here")

# ====== Subscribers list for admin view ======
async def show_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    if not subscribers:
        await update.message.reply_text("⚠️ No subscribers yet.")
        return
    
    subs_list = "\n".join([f"{idx+1}. {uid}" for idx, uid in enumerate(subscribers)])
    await update.message.reply_text(
        f"📊 Total Subscribers: {len(subscribers)}\n\n"
        f"📝 Subscriber IDs:\n{subs_list}"
    )

async def addseries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    try:
        args = " ".join(context.args)
        parts = args.split("|")
        name = parts[0].strip()
        thumbnail = parts[1].strip()

        # detect if it's season-based (contains Season)
        if any("Season" in p for p in parts[2:]):
            seasons = {}
            for p in parts[2:]:
                if "=" in p:
                    season_name, link = p.split("=", 1)
                    seasons[season_name.strip()] = link.strip()
            new_item = {"name": name, "type": "series", "thumbnail": thumbnail, "seasons": seasons}
        else:
            episodes = {}
            for p in parts[2:]:
                if ":" in p:
                    ep, qualities = p.split(":", 1)
                    q_links = {q.strip(): l.strip() for ql in qualities.split(",") if "=" in ql for q, l in [ql.split("=",1)]}
                    episodes[ep.strip()] = q_links
            new_item = {"name": name, "type": "series", "thumbnail": thumbnail, "episodes": episodes}

        data.append(new_item)
        save_data("movies.json", data)
        await update.message.reply_text(f"✅ Series *{name}* added!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(
            "⚠️ Usage:\n"
            "/addseries Name | thumbnail | S01E01:480p=link,720p=link\n"
            "OR\n"
            "/addseries Name | thumbnail | Season 1=ziplink | Season 2=ziplink"
        )


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

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
