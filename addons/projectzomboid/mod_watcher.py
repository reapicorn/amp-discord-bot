import discord
from discord.ext import commands, tasks

import steam
from amp import AmpClient
from addons.base import GameAddon
from addons.projectzomboid.config_reader import read_workshop_ids


class ModWatcher(GameAddon):
    game_name = "Project Zomboid"
    game_emoji = "🧟"

    def __init__(self, bot: commands.Bot, server_cfg: dict):
        super().__init__()
        self.bot = bot
        self.notification_channel: str = server_cfg["channel_notifications"]
        addon_cfg = server_cfg["addon_config"]
        self.server_config_path: str = addon_cfg["server_config_path"]
        self.check_interval: int = addon_cfg.get("workshop_check_interval", 1800)

        # AmpClient proxied to the PZ instance for file reading
        self.amp_client = AmpClient(
            url=server_cfg["amp_url"],
            user=server_cfg["amp_user"],
            password=server_cfg["amp_pass"],
            instance_id=server_cfg["instance_id"],
        )

        @tasks.loop(seconds=self.check_interval)
        async def _poll():
            await self._check_updates()

        self._poll_task = _poll

    def setup_tasks(self):
        self._poll_task.start()

    async def _check_updates(self):
        channel = discord.utils.get(self.bot.get_all_channels(), name=self.notification_channel)
        if channel is None:
            print(f"[pz/mod_watcher] Channel '{self.notification_channel}' not found")
            return
        mod_ids = read_workshop_ids(self.amp_client, self.server_config_path)
        if not mod_ids:
            print("[pz/mod_watcher] No mods found in server config")
            return
        print(f"[pz/mod_watcher] Checking {len(mod_ids)} mods...")
        try:
            updated = steam.check_for_updates(mod_ids)
            print(f"[pz/mod_watcher] {len(updated)} mods updated." if updated else "[pz/mod_watcher] No changes.")
            if updated:
                header = "🔧 **Mods updated — server restart recommended:**"
                lines = [
                    f"• **{m['title']}** — <https://steamcommunity.com/sharedfiles/filedetails/?id={m['id']}>"
                    for m in updated
                ]
                # Split into chunks of max 2000 characters
                chunks = []
                current = header
                for line in lines:
                    if len(current) + len(line) + 1 > 2000:
                        chunks.append(current)
                        current = line
                    else:
                        current += "\n" + line
                chunks.append(current)
                for chunk in chunks:
                    await channel.send(chunk)
        except Exception as e:
            print(f"[pz/mod_watcher] Error checking mods: {e}")
