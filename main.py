import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Load Startup Channel ID explicitly
STARTUP_CHANNEL_ID = os.getenv('CHANNEL_ID_STARTUP')

# Cog Whitelist Configuration
allowed_cogs_env = os.getenv('ENABLED_COGS', '')
ALLOWED_COGS = [cog.strip() for cog in allowed_cogs_env.split(',') if cog.strip()]

# Define Bot Version Here (Centralized)
BOT_VERSION = "v1.03"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    # ✅ Use BOT_VERSION variable
    activity = discord.Game(name=f"CSforChange Helper {BOT_VERSION}")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    print(f'🚀 Login Success: {bot.user.name} ({bot.user.id})')
    print(f'Version: {BOT_VERSION}')  # ✅ Updated
    print('System operational. Ready to serve.')
    print(f'🔒 Allowed Cogs: {ALLOWED_COGS}')

    if STARTUP_CHANNEL_ID:
        try:
            target_channel = bot.get_channel(int(STARTUP_CHANNEL_ID))
            if target_channel:
                # ✅ Use BOT_VERSION variable
                await target_channel.send(f"🚀 **System Online:** CSforChange Helper {BOT_VERSION} is ready!")
                print(f"✅ Startup msg sent to Test Channel : {target_channel.name}")
            else:
                print(f"⚠️ Could not find Test Channel with ID {STARTUP_CHANNEL_ID}")
        except Exception as e:
            print(f"❌ Error sending startup msg: {e}")
    else:
        print("⚠️ CHANNEL_ID_STARTUP not found in .env")

@bot.command()
async def ping(ctx):
    await ctx.send('pong!')

async def load_extensions():
    if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                cog_name = filename[:-3]
                if cog_name in ALLOWED_COGS:
                    try:
                        await bot.load_extension(f'cogs.{cog_name}')
                        print(f'✅ Extension Loaded: {filename}')
                    except Exception as e:
                        print(f'❌ Failed to load {filename}: {e}')
                else:
                    print(f'🚫 Skipped: {filename}')

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == '__main__':
    if TOKEN:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n🛑 Bot shutdown manually.")
    else:
        print("❌ Error: DISCORD_TOKEN not found.")