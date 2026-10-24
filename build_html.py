"""Tekee result.json:sta report.html (taulukko + palkkikaavio)."""
import json
from datetime import datetime
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
rows = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
games = json.loads((HERE / "games.json").read_text(encoding="utf-8"))
played = sum(g["ended"] for g in games)


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
<p>Monte Carlo -simulaatio, pelattu {played}/{len(games)} ottelua. Kolme heikointa putoaa. Päivitetty {datetime.now():%d.%m.%Y %H:%M}.</p>
<table><thead><tr><th>#</th><th class="l">Joukkue</th><th>O</th><th>P</th><th>+/−</th><th>Odotettu P</th><th>Odotettu sij.</th><th class="l">Putoamis-%</th></tr></thead>
<tbody>{table_rows}</tbody></table>
<p class="legend">Viivat sijojen 4, 12 ja 14 jälkeen. Sijat 15–17 putoavat. Taulukko on nykyisessä sarjajärjestyksessä (pisteet, vähemmän pelatut, maaliero).</p>
<h2>Odotettu loppusijoitus</h2>
<p>Joukkueet simulaation odotettujen runkosarjapisteiden mukaan.</p>
<table><thead><tr><th>#</th><th class="l">Joukkue</th><th>P nyt</th><th>Odotettu P</th><th>Odotettu sij.</th><th class="l">Putoamis-%</th></tr></thead>
<tbody>{exp_rows}</tbody></table>
</main></body></html>"""

out = HERE / "report.html"
out.write_text(html, encoding="utf-8")
print(out)
