import discord
import asyncio
import datetime
import requests
import os
import pytz
from flask import Flask
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# CONFIGURATION (edit below)
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

POST_SCHEDULE = {
    "datetime": "2025-06-01 14:30",  # Initial post time (local time)
    "timezone": "Europe/London",      # e.g., 'Europe/London' or 'Asia/Dubai'
    "repeat_every": "2d"             # e.g., '1d', '2d', '4h', '30m'
}

CATEGORIES_TO_INCLUDE = [
    '📦 ETHNICITY VAULTS',
    '🧔 MALE CREATORS  / AGENCY',
    '💪 HGF',
    '🎥 NET VIDEO GIRLS',
    '🇨🇳 ASIAN .1',
    '🇨🇳 ASIAN .2',
    '🇲🇽 LATINA .1',
    '🇲🇽 LATINA .2',
    '❄ SNOWBUNNIE .1',
    '❄ SNOWBUNNIE .2',
    '🇮🇳 INDIAN / DESI',
    '🇸🇦 ARAB',
    '🧬 MIXED / LIGHTSKIN',
    '🏴 BLACK',
    '🌺 POLYNESIAN',
    '☠ GOTH / ALT',
    '🏦 VAULT BANKS',
    '🔞 PORN',
    'Uncatagorised Girls'
]

# Discord & Scheduler Setup
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
client = discord.Client(intents=intents)
scheduler = AsyncIOScheduler()

# Fetch and Post Logic
async def fetch_and_post():
    print(f"\n🚀 fetch_and_post started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"❌ ERROR: Guild {GUILD_ID} not found!")
        return

    for category_name in CATEGORIES_TO_INCLUDE:
        print(f"\n🔍 Searching for category: '{category_name}'")
        matched_channels = []
        for ch in guild.text_channels:
            if ch.category and ch.category.name.strip().lower() == category_name.strip().lower():
                print(f"    ✅ Found: {ch.name} in {ch.category.name}")
                matched_channels.append(ch)

        if not matched_channels:
            print(f"❌ No channels found for category '{category_name}'")
        else:
            formatted = f"```md\n# {category_name}\n"
            for ch in matched_channels:
                formatted += f"- {ch.name}\n"
            formatted += f"\n_Last updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_\n```"

            response = requests.post(WEBHOOK_URL, json={"content": formatted})
            if response.status_code == 204:
                print(f"✅ Sent category: '{category_name}'")
            else:
                print(f"❌ Failed to send '{category_name}': {response.status_code}, {response.text}")

            await asyncio.sleep(2)
    print("✅ fetch_and_post complete.")

# Scheduler Setup
def setup_schedule():
    try:
        tz = pytz.timezone(POST_SCHEDULE['timezone'])
        dt_local = datetime.datetime.strptime(POST_SCHEDULE['datetime'], "%Y-%m-%d %H:%M")
        dt_utc = tz.localize(dt_local).astimezone(pytz.utc)
        repeat_str = POST_SCHEDULE['repeat_every']

        if repeat_str.endswith('d'):
            seconds = int(repeat_str[:-1]) * 86400
        elif repeat_str.endswith('h'):
            seconds = int(repeat_str[:-1]) * 3600
        elif repeat_str.endswith('m'):
            seconds = int(repeat_str[:-1]) * 60
        else:
            raise ValueError("Invalid format: Use '1d', '4h', '30m'")

        scheduler.add_job(fetch_and_post, trigger=IntervalTrigger(
            start_date=dt_utc,
            seconds=seconds
        ))

        scheduler.start()
        print(f"🗓️ Scheduled job: Starts {dt_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC, repeats every {repeat_str}")
    except Exception as e:
        print(f"❌ Scheduling error: {e}")

# Discord Bot Events
@client.event
async def on_ready():
    print(f"\n✅ Bot logged in as {client.user} ({client.user.id})")
    await fetch_and_post()
    setup_schedule()

# Flask app for uptime pings
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running."

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

# Run Everything
if __name__ == '__main__':
    import threading
    threading.Thread(target=run_flask).start()
    client.run(TOKEN)
