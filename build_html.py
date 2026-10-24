"""Tekee result.json:sta ja data/history.csv:sta report.html (taulukot + kaaviot)."""
import csv
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
rows = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
games = json.loads((HERE / "games.json").read_text(encoding="utf-8"))
played = sum(g["ended"] for g in games)

PALETTE = ["#d64545", "#2f7fd1", "#e69f00", "#2a9d6f", "#8e5bd0", "#d1568e", "#6b7280", "#17a2b8"]


def load_history():
    path = HERE / "data" / "history.csv"
    if not path.exists():
        return {}
    series = {}  # joukkue -> [(pvm, putoamis-%)]
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            series.setdefault(r["team"], []).append(
                (date.fromisoformat(r["date"]), float(r["relegation"])))
    return series


def history_chart(series, max_lines=8):
    dates = sorted({d for pts in series.values() for d, _ in pts})
    if len(dates) < 2:
        return "<p>Kehityskaavio ilmestyy, kun tilannekuvia on kertynyt vähintään kaksi.</p>"
    # näytetään joukkueet, joilla on ollut suurin putoamisriski
    teams = sorted(series, key=lambda t: -max(v for _, v in series[t]))[:max_lines]
    W, H, L, R, T, B = 720, 320, 44, 96, 12, 30
    x0, x1 = dates[0].toordinal(), dates[-1].toordinal()
    X = lambda d: L + (d.toordinal() - x0) / (x1 - x0) * (W - L - R)
    Y = lambda v: T + (1 - v) * (H - T - B)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Putoamisriskin kehitys" '
           f'style="width:100%;height:auto;font:12px system-ui,sans-serif">']
    for v in (0, .25, .5, .75, 1):
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--line)"/>'
                   f'<text x="{L-6}" y="{Y(v)+4:.1f}" text-anchor="end" fill="var(--mut)">{int(v*100)} %</text>')
    for d in sorted({dates[0], dates[len(dates) // 2], dates[-1]}):
        out.append(f'<text x="{X(d):.1f}" y="{H-8}" text-anchor="middle" fill="var(--mut)">{d:%d.%m.}</text>')
    labels = []
    for i, t in enumerate(teams):
        c = PALETTE[i % len(PALETTE)]
        pts = " ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in series[t])
        out.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2" '
                   f'stroke-linejoin="round"/>')
        d, v = series[t][-1]
        labels.append([Y(v), t, c, v])
    labels.sort()  # estä päällekkäiset nimet viivojen päässä
    for k in range(1, len(labels)):
        labels[k][0] = max(labels[k][0], labels[k - 1][0] + 14)
    for y, t, c, v in labels:
        out.append(f'<text x="{W-R+6}" y="{y+4:.1f}" fill="{c}" font-weight="600">'
                   f'{escape(t)} {v*100:.0f} %</text>')
    out.append("</svg>")
    return "".join(out)


chart = history_chart(load_history())


def bar(p):
    return (f'<div class="bar"><div class="fill" style="width:{p*100:.1f}%"></div>'
            f'<span>{p*100:.1f} %</span></div>')


rows.sort(key=lambda r: (-r["pts"], r["gp"], -r["gd"]))
CUTS = {4: "cut4", 12: "cut12", 14: "cut14"}  # viiva rivin jälkeen

table_rows = "".join(
    f"<tr class='{CUTS.get(i, '')}'><td>{i}</td><td class='l'>{escape(r['team'])}</td><td>{r['gp']}</td><td>{r['pts']}</td>"
    f"<td>{r['gd']:+d}</td><td>{r['exp_pts']:.1f}</td><td>{r['exp_rank']:.1f}</td>"
    f"<td class='l w'>{bar(r['relegation'])}</td></tr>"
    for i, r in enumerate(rows, 1)
)

exp_rows = "".join(
    f"<tr class='{CUTS.get(i, '')}'><td>{i}</td><td class='l'>{escape(r['team'])}</td>"
    f"<td>{r['pts']}</td><td>{r['exp_pts']:.1f}</td><td>{r['exp_rank']:.1f}</td>"
    f"<td class='l w'>{bar(r['relegation'])}</td></tr>"
    for i, r in enumerate(sorted(rows, key=lambda r: -r["exp_pts"]), 1)
)

html = f"""<!doctype html>
<html lang="fi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Liiga putoamisriski</title>
<style>
:root{{--bg:#fff;--fg:#1c1f24;--mut:#6b7280;--line:#e5e7eb;--bar:#d64545;--track:#f1f2f4}}
@media(prefers-color-scheme:dark){{:root{{--bg:#16181c;--fg:#e8eaed;--mut:#9aa0a6;--line:#2c3036;--bar:#e5645f;--track:#23262b}}}}
body{{margin:0;padding:24px 16px;background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,sans-serif}}
main{{max-width:860px;margin:auto}}
h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:18px;margin:32px 0 4px}} p{{color:var(--mut);margin:0 0 20px}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:7px 8px;text-align:right;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}}
th{{font-size:12px;color:var(--mut);font-weight:600}} .l{{text-align:left}} .w{{width:40%}}
.bar{{position:relative;height:22px;background:var(--track);border-radius:4px;overflow:hidden}}
.fill{{height:100%;background:var(--bar)}}
.bar span{{position:absolute;left:8px;top:2px;font-size:13px;font-weight:600}}
tr.cut4 td,tr.cut12 td,tr.cut14 td{{border-bottom:2px solid var(--fg)}}
.legend{{font-size:13px;color:var(--mut);margin:12px 0 0}}
@media(max-width:600px){{th:nth-child(n+6):not(:last-child),td:nth-child(n+6):not(:last-child){{display:none}}.w{{width:55%}}}}
</style></head><body><main>
<h1>Liiga 2026–27: putoamisriski</h1>
<p>Monte Carlo -simulaatio, pelattu {played}/{len(games)} ottelua. Kolme heikointa putoaa. Päivitetty {datetime.now(ZoneInfo('Europe/Helsinki')):%d.%m.%Y %H:%M}.</p>
<table><thead><tr><th>#</th><th class="l">Joukkue</th><th>O</th><th>P</th><th>+/−</th><th>Odotettu P</th><th>Odotettu sij.</th><th class="l">Putoamis-%</th></tr></thead>
<tbody>{table_rows}</tbody></table>
<p class="legend">Viivat sijojen 4, 12 ja 14 jälkeen. Sijat 15–17 putoavat. Taulukko on nykyisessä sarjajärjestyksessä (pisteet, vähemmän pelatut, maaliero).</p>
<h2>Odotettu loppusijoitus</h2>
<p>Joukkueet simulaation odotettujen runkosarjapisteiden mukaan.</p>
<table><thead><tr><th>#</th><th class="l">Joukkue</th><th>P nyt</th><th>Odotettu P</th><th>Odotettu sij.</th><th class="l">Putoamis-%</th></tr></thead>
<tbody>{exp_rows}</tbody></table>
<h2>Putoamisriskin kehitys</h2>
<p>Putoamistodennäköisyys tilannekuvittain (suurimman riskin joukkueet).</p>
{chart}
</main></body></html>"""

out = HERE / "report.html"
out.write_text(html, encoding="utf-8")
print(out)
