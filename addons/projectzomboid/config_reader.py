import re


def parse_workshop_ids(ini_content: str) -> list[str]:
    """Extract Workshop IDs from the contents of a servertest.ini file."""
    for line in ini_content.splitlines():
        match = re.match(r"^\s*WorkshopItems\s*=\s*(.+)", line)
        if match:
            raw = match.group(1).strip()
            return [mid.strip() for mid in raw.split(";") if mid.strip()]
    return []


def read_workshop_ids(amp_client, server_config_path: str) -> list[str]:
    """
    Read servertest.ini via the AMP API and return the list of Workshop IDs.
    amp_client: AmpClient instance configured with instance_id
    server_config_path: relative path within the instance (e.g. "Zomboid/Server/servertest.ini")
    """
    try:
        content = amp_client.read_file(server_config_path)
        return parse_workshop_ids(content)
    except Exception as e:
        print(f"[pz/config_reader] Error reading config via API: {e}")
        return []
