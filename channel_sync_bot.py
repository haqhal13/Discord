import discord
import asyncio
import datetime
import requests
import os
import schedule
import time
from flask import Flask

# CONFIGURATION (uses environment variables)
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
PASTEBIN_API_KEY = os.getenv('PASTEBIN_API_KEY')
PASTEBIN_USER_KEY = os.getenv('PASTEBIN_USER_KEY')  # Optional if you're using an account

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

async def post_to_pastebin(content):
    data = {
        'api_dev_key': PASTEBIN_API_KEY,
        'api_option': 'paste',
        'api_paste_code': content,
        'api_paste_private': 1,
        'api_paste_expire_date': '1W',
        'api_paste_format': 'text'
    }
    if PASTEBIN_USER_KEY:
        data['api_user_key'] = PASTEBIN_USER_KEY

    response = requests.post('https://pastebin.com/api/api_post.php', data=data)
    if response.status_code == 200:
        paste_url = response.text
        print(f"✅ Uploaded to Pastebin: {paste_url}")
        return paste_url
    else:
        print(f"❌ Pastebin upload failed: {response.status_code}, {response.text}")
        return None

async def sync_categories():
    print("🔄 Running category sync task...")

    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Could not find the server. Check GUILD_ID.")
        return

    # Build the category text
    all_content = ""
    for category_name in CATEGORIES_TO_INCLUDE:
        channels = [ch for ch in guild.text_channels if ch.category and ch.category.name == category_name]
        if channels:
            all_content += f"# {category_name}\n"
            for ch in channels:
                all_content += f"- {ch.name}\n"
            all_content += f"\n_Last updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}_\n\n"

    # Upload to Pastebin
    await post_to_pastebin(all_content)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

    # Schedule the task every Saturday at 12:00 PM
    schedule.every().saturday.at("12:00").do(lambda: asyncio.ensure_future(sync_categories()))

    # Keep running the schedule loop
    while True:
        schedule.run_pending()
        await asyncio.sleep(30)

# Minimal Flask app for Render
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running."

def run():
    import threading
    client_thread = threading.Thread(target=lambda: client.run(TOKEN))
    client_thread.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    run()
