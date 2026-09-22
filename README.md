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

### 2. Configure the bot

Copy the example config and fill in your values:

```bash
cp config.yaml.example config.yaml
```

```yaml
# config.yaml
discord_token: "YOUR_DISCORD_TOKEN"
admin_role: "Game Admin"
```

### 3. Configure instances

Each game server is a YAML file in `instances/`. Copy the example:

```bash
cp instances/projectzomboid.yaml.example instances/projectzomboid.yaml
```

Fill in your AMP credentials and instance ID:

```yaml
amp_url: "http://YOUR_AMP_HOST:8080"
amp_user: "discord-bot"
amp_pass: "your-password"
instance_id: "your-instance-uuid"
```

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

## Adding a new game

1. Create `instances/yourgame.yaml` with the required fields
2. Restart the bot — it loads all instance files automatically
3. Optionally create `addons/yourgame/` with a `setup(bot, server_cfg)` function

## Project Zomboid addon

When `addon: "projectzomboid"` is set, the bot:

- Reads `WorkshopItems` from `servertest.ini` via the AMP File Manager API
- Polls Steam Workshop every 30 minutes (configurable)
- Posts a message to `channel_notifications` when any mod is updated

```yaml
addon: "projectzomboid"
addon_config:
  server_config_path: "Zomboid/Server/servertest.ini"
  workshop_check_interval: 1800
```

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
ExecStart=/opt/amp-discord-bot/venv/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable amp-discord-bot
systemctl start amp-discord-bot
```
