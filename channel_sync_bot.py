import os
import asyncio
import datetime
import discord
import gspread
import json
from io import StringIO
from google.oauth2.service_account import Credentials
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import logging

# Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DiscordBot")

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Google Sheets setup via Environment Variable
SHEET_NAME = "logger"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

if not service_account_json:
    raise Exception("Missing GOOGLE_SERVICE_ACCOUNT_JSON environment variable.")

credentials = Credentials.from_service_account_info(json.loads(service_account_json), scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open(SHEET_NAME).sheet1

CATEGORIES_TO_INCLUDE = [
    '📦 ETHNICITY VAULTS', '🧔 MALE CREATORS / AGENCY', '💪 HGF', '🎥 NET VIDEO GIRLS', '🇨🇳 ASIAN .1',
    '🇨🇳 ASIAN .2', '🇲🇽 LATINA .1', '🇲🇽 LATINA .2', '❄ SNOWBUNNIE .1', '❄ SNOWBUNNIE .2',
    '🇮🇳 INDIAN / DESI', '🇸🇦 ARAB', '🧬 MIXED / LIGHTSKIN', '🏴 BLACK', '🌺 POLYNESIAN',
    '☠ GOTH / ALT', '🏦 VAULT BANKS', '🔞 PORN', 'Uncatagorised Girls'
]

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
client = discord.Client(intents=intents)

async def extract_and_upload():
    logger.info("Extracting Discord data...")
    try:
        guild = client.get_guild(GUILD_ID)
        if not guild:
            logger.error("Guild not found.")
            return

        sheet.clear()
        sheet.append_row(["Category", "Channel"])

        for category_name in CATEGORIES_TO_INCLUDE:
            channels = [ch.name for ch in guild.text_channels if ch.category and ch.category.name == category_name]
            if channels:
                for ch in channels:
                    sheet.append_row([category_name, ch])
        logger.info("Data uploaded to Google Sheets.")

        # Fetch from Sheets and post to Discord
        all_rows = sheet.get_all_values()[1:]
        message = ""
        current_category = ""
        for cat, chan in all_rows:
            if cat != current_category:
                message += f"**{cat}**\n"
                current_category = cat
            message += f" - {chan}\n"

        await post_to_discord(message)

    except Exception as e:
        logger.exception(f"Error in extract_and_upload: {e}")

async def post_to_discord(content):
    import requests
    logger.info("Posting data to Discord webhook...")
    response = requests.post(WEBHOOK_URL, json={"content": content})
    if response.status_code in [200, 204]:
        logger.info("Posted successfully!")
    else:
        logger.error(f"Failed to post: {response.text}")

@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    await extract_and_upload()

# Flask to keep alive
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
