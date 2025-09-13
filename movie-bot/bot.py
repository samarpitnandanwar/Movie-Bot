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

    # --- Send item info ---
    if item["type"] == "movie":
        text = f"🎥 *{item['name']}* (Movie)\n\n"
        for quality, link in item.get("links", {}).items():
            text += f"🔗 {quality}: {link}\n"

    elif "seasons" in item:  # 📦 Show season-based links
        text = f"📺 *{item['name']}* (Series – Full Seasons)\n\n"
        for season, link in item.get("seasons", {}).items():
            text += f"📦 {season}: {link}\n"

    elif "episodes" in item:  # 📺 Episode-based series
        text = f"📺 *{item['name']}* ({item['type'].capitalize()})\n\n"
        for ep, links in item.get("episodes", {}).items():
            text += f"▶️ {ep}\n"
            for quality, link in links.items():
                text += f"   🔗 {quality}: {link}\n"
            text += "\n"

    else:
        text = f"⚠️ No links available for *{item['name']}*."

    # --- Send thumbnail if available ---
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

        # Detect season-based links
        seasons = {}
        episodes = {}
        for p in parts[2:]:
            if "=" in p and "Season" in p:
                season_name, link = p.split("=",1)
                seasons[season_name.strip()] = link.strip()
            elif ":" in p:
                ep, qualities = p.split(":",1)
                q_links = {q.strip(): l.strip() for ql in qualities.split(",") if "=" in ql for q, l in [ql.split("=",1)]}
                episodes[ep.strip()] = q_links

        new_item = {"name": name, "type": "series", "thumbnail": thumbnail}
        if seasons:
            new_item["seasons"] = seasons
        if episodes:
            new_item["episodes"] = episodes

        data.append(new_item)
        save_data("movies.json", data)
        await update.message.reply_text(f"✅ Series *{name}* added!", parse_mode="Markdown")
    except:
        await update.message.reply_text(
            "⚠️ Usage:\n/addseries Name | thumbnail | S01E01:480p=link,720p=link\n"
            "OR\n/addseries Name | thumbnail | Season 1=ziplink | Season 2=ziplink"
        )

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
                if "=" in p and "Season" in p:
                    season_name, link = p.split("=",1)
                    if "seasons" not in item:
                        item["seasons"] = {}
                    item["seasons"][season_name.strip()] = link.strip()
                elif ":" in p:
                    ep, qualities = p.split(":",1)
                    q_links = {q.strip(): l.strip() for ql in qualities.split(",") if "=" in ql for q,l in [ql.split("=",1)]}
                    if "episodes" not in item:
                        item["episodes"] = {}
                    item["episodes"][ep.strip()] = q_links

        save_data("movies.json", data)
        await update.message.reply_text(f"✅ Updated *{name}*!", parse_mode="Markdown")
    except:
        await update.message.reply_text(
            "⚠️ Usage: /updateitem Name | thumbnail | 480p=newlink | S01E01:480p=newlink | Season 1=ziplink"
        )

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
        await update.message.reply_text(f"🗑️ Deleted *{item['name']}*
