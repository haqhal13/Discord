import discord
import asyncio
import datetime
import requests
import os

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

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Could not find the server. Check GUILD_ID.")
        await client.close()
        return

    print("🗑️ Deleting previous webhook posts...")
    for channel in guild.text_channels:
        async for message in channel.history(limit=500):
            if message.author.bot:
                try:
                    await message.delete()
                    print(f"🗑️ Deleted message: {message.id}")
                except:
                    pass

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

            await asyncio.sleep(5)  # Delay

    print("✅ All categories sent!")
    await client.close()

client.run(TOKEN)
