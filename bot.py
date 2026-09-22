import asyncio
import importlib

import discord
from discord.ext import commands

from settings import DISCORD_TOKEN, ADMIN_ROLE, SERVERS
from core.management import Management

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Registered addon cogs — used to call setup_tasks on ready
_addon_cogs: list = []


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    for cog in _addon_cogs:
        cog.setup_tasks()
    print("Addons started. Use !sync to register slash commands in Discord.")


@bot.command(hidden=True)
@commands.is_owner()
async def sync(ctx):
    """Sync slash commands with Discord (bot owner only)."""
    synced = await bot.tree.sync()
    await ctx.send(f"✅ {len(synced)} slash commands synced.")


async def setup():
    # Core: management commands for all servers
    await bot.add_cog(Management(bot, SERVERS, ADMIN_ROLE))

    # Addons: one per server that has an addon configured
    for server_cfg in SERVERS:
        addon_name = server_cfg.get("addon")
        if not addon_name:
            continue
        try:
            module = importlib.import_module(f"addons.{addon_name}")
            cog = await module.setup(bot, server_cfg)
            _addon_cogs.append(cog)
            print(f"[addon] {addon_name} loaded for '{server_cfg['name']}'")
        except Exception as e:
            print(f"[addon] Error loading {addon_name}: {e}")


async def main():
    await setup()
    await bot.start(DISCORD_TOKEN)


asyncio.run(main())
