"""
Loads global configuration (config.yaml) and all instances (instances/*.yaml).
Applies defaults to optional fields of each instance.
Resolves ${ENV_VAR} references in string values.
"""
import os
import re
from pathlib import Path

import yaml

# ------------------------------------------------------------------ #
#  Paths                                                               #
# ------------------------------------------------------------------ #

_BASE_DIR = Path(__file__).parent
_CONFIG_FILE = _BASE_DIR / "config.yaml"
_INSTANCES_DIR = _BASE_DIR / "instances"

# ------------------------------------------------------------------ #
#  Instance field defaults                                             #
# ------------------------------------------------------------------ #

_INSTANCE_DEFAULTS = {
    "emoji": "🎮",
    "channel_commands": "server-commands",
    "channel_notifications": "server-notifications",
    "addon": None,
    "addon_config": {},
}

_ADDON_CONFIG_DEFAULTS = {
    "projectzomboid": {
        "server_config_path": "Zomboid/Server/servertest.ini",
        "workshop_check_interval": 1800,
    },
}

# ------------------------------------------------------------------ #
#  Loaders                                                             #
# ------------------------------------------------------------------ #

_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_vars(value):
    """
    Recursively resolve ${ENV_VAR} references in strings within a dict/list.
    Raises ValueError if a referenced variable is not set.
    """
    if isinstance(value, str):
        def replace(match):
            var = match.group(1)
            if var not in os.environ:
                raise ValueError(f"Environment variable '{var}' is not set")
            return os.environ[var]
        return _ENV_VAR_RE.sub(replace, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(v) for v in value]
    return value


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return _resolve_env_vars(data)


def _apply_instance_defaults(data: dict, filename: str) -> dict:
    """Apply defaults to an instance dict. Modifies in-place and returns it."""
    # name: default = filename without extension
    if "name" not in data:
        data["name"] = Path(filename).stem

    for key, default in _INSTANCE_DEFAULTS.items():
        if key not in data:
            data[key] = default

    # Defaults inside addon_config based on the chosen addon
    addon = data.get("addon")
    if addon and addon in _ADDON_CONFIG_DEFAULTS:
        addon_defaults = _ADDON_CONFIG_DEFAULTS[addon]
        cfg = data.get("addon_config") or {}
        for key, default in addon_defaults.items():
            if key not in cfg:
                cfg[key] = default
        data["addon_config"] = cfg

    return data


def _validate_instance(data: dict, filename: str):
    required = ["amp_url", "amp_user", "amp_pass", "instance_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        raise ValueError(
            f"Instance '{filename}' is missing required fields: {', '.join(missing)}"
        )


def load_instances(global_admin_role: str) -> list[dict]:
    """Load and validate all instances from instances/*.yaml."""
    instances = []
    if not _INSTANCES_DIR.exists():
        return instances
    for path in sorted(_INSTANCES_DIR.glob("*.yaml")):
        data = _load_yaml(path)
        _apply_instance_defaults(data, path.name)
        # admin_role: falls back to global if not set per-instance
        if "admin_role" not in data:
            data["admin_role"] = global_admin_role
        _validate_instance(data, path.name)
        instances.append(data)
    return instances


def load_config() -> dict:
    """Load config.yaml and validate required fields."""
    if not _CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {_CONFIG_FILE}")
    data = _load_yaml(_CONFIG_FILE)
    if not data.get("discord_token"):
        raise ValueError("config.yaml: missing 'discord_token'")
    if not data.get("admin_role"):
        data["admin_role"] = "Server Admin"
    return data


# ------------------------------------------------------------------ #
#  Global access                                                       #
# ------------------------------------------------------------------ #

_config = load_config()
_servers = load_instances(_config["admin_role"])

DISCORD_TOKEN: str = _config["discord_token"]
ADMIN_ROLE: str = _config["admin_role"]
SERVERS: list[dict] = _servers
