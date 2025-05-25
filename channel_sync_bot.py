import os
import asyncio
import datetime
import discord
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import logging
import json

# === Logging Setup ===
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DiscordBot")

# === Load Environment Variables ===
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL')

# === Discord Setup ===
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
client = discord.Client(intents=intents)

CATEGORIES_TO_INCLUDE = [
    '📦 ETHNICITY VAULTS', '🧔 MALE CREATORS / AGENCY', '💪 HGF', '🎥 NET VIDEO GIRLS', '🇨🇳 ASIAN .1',
    '🇨🇳 ASIAN .2', '🇲🇽 LATINA .1', '🇲🇽 LATINA .2', '❄ SNOWBUNNIE .1', '❄ SNOWBUNNIE .2',
    '🇮🇳 INDIAN / DESI', '🇸🇦 ARAB', '🧬 MIXED / LIGHTSKIN', '🏴 BLACK', '🌺 POLYNESIAN',
    '☠ GOTH / ALT', '🏦 VAULT BANKS', '🔞 PORN', 'Uncatagorised Girls'
]

async def extract_and_upload():
    logger.info("Starting extraction process...")

    try:
        guild = client.get_guild(GUILD_ID)
        if not guild:
            logger.error("Guild not found.")
            return

        data = {"categories": []}

        for category_name in CATEGORIES_TO_INCLUDE:
            channels = [ch.name for ch in guild.text_channels if ch.category and ch.category.name == category_name]
            logger.debug(f"Processing category: {category_name} | Channels: {channels}")
            if channels:
                data["categories"].append({"category": category_name, "channels": channels})

        logger.info("Data ready. Sending to Make...")

        # Send JSON data to Make Webhook
        response = requests.post(MAKE_WEBHOOK_URL, json=data)
        if response.status_code in [200, 204]:
            logger.info("Data sent to Make successfully.")
        else:
            logger.error(f"Failed to send to Make: {response.status_code} | {response.text}")

    except Exception as e:
        logger.exception(f"Error in extract_and_upload: {e}")

@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    await extract_and_upload()

# Flask + Scheduler
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running."

scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.get_event_loop().create_task(extract_and_upload()), 'cron', day_of_week='sat', hour=12)
scheduler.start()

def run():
    import threading
    threading.Thread(target=lambda: client.run(DISCORD_TOKEN)).start()
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 10000)))

if __name__ == '__main__':
    run()
