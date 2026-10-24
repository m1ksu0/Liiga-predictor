"""Monte Carlo -simulaatio: Liigan putoamistodennäköisyydet.

Malli: kullekin joukkueelle hyökkäys- ja puolustuskerroin pelatuista otteluista
(shrinkage kohti keskiarvoa), kotietu erikseen. Maalit ~ Poisson. Tasatilanteessa
jatkoaika/rankkarit ratkaistaan voimasuhteilla painotetulla arvonnalla.
Pisteet: 3-2-1-0.
"""
import argparse
import json
from pathlib import Path

import numpy as np

DATA = Path(__file__).with_name("games.json")
RELEGATED = 3
# "pseudo-otteluiden" määrä kohti keskiarvoa. Estimoitu maaliero/ottelu-hajonnasta:
# kausi 26-27 ~15, 25-26 ~12, 24-25 ~27 -> 18
SHRINK = 18.0


def load(path: Path = DATA):
    games = json.loads(path.read_text(encoding="utf-8"))
    teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
    idx = {t: i for i, t in enumerate(teams)}
    played = [g for g in games if g["ended"]]
    todo = [g for g in games if not g["ended"]]
    return teams, idx, played, todo


def standings(teams, idx, played):
    n = len(teams)
    pts, gf, ga, gp = (np.zeros(n) for _ in range(4))
    for g in played:
        h, a = idx[g["home"]], idx[g["away"]]
        hg, ag = g["home_goals"], g["away_goals"]
        gp[h] += 1
        gp[a] += 1
        gf[h] += hg; ga[h] += ag
        gf[a] += ag; ga[a] += hg
        if g["finished_type"] == "ENDED_DURING_REGULAR_GAME_TIME":
            pts[h if hg > ag else a] += 3
        else:  # jatkoaika / voittolaukauskilpailu
            pts[h if hg > ag else a] += 2
            pts[a if hg > ag else h] += 1
    return pts, gf, ga, gp


def fit_strengths(n, idx, played):
    """Iteratiivinen hyökkäys/puolustus-sovitus kotietu huomioiden."""
    hg = np.mean([g["home_goals"] for g in played])
    ag = np.mean([g["away_goals"] for g in played])
    base = (hg + ag) / 2
    home_f, away_f = hg / base, ag / base
    att, dfn = np.ones(n), np.ones(n)
    for _ in range(100):
        num_a, den_a = np.full(n, SHRINK * base), np.full(n, SHRINK * base)
        num_d, den_d = np.full(n, SHRINK * base), np.full(n, SHRINK * base)
        for g in played:
            h, a = idx[g["home"]], idx[g["away"]]
            exp_h = base * home_f * att[h] * dfn[a]
            exp_a = base * away_f * att[a] * dfn[h]
            num_a[h] += g["home_goals"]; den_a[h] += exp_h / att[h]
            num_a[a] += g["away_goals"]; den_a[a] += exp_a / att[a]
            num_d[a] += g["home_goals"]; den_d[a] += exp_h / dfn[a]
            num_d[h] += g["away_goals"]; den_d[h] += exp_a / dfn[h]
        att, dfn = num_a / den_a, num_d / den_d
        att /= att.mean(); dfn /= dfn.mean()
    return att, dfn, base, home_f, away_f


