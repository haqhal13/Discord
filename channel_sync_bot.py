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
    print("\n🚀 Starting fetch_and_post at", datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), "UTC")
    
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ ERROR: Could not find server with GUILD_ID:", GUILD_ID)
        return
    
    print(f"✅ Connected to server: {guild.name} (ID: {guild.id})")
    print(f"✅ Categories to process: {CATEGORIES_TO_INCLUDE}")

    # List all categories and channels in server
    all_categories = [c.name for c in guild.categories]
    print(f"📂 Server has {len(all_categories)} categories: {all_categories}")

    # Delete previous bot posts
    print("🗑️ Deleting previous messages by the bot...")
    for channel in guild.text_channels:
        async for message in channel.history(limit=100):
            if message.author == client.user:
                try:
                    await message.delete()
                    print(f"🗑️ Deleted message: {message.id} in #{channel.name}")
                except Exception as e:
                    print(f"⚠️ Failed to delete message {message.id}: {e}")

    for category_name in CATEGORIES_TO_INCLUDE:
        print(f"\n🔍 Searching for category: '{category_name}'")
        matched_channels = []
        for ch in guild.text_channels:
            if ch.category:
                print(f"    Checking channel: {ch.name} in category '{ch.category.name}' (ID: {ch.category.id})")
                if ch.category.name.strip().lower() == category_name.strip().lower():
                    print(f"    ✅ Match found: {ch.name} under '{ch.category.name}'")
                    matched_channels.append(ch)
        
        if not matched_channels:
            print(f"❌ No channels found under category: '{category_name}'")
        else:
            formatted = f"```md\n# {category_name}\n"
            for ch in matched_channels:
                formatted += f"- {ch.name}\n"
            formatted += f"\n_Last updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_\n```"

            print(f"📤 Sending data for category: '{category_name}'")
            print("Content to send:\n", formatted)

            response = requests.post(WEBHOOK_URL, json={"content": formatted})
            if response.status_code == 204:
                print(f"✅ Successfully sent category: '{category_name}'")
            else:
                print(f"❌ Failed to send category '{category_name}'. Status: {response.status_code}, Response: {response.text}")

            await asyncio.sleep(2)

    print("✅ fetch_and_post completed.\n")

@client.event
async def on_ready():
    print(f"\n✅ Bot is logged in as {client.user} (ID: {client.user.id})")
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
