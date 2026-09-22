from discord.ext import commands


class GameAddon(commands.Cog):
    """
    Base class for game-specific addons.
    Each addon registers its own Cogs and tasks in setup().
    """

    # Override in each addon
    game_name: str = ""
    game_emoji: str = ""

    def setup_tasks(self):
        """Hook to start background tasks. Called on on_ready."""
        pass