def simulate(teams, idx, played, todo, n_sims=20000, seed=1):
    rng = np.random.default_rng(seed)
    n = len(teams)
    att, dfn, base, home_f, away_f = fit_strengths(n, idx, played)
    pts0, gf0, ga0, gp0 = standings(teams, idx, played)

    h =np.array([idx[g["home"]] for g in todo])
    a = np.array([idx[g["away"]] for g in todo])
    m = len(todo)
    # voimatasojen epävarmuus: jokaiseen simulaatioon oma otos joukkueiden voimista
    # (log-asteikon keskihajonta ~ 1/sqrt(base * (SHRINK + pelatut ottelut)))
    sd = 1 / np.sqrt(base * (SHRINK + gp0))
    eps_a = rng.normal(0, sd, size=(n_sims, n))
    eps_d = rng.normal(0, sd, size=(n_sims, n))
    lam_h = base * home_f * att[h] * dfn[a] * np.exp(eps_a[:, h] + eps_d[:, a])
    lam_a = base * away_f * att[a] * dfn[h] * np.exp(eps_a[:, a] + eps_d[:, h])

    hg = rng.poisson(lam_h, size=(n_sims, m))
    ag = rng.poisson(lam_a, size=(n_sims, m))
    tie = hg == ag
    # jatkoaika: voittaja voimasuhteen mukaan (kotietu mukana)
    p_home_ot = lam_h / (lam_h + lam_a)
    home_ot_win = rng.random((n_sims, m)) < p_home_ot
    home_win = np.where(tie, home_ot_win, hg > ag)
    reg = ~tie
    # tasatilanteessa voittaja saa maalin lisää (maaliero/GF)
    hg = np.where(tie & home_ot_win, hg + 1, hg)
    ag = np.where(tie & ~home_ot_win, ag + 1, ag)

    h_pts = np.where(home_win, np.where(reg, 3, 2), np.where(reg, 0, 1))
    a_pts = np.where(home_win, np.where(reg, 0, 1), np.where(reg, 3, 2))

    pts = np.tile(pts0, (n_sims, 1))
    gd = np.tile(gf0 - ga0, (n_sims, 1))
    gf = np.tile(gf0, (n_sims, 1))
    for j in range(m):
        pts[:, h[j]] += h_pts[:, j]
        pts[:, a[j]] += a_pts[:, j]
        gd[:, h[j]] += hg[:, j] - ag[:, j]
        gd[:, a[j]] += ag[:, j] - hg[:, j]
        gf[:, h[j]] += hg[:, j]
        gf[:, a[j]] += ag[:, j]

    # sijoitus: pisteet, maaliero, tehdyt maalit, arpa
    key = pts * 1e6 + gd * 1e3 + gf + rng.random((n_sims, n)) * 0.5
    order = np.argsort(-key, axis=1)
    rank = np.empty_like(order)
    rows = np.arange(n_sims)[:, None]
    rank[rows, order] = np.arange(1, n + 1)
    return pts, rank, att, dfn


def report(teams, idx, played, todo, n_sims):
    pts, rank, att, dfn = simulate(teams, idx, played, todo, n_sims)
    pts0, gf0, ga0, gp0 = standings(teams, idx, played)
    n = len(teams)
    rel = (rank > n - RELEGATED).mean(axis=0)
    rows = []
    for i, t in enumerate(teams):
        rows.append(dict(
            team=t, gp=int(gp0[i]), pts=int(pts0[i]), gd=int(gf0[i] - ga0[i]),
            exp_pts=float(pts[:, i].mean()), exp_rank=float(rank[:, i].mean()),
            att=float(att[i]), dfn=float(dfn[i]), relegation=float(rel[i]),
        ))
    rows.sort(key=lambda r: -r["relegation"])
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=20000)
    args = ap.parse_args()
    teams, idx, played, todo = load()
    rows = report(teams, idx, played, todo, args.sims)
    print(f"Pelattu {len(played)}, jäljellä {len(todo)}, simulaatioita {args.sims}")
    print(f"{'Joukkue':<16}{'O':>3}{'P':>4}{'+/-':>5}{'odP':>7}{'odSij':>7}{'Putoaa':>9}")
    for r in rows:
        print(f"{r['team']:<16}{r['gp']:>3}{r['pts']:>4}{r['gd']:>5}"
              f"{r['exp_pts']:>7.1f}{r['exp_rank']:>7.1f}{r['relegation']*100:>8.1f}%")
    Path(__file__).with_name("result.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
