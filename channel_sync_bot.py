import os
import asyncio
import datetime
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import discord
import traceback

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

async def extract_and_upload():
    try:
        print("\n========== STARTING extract_and_upload() ==========")
        print(f"Time: {datetime.datetime.utcnow()}")

        print(f"🔍 Trying to fetch GUILD_ID: {GUILD_ID}")
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print("❌ Guild not found. Check if bot has access to this server.")
            return
        print(f"✅ Fetched guild: {guild.name} ({guild.id})")

        content = ""
        for category_name in CATEGORIES_TO_INCLUDE:
            print(f"\n🔎 Checking category: {category_name}")
            channels = [ch for ch in guild.text_channels if ch.category and ch.category.name == category_name]
            print(f"✅ Found {len(channels)} channels under {category_name}")
            if channels:
                formatted = f"```md\n# {category_name}\n"
                for ch in channels:
                    formatted += f"- {ch.name}\n"
                formatted += f"\n_Last updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}_\n```\n\n"
                content += formatted

        if not content:
            print("⚠️ No channels found in any categories. Exiting upload function.")
            return

        print("\n🔐 Authenticating with Pastebin...")
        login_data = {
            'api_dev_key': PASTEBIN_API_KEY,
            'api_user_name': PASTEBIN_USERNAME,
            'api_user_password': PASTEBIN_PASSWORD
        }
        print(f"🔑 Login data: {login_data}")
        login_response = requests.post("https://pastebin.com/api/api_login.php", data=login_data)
        print(f"🔐 Pastebin login response code: {login_response.status_code}, text: {login_response.text}")
        if login_response.status_code != 200:
            print("❌ Pastebin login failed.")
            return
        user_key = login_response.text.strip()

        print("📝 Creating new Pastebin paste...")
        paste_data = {
            'api_option': 'paste',
            'api_dev_key': PASTEBIN_API_KEY,
            'api_paste_code': content,
            'api_paste_name': f"Server A Categories {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            'api_paste_private': '1',
            'api_paste_expire_date': '1W',
            'api_user_key': user_key
        }
        print(f"📦 Paste data: {paste_data}")
        paste_response = requests.post("https://pastebin.com/api/api_post.php", data=paste_data)
        print(f"📝 Pastebin response: {paste_response.status_code} - {paste_response.text}")
        if paste_response.status_code != 200:
            print("❌ Pastebin paste creation failed.")
            return
        paste_url = paste_response.text.strip()
        print(f"✅ Pastebin paste created: {paste_url}")

        paste_key = paste_url.split('/')[-1]
        raw_url = f"https://pastebin.com/raw/{paste_key}"

        print("📥 Fetching raw Pastebin content...")
        raw_response = requests.get(raw_url)
        print(f"📥 Raw content status: {raw_response.status_code}")
        if raw_response.status_code != 200:
            print(f"❌ Failed to fetch raw content: {raw_response.text}")
            return
        raw_content = raw_response.text
        print(f"📄 Raw content:\n{raw_content[:500]}...")  # Show first 500 chars

        print("📤 Posting to Server B via webhook...")
        webhook_response = requests.post(WEBHOOK_URL, json={"content": raw_content})
        print(f"📤 Webhook response: {webhook_response.status_code} - {webhook_response.text}")
        if webhook_response.status_code in [200, 204]:
            print("✅ Successfully posted content to Server B.")
        else:
            print("❌ Webhook post failed.")

        print("========== FINISHED extract_and_upload() ==========\n")

    except Exception as e:
        print(f"❌ Exception in extract_and_upload(): {e}")
        traceback.print_exc()

@client.event
async def on_ready():
    print(f"\n🤖 Bot logged in as {client.user} at {datetime.datetime.utcnow()}")
    await extract_and_upload()

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running."

scheduler = BackgroundScheduler()

def scheduled_task():
    print(f"\n🕒 Running scheduled task at {datetime.datetime.utcnow()}")
    loop = asyncio.get_event_loop()
    loop.create_task(extract_and_upload())

scheduler.add_job(scheduled_task, 'cron', day_of_week='sat', hour=12, minute=0)
scheduler.start()

def run():
    import threading
    client_thread = threading.Thread(target=lambda: client.run(DISCORD_TOKEN))
    client_thread.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    print("🚀 Starting bot...")
    run()
