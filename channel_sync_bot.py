import os
import asyncio
import discord
import logging
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import requests
import json
import re

# === Logging Setup ===
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DiscordBot")

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
client = discord.Client(intents=intents)

CATEGORIES_TO_INCLUDE = [
    '📦 ETHNICITY VAULTS', '🧔 MALE CREATORS / AGENCY', '💪 HGF', '🎥 NET VIDEO GIRLS', '🇨🇳 ASIAN .1',
    '🇨🇳 ASIAN .2', '🇲🇽 LATINA .1', '🇲🇽 LATINA .2', '❄ SNOWBUNNIE .1', '❄ SNOWBUNNIE .2',
    '🇮🇳 INDIAN / DESI', '🇸🇦 ARAB', '🧬 MIXED / LIGHTSKIN', '🏴 BLACK', '🌺 POLYNESIAN',
    '☠ GOTH / ALT', '🏦 VAULT BANKS', '🔞 PORN', 'Uncatagorised Girls'
]

# === Helper to Extract Clean Names ===
def clean_name(name):
    return re.sub(r'[^a-zA-Z0-9\s\-]', '', name).strip()

# === Extract and Upload ===
async def extract_and_upload():
    logger.info("Starting extraction process...")

    try:
        guild = client.get_guild(GUILD_ID)
        if not guild:
            logger.error("Guild not found.")
            return

        data = []
        for category in guild.categories:
            if category.name not in CATEGORIES_TO_INCLUDE:
                logger.debug(f"Skipping category: {category.name}")
                continue

            channels = [ch.name for ch in category.channels if isinstance(ch, discord.TextChannel)]
            logger.debug(f"Processing category: {category.name} | Channels: {channels}")

            data.append({
                "category_raw": clean_name(category.name),
                "category_full": category.name,
                "channels": [
                    {"channel_raw": clean_name(ch), "channel_full": ch} for ch in channels
                ]
            })

        logger.debug("Final extracted data:")
        logger.debug(json.dumps(data, indent=2, ensure_ascii=False))

        send_to_make(data)

    except Exception as e:
        logger.exception(f"Error in extract_and_upload: {e}")

# === Post to Make Webhook ===
def send_to_make(data):
    logger.info("Sending extracted data to Make webhook...")
    try:
        payload = {"categories": data}
        headers = {"Content-Type": "application/json"}
        response = requests.post(MAKE_WEBHOOK_URL, json=payload, headers=headers)
        if response.status_code in [200, 204]:
            logger.info("Data sent to Make successfully.")
        else:
            logger.error(f"Failed to send to Make: {response.status_code} | {response.text}")
    except Exception as e:
        logger.exception(f"Error posting to Make: {e}")

# === Discord Events ===
@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    await extract_and_upload()

# === Flask Server ===
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running."

# === Scheduler ===
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
