# AMP Discord Bot

A Discord bot for managing [AMP (Application Management Panel)](https://cubecoders.com/AMP) game servers via slash commands, with a per-game addon system.

## Features

- **Slash commands** — `/status`, `/start`, `/stop`, `/restart`, `/update`
- **Multi-server** — manages multiple AMP instances from a single bot, routed by Discord channel
- **Per-game addons** — extend the bot with game-specific functionality
- **Role-based access** — global admin role + per-instance override
- **Project Zomboid addon** — automatic Steam Workshop mod update notifications

## Requirements

- Python 3.12+
- An [AMP](https://cubecoders.com/AMP) installation
- A Discord bot token ([discord.com/developers](https://discord.com/developers/applications))

## Setup

### 1. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
DISCORD_TOKEN=your_discord_bot_token

AMP_URL=http://YOUR_AMP_HOST:8080
AMP_USER=discord-bot
AMP_PASS=your_amp_password
AMP_INSTANCE_ID=your_instance_uuid
```

Load the `.env` file before running the bot (or configure it in your systemd service — see [Running as a service](#running-as-a-service)).

### 3. Configure instances

Each game server is a YAML file in `instances/`. The default `instances/projectzomboid.yaml` references environment variables — edit it if you need to rename the variables or add more instances.

The bot loads all `*.yaml` files from `instances/` automatically.

### 4. Run

```bash
python3 bot.py
```

### 5. Sync slash commands (once)

In Discord, run `!sync` with the bot owner account. This registers the slash commands with Discord.

## Discord setup

Create two channels per game server:

| Channel | Purpose |
|---|---|
| `pz-commands` | Users write commands here |
| `pz-notifications` | Bot posts mod update alerts here (read-only for users) |

Set `channel_commands` and `channel_notifications` in the instance YAML to match.

## Instance YAML reference

```yaml
# Required
amp_url: "http://YOUR_AMP_HOST:8080"
amp_user: "discord-bot"
amp_pass: "password"
instance_id: "uuid-of-the-instance"

# Optional (defaults shown)
name: "projectzomboid"         # display name in embeds
emoji: "🎮"                    # emoji shown next to name
channel_commands: "server-commands"
channel_notifications: "server-notifications"
admin_role: null               # falls back to global admin_role
addon: null                    # game-specific addon module name
addon_config: {}
```

## Addons

Addons extend the bot with game-specific functionality. Set `addon: "<name>"` in an instance YAML to activate one.

| Addon | Description | Docs |
|---|---|---|
| `projectzomboid` | Steam Workshop mod update notifications | [README](addons/projectzomboid/README.md) |

### Writing a new addon

1. Create `addons/yourgame/__init__.py` with an `async def setup(bot, server_cfg)` function that registers your Cogs and returns the main Cog
2. Set `addon: "yourgame"` in the instance YAML
3. Restart the bot

## Adding a new game server

1. Create `instances/yourgame.yaml` with the required fields
2. Restart the bot — it loads all instance files automatically
3. Optionally set `addon: "yourgame"` to attach game-specific features

## Running multiple instances of the same game

Each file in `instances/` is an independent server — you can have as many as you need, including multiple servers running the same game.

**Example: two Project Zomboid servers**

`instances/projectzomboid.yaml`:
```yaml
amp_url: "${AMP_URL}"
amp_user: "${AMP_USER}"
amp_pass: "${AMP_PASS}"
instance_id: "${AMP_PZ1_INSTANCE_ID}"

name: "Project Zomboid"
emoji: "🧟"
channel_commands: "pz-commands"
channel_notifications: "pz-notifications"
admin_role: "PZ Admin"
addon: "projectzomboid"
addon_config:
  server_config_path: "Zomboid/Server/servertest.ini"
```

`instances/projectzomboid2.yaml`:
```yaml
amp_url: "${AMP_URL}"
amp_user: "${AMP_USER}"
amp_pass: "${AMP_PASS}"
instance_id: "${AMP_PZ2_INSTANCE_ID}"

name: "Project Zomboid 2"
emoji: "🧟"
channel_commands: "pz2-commands"
channel_notifications: "pz2-notifications"
admin_role: "PZ Admin"
addon: "projectzomboid"
addon_config:
  server_config_path: "Zomboid/Server/servertest2.ini"
```

`.env`:
```env
AMP_PZ1_INSTANCE_ID=uuid-of-first-pz-instance
AMP_PZ2_INSTANCE_ID=uuid-of-second-pz-instance
```

**Rules:**
- `channel_commands` and `channel_notifications` must be unique across all instances — the bot uses the channel name to route commands
- `name` must be unique — it is used as the internal key for the AMP client cache
- Each instance gets its own independent mod watcher loop and notification channel

## AMP user permissions

Create a dedicated AMP user (e.g. `discord-bot`) with a role that has:

**App Management:** Start, Stop, Restart, Update  
**File Manager:** Browse Files, Download Files  
**Instances:** Manage (on each target instance)

## Running as a service

```bash
cat > /etc/systemd/system/amp-discord-bot.service << 'EOF'
[Unit]
Description=AMP Discord Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/amp-discord-bot
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=/opt/amp-discord-bot/.env
ExecStart=/opt/amp-discord-bot/venv/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable amp-discord-bot
systemctl start amp-discord-bot
```

The `EnvironmentFile` directive loads `/opt/amp-discord-bot/.env` automatically — no need to `source` it manually.
