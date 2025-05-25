import os
import asyncio
import datetime
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import discord
import logging
import re

# Logging setup
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DiscordBot")

# Load .env
load_dotenv()

# Config
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PRIVATEBIN_URL = os.getenv('PRIVATEBIN_URL', 'https://privatebin.net')

CATEGORIES_TO_INCLUDE = [
    '📦 ETHNICITY VAULTS', '🧔 MALE CREATORS / AGENCY', '💪 HGF', '🎥 NET VIDEO GIRLS',
    '🇨🇳 ASIAN .1', '🇨🇳 ASIAN .2', '🇲🇽 LATINA .1', '🇲🇽 LATINA .2', '❄ SNOWBUNNIE .1', '❄ SNOWBUNNIE .2',
    '🇮🇳 INDIAN / DESI', '🇸🇦 ARAB', '🧬 MIXED / LIGHTSKIN', '🏴 BLACK', '🌺 POLYNESIAN',
    '☠ GOTH / ALT', '🏦 VAULT BANKS', '🔞 PORN', 'Uncatagorised Girls'
]

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
client = discord.Client(intents=intents)

async def extract_and_upload():
    logger.debug("Starting category extraction process...")
    try:
        guild = client.get_guild(GUILD_ID)
        if not guild:
            logger.error("Guild not found. Check GUILD_ID.")
            return

        logger.info(f"Connected to guild: {guild.name} (ID: {guild.id})")
        content = ""
        for category_name in CATEGORIES_TO_INCLUDE:
            channels = [ch for ch in guild.text_channels if ch.category and ch.category.name == category_name]
            logger.debug(f"Category '{category_name}': Found {len(channels)} channels.")
            if channels:
                formatted = f"```md\n# {category_name}\n"
                for ch in channels:
                    formatted += f"- {ch.name}\n"
                formatted += f"\n_Last updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}_\n```\n\n"
                content += formatted

        if not content:
            logger.warning("No content found to upload.")
            return

        logger.info("Uploading data to PrivateBin...")

        data = {
            "text": content,
            "formatter": "plaintext",
            "expire": "1day"
        }

        response = requests.post(f"{PRIVATEBIN_URL}/", data=data)
        if response.status_code != 200:
            logger.error(f"Failed to upload to PrivateBin: {response.status_code} - {response.text}")
            return

        match = re.search(r'href="(.*?)"', response.text)
        if match:
            paste_url = match.group(1)
            if paste_url.startswith("/"):
                paste_url = f"{PRIVATEBIN_URL}{paste_url}"
            logger.info(f"PrivateBin paste created: {paste_url}")
        else:
            logger.error("Could not extract paste URL from PrivateBin response.")
            return

        # Send link to Discord webhook
        logger.info("Posting link to Server B via webhook...")
        webhook_response = requests.post(WEBHOOK_URL, json={"content": f"New content uploaded: {paste_url}"})
        if webhook_response.status_code in [200, 204]:
            logger.info("Content posted to Discord successfully.")
        else:
            logger.error(f"Failed to post to Discord: {webhook_response.status_code} - {webhook_response.text}")

    except Exception as e:
        logger.exception(f"Unexpected error in extract_and_upload: {str(e)}")

@client.event
async def on_ready():
    logger.info(f"🤖 Logged in as {client.user} (ID: {client.user.id})")
    await extract_and_upload()

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running."

scheduler = BackgroundScheduler()

def scheduled_task():
    logger.info("Running scheduled task (every Saturday at 12 PM)...")
    loop = asyncio.get_event_loop()
    loop.create_task(extract_and_upload())

scheduler.add_job(scheduled_task, 'cron', day_of_week='sat', hour=12, minute=0)
scheduler.start()

def run():
    import threading
    logger.info("Starting Discord bot and Flask app...")
    client_thread = threading.Thread(target=lambda: client.run(DISCORD_TOKEN))
    client_thread.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    run()
