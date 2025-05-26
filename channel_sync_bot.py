import os
import logging
from dotenv import load_dotenv
from flask import Flask, request
import discord
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, webhook

# --- Configuration & Logging ---
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # https://your-domain.com/webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Only these categories will be included
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
_allowed = {c.strip() for c in CATEGORIES_TO_INCLUDE}

# --- Discord Client Setup ---
intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)

# --- Telegram Bot Setup ---
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

def filter_channels(guild):
    out = []
    for ch in guild.text_channels:
        if ch.category and ch.category.name.strip() in _allowed:
            out.append((ch.category.name.strip(), ch.name))
    return out

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"⏳ Getting up to date list, please wait 2-5 mins...", parse_mode='HTML'
    )
    try:
        await client.wait_until_ready()
        guild = client.get_guild(DISCORD_GUILD_ID)
        if not guild:
            raise ValueError("Guild not found")

        logger.info("⏳ Fetching Model channels please wait this could take 2-5 mins as we have hundreds...")
        channels = filter_channels(guild)
        if not channels:
            text = "❌ No matching categories or channels found."
        else:
            lines = []
            current_cat = None
            for cat, name in sorted(channels):
                if cat != current_cat:
                    lines.append(f"\n<b>{cat}</b>")
                    current_cat = cat
                lines.append(f" - {name}")
            text = "\n".join(lines)

        await update.message.reply_text(
            f"<b>Guild Channels:</b>\n{text}", parse_mode='HTML', disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Failed to fetch channels: {e}")
        await update.message.reply_text(
            "❌ Could not fetch channels.", parse_mode='HTML'
        )

# Register Telegram handler
t_bot = bot_app
t_bot.add_handler(CommandHandler('start', start_handler))

# --- Flask Webhook Receiver ---
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook_route():
    data = request.get_json(force=True)
    update = Update.de_json(data, Bot(TELEGRAM_TOKEN))
    bot_app._process_update(update)
    return 'OK', 200

if __name__ == '__main__':
    # set Telegram webhook
    Bot(TELEGRAM_TOKEN).set_webhook(f"{WEBHOOK_URL}/webhook")
    logger.info("🚀 Telegram webhook initialized")

    # start Discord
    logger.info("🚀 Starting Discord client")
    client.run(DISCORD_TOKEN)


