import os
import asyncio
import datetime
import discord
import gspread
from google.oauth2.service_account import Credentials
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
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
SHEET_NAME = "logger"

logger.debug(f"DISCORD_TOKEN loaded: {bool(DISCORD_TOKEN)}")
logger.debug(f"GUILD_ID loaded: {GUILD_ID}")
logger.debug(f"WEBHOOK_URL loaded: {bool(WEBHOOK_URL)}")

# === Google Sheets Setup ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "service_account.json"

def setup_google_sheet():
    try:
        logger.debug("Attempting to load service_account.json...")
        credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        gc = gspread.authorize(credentials)
        sheet = gc.open(SHEET_NAME).sheet1
        logger.info("Google Sheets setup successful.")
        return sheet
    except Exception as e:
        logger.error(f"Error setting up Google Sheets: {e}")
        return None

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

# === Main Sync Function ===
async def extract_and_upload():
    logger.info("Starting extraction process...")

    # Setup Google Sheets
    sheet = setup_google_sheet()
    if sheet is None:
        logger.error("Google Sheets not available. Aborting extraction.")
        return

    try:
        guild = client.get_guild(GUILD_ID)
        if not guild:
            logger.error("Guild not found.")
            return

        logger.debug("Clearing existing sheet content...")
        sheet.clear()
        sheet.append_row(["Category", "Channel"])

        for category_name in CATEGORIES_TO_INCLUDE:
            channels = [ch.name for ch in guild.text_channels if ch.category and ch.category.name == category_name]
            logger.debug(f"Processing category: {category_name} | Channels found: {channels}")
            if channels:
                for ch in channels:
                    sheet.append_row([category_name, ch])

        logger.info("Data uploaded to Google Sheets.")

        # Prepare Discord message
        all_rows = sheet.get_all_values()[1:]
        message = ""
        last_category = ""
        for cat, chan in all_rows:
            if cat != last_category:
                message += f"**{cat}**\n"
                last_category = cat
            message += f" - {chan}\n"

        await post_to_discord(message)

    except Exception as e:
        logger.exception(f"Error in extract_and_upload: {e}")

# === Post to Discord Webhook ===
async def post_to_discord(content):
    import requests
    logger.info("Posting data to Discord webhook...")
    try:
        response = requests.post(WEBHOOK_URL, json={"content": content})
        if response.status_code in [200, 204]:
            logger.info("Posted successfully to Discord.")
        else:
            logger.error(f"Failed to post to Discord: {response.status_code} | {response.text}")
    except Exception as e:
        logger.exception(f"Error posting to Discord: {e}")

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
