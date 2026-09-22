import json
import os
import requests

STEAM_API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
STATE_FILE = "workshop_state.json"


def fetch_mod_details(mod_ids: list[str]) -> dict:
    """Consulta la Steam API y devuelve {mod_id: {"title": ..., "time_updated": ...}}"""
    if not mod_ids:
        return {}
    data = {"itemcount": len(mod_ids)}
    for i, mod_id in enumerate(mod_ids):
        data[f"publishedfileids[{i}]"] = mod_id

    r = requests.post(STEAM_API_URL, data=data, timeout=15)
    r.raise_for_status()

    result = {}
    for item in r.json()["response"].get("publishedfiledetails", []):
        result[item["publishedfileid"]] = {
            "title": item.get("title", item["publishedfileid"]),
            "time_updated": item.get("time_updated", 0),
        }
    return result


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def check_for_updates(mod_ids: list[str]) -> list[dict]:
    """
    Compara los time_updated actuales con los guardados.
    Devuelve lista de mods actualizados: [{"id": ..., "title": ...}, ...]
    """
    current = fetch_mod_details(mod_ids)
    previous = load_state()
    updated = []

    for mod_id, info in current.items():
        prev_time = previous.get(mod_id, {}).get("time_updated", 0)
        if info["time_updated"] > prev_time:
            updated.append({"id": mod_id, "title": info["title"]})

    save_state({mod_id: info for mod_id, info in current.items()})
    return updated
