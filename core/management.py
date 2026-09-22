import discord
from discord import app_commands
from discord.ext import commands

from amp import AmpClient

STATE_MAP = {
    -1:  "❓ Unknown",
    0:   "⚪ Stopped",
    5:   "🟡 Starting",
    7:   "🟡 Configuring",
    10:  "🟡 Starting",
    20:  "🟢 Running",
    30:  "🔄 Restarting",
    40:  "🔴 Stopping",
    45:  "🔴 Stopping",
    50:  "💤 Sleeping",
    60:  "⏳ Waiting",
    70:  "📦 Installing",
    75:  "🔄 Updating",
    80:  "⚠️ Awaiting input",
    100: "💥 Failed",
    200: "🚫 Suspended",
    250: "🔧 Maintenance",
    999: "❓ Indeterminate",
}


def _build_server_lookup(servers: list[dict]) -> dict[str, dict]:
    """Returns {channel_name: server_config} for fast routing."""
    return {s["channel_commands"]: s for s in servers}


class Management(commands.Cog):
    def __init__(self, bot: commands.Bot, servers: list[dict], admin_role: str):
        self.bot = bot
        self.global_admin_role = admin_role
        self._lookup = _build_server_lookup(servers)
        # AmpClient cached per server name
        self._clients: dict[str, AmpClient] = {
            s["name"]: AmpClient(
                s["amp_url"], s["amp_user"], s["amp_pass"],
                instance_id=s.get("instance_id"),
            )
            for s in servers
        }

    def _get_server(self, interaction: discord.Interaction) -> tuple[dict, AmpClient] | None:
        """Returns (server_config, amp_client) based on the interaction channel, or None."""
        cfg = self._lookup.get(interaction.channel.name)
        if cfg is None:
            return None
        return cfg, self._clients[cfg["name"]]

    def _is_admin(self, interaction: discord.Interaction, cfg: dict) -> bool:
        """Checks if the user has the global role or the instance-specific role."""
        allowed_roles = {self.global_admin_role, cfg.get("admin_role")} - {None}
        return any(
            discord.utils.get(interaction.user.roles, name=role)
            for role in allowed_roles
        )

    def _log_command(self, interaction: discord.Interaction, command: str):
        user = f"{interaction.user} ({interaction.user.id})"
        channel = f"#{interaction.channel.name}"
        print(f"[cmd] {command} by {user} in {channel}")

    async def _reject_wrong_channel(self, interaction: discord.Interaction) -> bool:
        """Replies with an error if the channel doesn't match any server. Returns True to abort."""
        if self._get_server(interaction) is None:
            channels = ", ".join(f"#{c}" for c in self._lookup)
            await interaction.response.send_message(
                f"❌ Use this command in one of these channels: {channels}", ephemeral=True
            )
            return True
        return False

    async def _reject_non_admin(self, interaction: discord.Interaction, cfg: dict) -> bool:
        """Replies with an error if the user lacks any authorized role. Returns True to abort."""
        if not self._is_admin(interaction, cfg):
            allowed_roles = {self.global_admin_role, cfg.get("admin_role")} - {None}
            roles_str = " or ".join(f"**{r}**" for r in allowed_roles)
            await interaction.response.send_message(
                f"❌ You need the {roles_str} role to use this command.", ephemeral=True
            )
            return True
        return False

    # ------------------------------------------------------------------ #
    #  Slash commands                                                      #
    # ------------------------------------------------------------------ #

    @app_commands.command(name="status", description="Show server status")
    async def status(self, interaction: discord.Interaction):
        if await self._reject_wrong_channel(interaction):
            return
        cfg, client = self._get_server(interaction)
        self._log_command(interaction, "status")
        await interaction.response.defer()
        try:
            data = client.get_status()
            state_code = data.get("State", -1)
            state_label = STATE_MAP.get(state_code, f"Unknown ({state_code})")
            metrics = data.get("Metrics", {})
            players = metrics.get("Active Users", {}).get("RawValue", 0)
            max_players = metrics.get("Active Users", {}).get("MaxValue", "?")
            cpu = metrics.get("CPU Usage", {}).get("RawValue", 0)
            ram = metrics.get("Memory Usage", {}).get("RawValue", 0)
            ram_max = metrics.get("Memory Usage", {}).get("MaxValue", "?")

            embed = discord.Embed(
                title=f"{cfg['emoji']} {cfg['name']}",
                color=0x3b82d4,
            )
            embed.add_field(name="Status", value=state_label, inline=False)
            embed.add_field(name="Players", value=f"{players}/{max_players}", inline=True)
            embed.add_field(name="CPU", value=f"{cpu:.1f}%", inline=True)
            embed.add_field(name="RAM", value=f"{ram}/{ram_max} MB", inline=True)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Error fetching status: `{e}`")

    @app_commands.command(name="start", description="Start the server")
    async def start(self, interaction: discord.Interaction):
        if await self._reject_wrong_channel(interaction):
            return
        cfg, client = self._get_server(interaction)
        if await self._reject_non_admin(interaction, cfg):
            return
        self._log_command(interaction, "start")
        await interaction.response.defer()
        try:
            client.start()
            await interaction.followup.send("✅ Server started.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error starting server: `{e}`")

    @app_commands.command(name="stop", description="Stop the server")
    async def stop(self, interaction: discord.Interaction):
        if await self._reject_wrong_channel(interaction):
            return
        cfg, client = self._get_server(interaction)
        if await self._reject_non_admin(interaction, cfg):
            return
        self._log_command(interaction, "stop")
        await interaction.response.defer()
        try:
            client.stop()
            await interaction.followup.send("🛑 Server stopped.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error stopping server: `{e}`")

    @app_commands.command(name="restart", description="Restart the server")
    async def restart(self, interaction: discord.Interaction):
        if await self._reject_wrong_channel(interaction):
            return
        cfg, client = self._get_server(interaction)
        if await self._reject_non_admin(interaction, cfg):
            return
        self._log_command(interaction, "restart")
        await interaction.response.defer()
        try:
            client.restart()
            await interaction.followup.send("🔄 Server restarted.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error restarting server: `{e}`")

    @app_commands.command(name="update", description="Update the server")
    async def update(self, interaction: discord.Interaction):
        if await self._reject_wrong_channel(interaction):
            return
        cfg, client = self._get_server(interaction)
        if await self._reject_non_admin(interaction, cfg):
            return
        self._log_command(interaction, "update")
        await interaction.response.defer()
        try:
            client.update()
            await interaction.followup.send("🔄 Updating server... this may take a few minutes.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error updating server: `{e}`")
