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
import traceback

# Logging Setup
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("DiscordBot")

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

logger.debug(f"DISCORD_TOKEN loaded: {bool(DISCORD_TOKEN)}")
logger.debug(f"GUILD_ID loaded: {GUILD_ID}")
logger.debug(f"WEBHOOK_URL loaded: {bool(WEBHOOK_URL)}")

# Google Sheets Setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "logger"

def setup_google_sheet():
    try:
        logger.debug("Attempting to load service_account.json...")
        credentials = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
        gc = gspread.authorize(credentials)
        sheet = gc.open(SHEET_NAME).sheet1
        logger.info("Google Sheets connected successfully.")
        return sheet
    except Exception as e:
        logger.error(f"Error setting up Google Sheets: {e}")
        traceback.print_exc()
        return None

CATEGORIES_TO_INCLUDE = [
    '📦 ETHNICITY VAULTS', '🧔 MALE CREATORS / AGENCY', '💪 HGF', '🎥 NET VIDEO GIRLS',
    '🇨🇳 ASIAN .1', '🇨🇳 ASIAN .2', '🇲🇽 LATINA .1', '🇲🇽 LATINA .2', '❄ SNOWBUNNIE .1',
    '❄ SNOWBUNNIE .2', '🇮🇳 INDIAN / DESI', '🇸🇦 ARAB', '🧬 MIXED / LIGHTSKIN', '🏴 BLACK',
    '🌺 POLYNESIAN', '☠ GOTH / ALT', '🏦 VAULT BANKS', '🔞 PORN', 'Uncatagorised Girls'
]

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
client = discord.Client(intents=intents)

async def extract_and_upload():
    logger.info("Starting extraction process...")

    sheet = setup_google_sheet()
    if sheet is None:
        logger.error("Google Sheets not available. Aborting extraction.")
        return

    try:
        guild = client.get_guild(int(GUILD_ID))
        if not guild:
            logger.error("Guild not found. Check GUILD_ID.")
            return

        logger.info(f"Found guild: {guild.name} ({guild.id})")

        sheet.clear()
        sheet.append_row(["Category", "Channel"])
        logger.info("Cleared existing sheet and wrote header row.")

        for category_name in CATEGORIES_TO_INCLUDE:
            logger.debug(f"Processing category: {category_name}")
            try:
                channels = [ch.name for ch in guild.text_channels if ch.category and ch.category.name == category_name]
                logger.debug(f"Channels found in {category_name}: {channels}")
                for ch in channels:
                    sheet.append_row([category_name, ch])
            except Exception as e:
                logger.error(f"Error processing category {category_name}: {e}")
                traceback.print_exc()

        logger.info("Data written to Google Sheets.")

        # Fetch from Sheets and post to Discord
        all_rows = sheet.get_all_values()[1:]
        logger.debug(f"All rows fetched from sheet: {all_rows}")

        message = ""
        last_category = ""
        for cat, chan in all_rows:
            if cat != last_category:
                message += f"\n**{cat}**\n"
                last_category = cat
            message += f"- {chan}\n"

        await post_to_discord(message.strip())

    except Exception as e:
        logger.error(f"Error in extract_and_upload: {e}")
        traceback.print_exc()

async def post_to_discord(content):
    import requests
    try:
        logger.info("Posting data to Discord webhook...")
        response = requests.post(WEBHOOK_URL, json={"content": content})
        logger.debug(f"Discord webhook response: {response.status_code}, {response.text}")
        if response.status_code in [200, 204]:
            logger.info("Posted successfully!")
        else:
            logger.error(f"Failed to post: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error posting to Discord: {e}")
        traceback.print_exc()

@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    await extract_and_upload()

# Flask server to keep alive
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
