from discord.ext import commands

from addons.projectzomboid.mod_watcher import ModWatcher


async def setup(bot: commands.Bot, server_cfg: dict):
    """Registra los Cogs del addon Project Zomboid."""
    cog = ModWatcher(bot, server_cfg)
    await bot.add_cog(cog)
    return cog
