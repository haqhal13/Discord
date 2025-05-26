import os
import logging
from flask import Flask, request
import discord
import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv

# ─── CONFIGURATION ─────────────────────────────────────────────────────────
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', '0'))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # e.g. https://your-app.onrender.com/webhook

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
INCLUDE_SET = { name.strip().lower() for name in CATEGORIES_TO_INCLUDE }

# ─── LOGGING ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ─── DISCORD CLIENT SETUP ──────────────────────────────────────────────────
intents = discord.Intents.default()
intents.guilds = True
intents.messages = False
discord_client = discord.Client(intents=intents)

async def fetch_discord_channels() -> str:
    logging.info("Fetching Discord channels...")
    guild = discord_client.get_guild(DISCORD_GUILD_ID)
    if guild is None:
        logging.error(f"Guild ID {DISCORD_GUILD_ID} not found!")
        return "❌ Discord guild not found."

    lines = []
    for category in guild.categories:
        if category.name.strip().lower() in INCLUDE_SET:
            lines.append(f"<b>{category.name}</b>")
            for ch in category.text_channels:
                lines.append(f" - {ch.name}")
            lines.append("")

    if not lines:
        logging.warning("No matching categories found.")
        return "❌ No matching categories."

    # wrap in HTML <pre> for fixed spacing
    text = "\n".join(lines).strip()
    return text

# ─── TELEGRAM BOT SETUP ───────────────────────────────────────────────────
app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def start_handler(update, context):
    logging.info(f"/start by {update.effective_user.id}")
    await update.message.reply_text('⏳ Fetching Model channels please wait his could take 2-5 mins as we have hundreds...')
    try:
        text = await fetch_discord_channels()
        # send as HTML-formatted text
        await update.message.reply_text(text, parse_mode='HTML')
        logging.info("Channels sent successfully.")
    except Exception as e:
        logging.error(f"Failed to fetch channels: {e}")
        await update.message.reply_text('❌ Could not fetch channels.')

telegram_app.add_handler(CommandHandler('start', start_handler))

# ─── FLASK WEBHOOK ENDPOINT ───────────────────────────────────────────────
@app.route('/webhook', methods=['POST'])
def webhook():
    update = discord.utils.async_to_sync(telegram_app.bot.parse_update)(request.get_data())
    asyncio.run(telegram_app.process_update(update))
    return 'OK', 200

# ─── MAIN ENTRYPOINT ───────────────────────────────────────────────────────
if __name__ == '__main__':
    # Start Discord client
    loop = asyncio.get_event_loop()
    loop.create_task(discord_client.start(DISCORD_TOKEN))

    # Set Telegram webhook
    bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    logging.info("🚀 Telegram webhook initialized")

    # Run Flask (this will block)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

