# Project Zomboid Addon

Extends the bot with Steam Workshop mod update monitoring for Project Zomboid dedicated servers.

## What it does

- On startup and every 30 minutes, reads the active mod list from `servertest.ini` via the AMP File Manager API
- Compares each mod's `time_updated` against the last known value (stored in `workshop_state.json`)
- Posts a notification to `channel_notifications` when one or more mods have been updated on Steam Workshop

## Configuration

```yaml
addon: "projectzomboid"
addon_config:
  # Path to servertest.ini, relative to the instance root in AMP
  # Default: "Zomboid/Server/servertest.ini"
  server_config_path: "Zomboid/Server/servertest.ini"

  # How often to check for mod updates, in seconds
  # Default: 1800 (30 minutes)
  workshop_check_interval: 1800
```

## AMP permissions required

The AMP user needs the following permissions **on the PZ instance** (not just the ADS):

| Section | Permission |
|---|---|
| App Management | Start, Stop, Restart, Update |
| File Manager | Browse Files, Download Files |
| Instances | Manage |

> The **Manage** permission on the instance is required for the bot to authenticate via the ADS proxy.

## How mod detection works

1. The addon calls `FileManagerPlugin/ReadFileChunk` on the AMP API to read `servertest.ini`
2. It parses the `WorkshopItems` field (semicolon-separated list of Steam Workshop IDs)
3. It queries the Steam API (`ISteamRemoteStorage/GetPublishedFileDetails`) for each mod's `time_updated`
4. It compares against the previous values saved in `workshop_state.json`
5. Any mod with a newer `time_updated` is reported as updated

No manual mod ID configuration is needed — the list is always read from the server config file.

## Notification format

```
🔧 Mods updated — server restart recommended:
• Mod Name — https://steamcommunity.com/sharedfiles/filedetails/?id=123456789
• Another Mod — https://steamcommunity.com/sharedfiles/filedetails/?id=987654321
```

If the list exceeds Discord's 2000-character message limit, it is split into multiple messages.

## State file

`workshop_state.json` is created automatically in the bot's working directory. It stores the last known `time_updated` for each monitored mod. Delete it to force a full re-check on next startup (useful for testing).
