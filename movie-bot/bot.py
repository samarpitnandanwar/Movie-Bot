import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============ CONFIG ============
TOKEN = "8277340119:AAEwZFUHnlKggYNlBj-ZxGn0BtOJQtZdTmg"  # Replace with BotFather token
ADMIN_ID = 1461452255  # Replace with your Telegram user ID (from @userinfobot)

# Load movie data
def load_movies():
    try:
        with open("movies.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_movies(movies):
    with open("movies.json", "w") as f:
        json.dump(movies, f, indent=2)

movies = load_movies()

# Search function
def find_movie(movie_name):
    for movie in movies:
        if movie_name.lower() in movie["name"].lower():
            return movie
    return None

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Welcome! Send me a movie name to get download links.")

# Handle normal movie search
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    movie = find_movie(query)

    if movie:
        reply = f"🎥 *{movie['name']}* Links:\n"
        for quality, link in movie["links"].items():
            reply += f"🔗 {quality}: {link}\n"
        await update.message.reply_text(reply, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Movie not found. Try another name.")

# Admin command to add movies
async def addmovie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to add movies.")
        return

    try:
        # Expected format: /addmovie Name | 480p=link | 720p=link | 1080p=link
        text = " ".join(context.args)
        parts = text.split("|")
        name = parts[0].strip()

        links = {}
        for part in parts[1:]:
            if "=" in part:
                quality, link = part.split("=", 1)
                links[quality.strip()] = link.strip()

        new_movie = {"name": name, "links": links}
        movies.append(new_movie)
        save_movies(movies)

        await update.message.reply_text(f"✅ Movie *{name}* added successfully!", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("⚠️ Usage: /addmovie Name | 480p=link | 720p=link | 1080p=link")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addmovie", addmovie))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
