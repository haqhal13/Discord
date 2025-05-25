import discord
import asyncio
import datetime
import requests
import os

# CONFIGURATION
TOKEN = os.getenv("DISCORD_TOKEN")  # Secure token from Render Environment
GUILD_ID = int(os.getenv("GUILD_ID"))  # Secure Server ID from Render Environment
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Secure Webhook URL from Render Environment

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

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Could not find the server. Check GUILD_ID.")
        await client.close()
        return

    # Delete all old messages
    print("🗑️ Deleting previous messages...")
    for channel in guild.text_channels:
        try:
            async for message in channel.history(limit=500):
                if message.author.bot:
                    await message.delete()
                    print(f"🗑️ Deleted message: {message.id}")
        except Exception as e:
            print(f"⚠️ Error deleting messages in {channel.name}: {e}")

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
                print(f"❌ Failed to send {category_name}: {response.status_code} | {response.text}")

            await asyncio.sleep(10)  # Slow down to avoid rate limits

    print("✅ All categories sent!")
    await client.close()

client.run(TOKEN)
