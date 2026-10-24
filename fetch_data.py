"""Hakee Liigan runkosarjan ottelut liiga.fi:n rajapinnasta ja tallentaa games.json."""
import json
import sys
from pathlib import Path

import requests

SEASON = 2027  # kausi 2026-27
URL = "https://liiga.fi/api/v2/games"
OUT = Path(__file__).with_name("games.json")


def fetch(season: int = SEASON) -> list[dict]:
    r = requests.get(URL, params={"tournament": "runkosarja", "season": season}, timeout=30)
    r.raise_for_status()
    games = []
    for g in r.json():
        games.append({
            "id": g["id"],
            "start": g["start"],
            "home": g["homeTeam"]["teamName"],
            "away": g["awayTeam"]["teamName"],
            "home_goals": g["homeTeam"]["goals"],
            "away_goals": g["awayTeam"]["goals"],
            "ended": bool(g["ended"]),
            "finished_type": g["finishedType"],
        })
    return games


if __name__ == "__main__":
    season = int(sys.argv[1]) if len(sys.argv) > 1 else SEASON
    games = fetch(season)
    OUT.write_text(json.dumps(games, ensure_ascii=False, indent=1), encoding="utf-8")
    played = sum(g["ended"] for g in games)
    print(f"{len(games)} ottelua, pelattu {played}, tallennettu {OUT}")
