import os
import asyncio
import discord
import json
import re
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import logging

# === Logging Setup ===
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Discord-Make-Bridge")

# === Load Environment Variables ===
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL')

logger.debug(f"DISCORD_TOKEN loaded: {bool(DISCORD_TOKEN)}")
logger.debug(f"GUILD_ID loaded: {GUILD_ID}")
logger.debug(f"MAKE_WEBHOOK_URL loaded: {bool(MAKE_WEBHOOK_URL)}")

# === Discord Setup ===
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
client = discord.Client(intents=intents)

# === Utility Functions ===
def strip_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002700-\U000027BF"  # Dingbats
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text).strip()

# === Main Extraction ===
async def extract_and_upload():
    logger.info("Starting extraction process...")

    try:
        guild = client.get_guild(GUILD_ID)
        if not guild:
            logger.error("Guild not found.")
            return

        data_payload = []
        for category in guild.categories:
            logger.debug(f"Processing category: {category.name}")
            category_raw = strip_emojis(category.name)
            category_obj = {
                "category_full": category.name,
                "category_raw": category_raw,
                "channels": []
            }
            for channel in category.channels:
                if isinstance(channel, discord.TextChannel):
                    channel_raw = strip_emojis(channel.name)
                    channel_obj = {
                        "channel_full": channel.name,
                        "channel_raw": channel_raw
                    }
                    category_obj["channels"].append(channel_obj)
                    logger.debug(f"  Channel: {channel.name} | Raw: {channel_raw}")
            data_payload.append(category_obj)

        logger.debug("Full extracted data:")
        logger.debug(json.dumps(data_payload, indent=2, ensure_ascii=False))

        logger.info("Sending extracted data to Make webhook...")
        response = requests.post(MAKE_WEBHOOK_URL, json={"categories": data_payload})
        if response.status_code in [200, 204]:
            logger.info("Data sent to Make successfully.")
        else:
            logger.error(f"Failed to send to Make: {response.status_code} | {response.text}")

    except Exception as e:
        logger.exception(f"Error in extract_and_upload: {e}")

# === Re-post Data Back to Discord ===
async def post_to_discord(processed_data):
    logger.info("Posting reformatted data back to Discord...")
    try:
        message = ""
        for category in processed_data.get("categories", []):
            message += f"**{category['category_full']}**\n"
            for channel in category.get("channels", []):
                message += f"- {channel['channel_full']}\n"
        webhook_url = MAKE_WEBHOOK_URL  # If you have a Discord webhook URL, replace this
        response = requests.post(webhook_url, json={"content": message})
        if response.status_code in [200, 204]:
            logger.info("Posted back to Discord successfully.")
        else:
            logger.error(f"Failed to post to Discord: {response.status_code} | {response.text}")
    except Exception as e:
        logger.exception(f"Error posting to Discord: {e}")

# === Discord Events ===
@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    await extract_and_upload()

# === Flask Server for Keep-Alive ===
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running."

# === Scheduler Setup ===
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.get_event_loop().create_task(extract_and_upload()), 'cron', day_of_week='sat', hour=12)
scheduler.start()

# === Run App ===
def run():
    import threading
    threading.Thread(target=lambda: client.run(DISCORD_TOKEN)).start()
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 10000)))

if __name__ == '__main__':
    run()
