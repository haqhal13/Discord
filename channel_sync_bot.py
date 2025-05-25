import os
import asyncio
import datetime
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import discord
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DiscordBot")

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PASTEBIN_API_KEY = os.getenv('PASTEBIN_API_KEY')
PASTEBIN_USERNAME = os.getenv('PASTEBIN_USERNAME')
PASTEBIN_PASSWORD = os.getenv('PASTEBIN_PASSWORD')

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
        logger.debug(f"Fetching categories: {CATEGORIES_TO_INCLUDE}")

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
            logger.warning("No categories matched for upload.")
            return

        logger.info("Authenticating with Pastebin...")
        login_data = {
            'api_dev_key': PASTEBIN_API_KEY,
            'api_user_name': PASTEBIN_USERNAME,
            'api_user_password': PASTEBIN_PASSWORD
        }
        login_response = requests.post("https://pastebin.com/api/api_login.php", data=login_data)
        logger.debug(f"Pastebin login response: {login_response.status_code} - {login_response.text}")
        if login_response.status_code != 200:
            logger.error(f"Pastebin login failed: {login_response.text}")
            return
        user_key = login_response.text

       paste_data = {
    'api_option': 'paste',
    'api_dev_key': PASTEBIN_API_KEY,
    'api_paste_code': content,
    'api_paste_name': f"Server A Categories {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
    'api_paste_private': '2',  # Private
    'api_paste_expire_date': '1W',
    'api_user_key': user_key
}
        paste_response = requests.post("https://pastebin.com/api/api_post.php", data=paste_data)
        logger.debug(f"Pastebin paste response: {paste_response.status_code} - {paste_response.text}")
        if paste_response.status_code != 200:
            logger.error(f"Failed to create paste: {paste_response.text}")
            return
        paste_url = paste_response.text
        logger.info(f"Paste created: {paste_url}")

        paste_key = paste_url.split('/')[-1]
        raw_url = f"https://pastebin.com/raw/{paste_key}"

        logger.info("Fetching raw content from Pastebin...")
        raw_response = requests.get(raw_url)
        logger.debug(f"Raw content response: {raw_response.status_code}")
        if raw_response.status_code != 200:
            logger.error(f"Failed to fetch raw content: {raw_response.text}")
            return
        raw_content = raw_response.text

        logger.info("Posting content to Server B via webhook...")
        webhook_response = requests.post(WEBHOOK_URL, json={"content": raw_content})
        logger.debug(f"Webhook response: {webhook_response.status_code} - {webhook_response.text}")
        if webhook_response.status_code in [200, 204]:
            logger.info("Content posted to Server B successfully.")
        else:
            logger.error(f"Failed to post content to Server B: {webhook_response.text}")

    except Exception as e:
        logger.exception(f"Unexpected error in extract_and_upload: {str(e)}")

@client.event
async def on_ready():
    logger.info(f"🤖 Logged in as {client.user} (ID: {client.user.id})")
    await extract_and_upload()

# Flask app to keep bot alive
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
