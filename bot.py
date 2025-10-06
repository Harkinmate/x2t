import os
import json
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import snscrape.modules.twitter as sntwitter
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CONFIG_FILE = "config.json"

# Load or create config
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {"channel": "", "twitters": [], "last_tweets": {}}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

bot = Bot(token=TELEGRAM_TOKEN)

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# ----- Telegram Commands -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot is online!\nUse /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/setchannel @channelname - Set your Telegram channel\n"
        "/addtwitter username - Track a Twitter account\n"
        "/removetwitter username - Remove tracked Twitter account\n"
        "/listtwitters - List all tracked accounts\n"
        "/fetch - Manually fetch latest tweets\n"
        "/status - Show bot status"
    )

async def setchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /setchannel @channelname")
        return
    config["channel"] = context.args[0]
    save_config()
    await update.message.reply_text(f"✅ Channel set to {context.args[0]}")

async def addtwitter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /addtwitter username")
        return
    username = context.args[0].lstrip("@")
    if username not in config["twitters"]:
        config["twitters"].append(username)
        save_config()
        await update.message.reply_text(f"✅ Added Twitter account: {username}")
    else:
        await update.message.reply_text("⚠️ Twitter account already tracked.")

async def removetwitter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /removetwitter username")
        return
    username = context.args[0].lstrip("@")
    if username in config["twitters"]:
        config["twitters"].remove(username)
        config["last_tweets"].pop(username, None)
        save_config()
        await update.message.reply_text(f"✅ Removed Twitter account: {username}")
    else:
        await update.message.reply_text("⚠️ Twitter account not found.")

async def listtwitters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if config["twitters"]:
        msg = "📌 Tracked Twitter accounts:\n" + "\n".join(config["twitters"])
    else:
        msg = "⚠️ No Twitter accounts are being tracked."
    await update.message.reply_text(msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"🟢 Bot Status\nChannel: {config.get('channel', 'Not set')}\nTracked accounts: {len(config.get('twitters', []))}\n"
    for u in config.get("twitters", []):
        last = config.get("last_tweets", {}).get(u, "No tweets fetched yet")
        msg += f"\n@{u} - Last tweet ID: {last}"
    await update.message.reply_text(msg)

# ----- Tweet Fetching -----
async def fetch_latest_tweet(username):
    try:
        # Run blocking snscrape in thread to not block event loop
        tweets = await asyncio.to_thread(lambda: list(sntwitter.TwitterUserScraper(username).get_items()))
        if not tweets:
            return None
        latest = tweets[0]
        tweet_id = str(latest.id)
        if config.get("last_tweets", {}).get(username) != tweet_id:
            config.setdefault("last_tweets", {})[username] = tweet_id
            save_config()
            text_filtered = ' '.join([w for w in latest.content.split() if not w.startswith("http")])
            return text_filtered
    except Exception as e:
        print(f"Error fetching tweets for {username}: {e}")
    return None

async def fetch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not config.get("channel"):
        await update.message.reply_text("⚠️ Channel not set. Use /setchannel to set your Telegram channel.")
        return
    sent_count = 0
    for username in config["twitters"]:
        tweet_text = await fetch_latest_tweet(username)
        if tweet_text:
            await bot.send_message(chat_id=config["channel"], text=f"@{username}: {tweet_text}")
            sent_count += 1
    await update.message.reply_text(f"✅ Fetch complete. {sent_count} new tweet(s) sent.")

# ----- Background Task -----
async def periodic_fetch():
    while True:
        if config.get("channel") and config.get("twitters"):
            for username in config["twitters"]:
                tweet_text = await fetch_latest_tweet(username)
                if tweet_text:
                    try:
                        await bot.send_message(chat_id=config["channel"], text=f"@{username}: {tweet_text}")
                        print(f"[{datetime.now()}] Posted tweet from @{username}")
                    except Exception as e:
                        print(f"[{datetime.now()}] Error sending tweet for @{username}: {e}")
        await asyncio.sleep(60)  # check every 1 minute

# ----- Main -----
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setchannel", setchannel))
    app.add_handler(CommandHandler("addtwitter", addtwitter))
    app.add_handler(CommandHandler("removetwitter", removetwitter))
    app.add_handler(CommandHandler("listtwitters", listtwitters))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("fetch", fetch_command))

    # Run bot with background fetch
    async def run_bot():
        asyncio.create_task(periodic_fetch())
        await app.run_polling()

    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
