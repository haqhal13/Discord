import discord
import asyncio
import datetime
import requests
import os
from flask import Flask
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# CONFIGURATION (uses environment variables)
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

CATEGORIES_TO_INCLUDE = [
    '📦 ETHNICITY VAULTS',
    '🧔 MALE CREATORS / AGENCY',
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

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

client = discord.Client(intents=intents)
scheduler = AsyncIOScheduler()

async def fetch_and_post():
    print("🚀 Fetching and posting categories...")

    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Could not find the server. Check GUILD_ID.")
        return

    for channel in guild.text_channels:
        async for message in channel.history(limit=100):
            if message.author == client.user:
                try:
                    await message.delete()
                    print(f"🗑️ Deleted message: {message.id}")
                except:
                    pass

    for category_name in CATEGORIES_TO_INCLUDE:
        channels = [
            ch for ch in guild.text_channels
            if ch.category and ch.category.name.strip().lower() == category_name.strip().lower()
        ]

        if channels:
            formatted = f"```md\n# {category_name}\n"
            for ch in channels:
                formatted += f"- {ch.name}\n"
            formatted += f"\n_Last updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_\n```"

            response = requests.post(WEBHOOK_URL, json={"content": formatted})
            if response.status_code == 204:
                print(f"✅ Sent category: {category_name}")
            else:
                print(f"❌ Failed to send {category_name}: {response.status_code}, {response.text}")

            await asyncio.sleep(2)

    print("✅ All categories posted.")

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

    # Run post on startup
    await fetch_and_post()

    # Schedule the weekly job
    user_datetime_str = "2025-06-01 14:30"  # Set your time here (UTC)
    dt = datetime.datetime.strptime(user_datetime_str, "%Y-%m-%d %H:%M")
    scheduler.add_job(fetch_and_post, trigger='cron', day_of_week=dt.weekday(), hour=dt.hour, minute=dt.minute)
    scheduler.start()

    print(f"🗓️ Scheduled weekly job at {dt.strftime('%A %H:%M')} UTC")

# Flask app for uptime pings
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running."

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    import threading
    threading.Thread(target=run_flask).start()
    client.run(TOKEN)
