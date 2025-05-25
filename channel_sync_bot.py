import discord
import asyncio
import datetime
import requests
import os
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

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

async def post_category_list():
    print("✅ Posting category list...")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Could not find the server. Check GUILD_ID.")
        return

    # Delete previous webhook messages
    print("🗑️ Deleting previous webhook posts...")
    for channel in guild.text_channels:
        async for message in channel.history(limit=500):
            if message.author.bot:
                try:
                    await message.delete()
                    print(f"🗑️ Deleted message: {message.id}")
                except:
                    pass

    # Post categories
    for category_name in CATEGORIES_TO_INCLUDE:
        channels = [ch for ch in guild.text_channels if ch.category and ch.category.name == category_name]
        if channels:
            formatted = f"```md\n# {category_name}\n"
            for ch in channels:
                formatted += f"- {ch.name}\n"
            formatted += f"\n_Last updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}_\n```"

            response = requests.post(WEBHOOK_URL, json={"content": formatted})
            if response.status_code == 204:
                print(f"✅ Sent category: {category_name}")
            else:
                print(f"❌ Failed to send category {category_name}: {response.status_code}, {response.text}")

            await asyncio.sleep(5)

    print("✅ All categories sent!")

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    # Run once on startup
    await post_category_list()

# Flask app to keep Render awake
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running."

# Scheduler setup
scheduler = BackgroundScheduler()

def scheduled_job():
    loop = asyncio.get_event_loop()
    loop.create_task(post_category_list())

scheduler.add_job(scheduled_job, 'cron', day_of_week='sat', hour=12, minute=0)
scheduler.start()

def run():
    import threading
    client_thread = threading.Thread(target=lambda: client.run(TOKEN))
    client_thread.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    run()
