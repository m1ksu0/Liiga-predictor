"""Lisää tuoreimman simulaation tulokset tiedostoon data/history.csv.

Uusi tilannekuva lisätään vain, jos pelattujen otteluiden määrä on muuttunut
edellisestä tilannekuvasta. Samalle päivälle tulee korkeintaan yksi tilannekuva
(uudempi korvaa saman päivän aiemman).
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
HISTORY = HERE / "data" / "history.csv"
FIELDS = ["date", "games_total", "team", "games_played", "points",
          "exp_points", "exp_rank", "relegation"]


def read_history() -> list[dict]:
    if not HISTORY.exists():
        return []
    with HISTORY.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
    games = json.loads((HERE / "games.json").read_text(encoding="utf-8"))
    total = sum(g["ended"] for g in games)
    today = datetime.now(timezone.utc).date().isoformat()

    history = read_history()
    if history and int(history[-1]["games_total"]) == total:
        print(f"Ei uusia otteluita ({total} pelattu), historiaa ei päivitetty")
        return

    history = [h for h in history if h["date"] != today]
    for r in sorted(rows, key=lambda r: r["team"]):
        history.append({
            "date": today, "games_total": total, "team": r["team"],
            "games_played": r["gp"], "points": r["pts"],
            "exp_points": f"{r['exp_pts']:.2f}", "exp_rank": f"{r['exp_rank']:.2f}",
            "relegation": f"{r['relegation']:.4f}",
        })
    HISTORY.parent.mkdir(exist_ok=True)
    with HISTORY.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(history)
    print(f"Historiaan lisätty tilannekuva {today} ({total} ottelua pelattu)")


if __name__ == "__main__":
    main()
