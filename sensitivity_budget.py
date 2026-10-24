"""Herkkyysanalyysi: putoamis-% eri budjettikertoimilla (BETA).

Ajaa simulate.py:n mallin usealla BETA-arvolla (budgets.py) ja vertaa tuloksia
tilanteeseen ilman budjetteja (BETA = 0). Ei kirjoita mitään tiedostoihin.
"""
import simulate as sim
from budgets import BETA as DEFAULT_BETA

BETAS = [0.0, 0.2, DEFAULT_BETA, 0.4, 0.6]
N_SIMS = 20000


def main():
    teams, idx, played, todo = sim.load()
    results = {}
    try:
        for beta in sorted(set(BETAS)):
            sim.BETA = beta
            results[beta] = {r["team"]: r for r in sim.report(teams, idx, played, todo, N_SIMS)}
    finally:
        sim.BETA = DEFAULT_BETA

    betas = sorted(results)
    pts0 = sim.standings(teams, idx, played)[0]
    order = sorted(teams, key=lambda t: -results[DEFAULT_BETA][t]["relegation"])
    print(f"Putoamis-% eri BETA-arvoilla ({N_SIMS} simulaatiota; käytössä {DEFAULT_BETA})\n")
    print(f"{'Joukkue':<10}{'Budj.':>6}{'P':>4}" + "".join(f"{'b='+str(b):>9}" for b in betas)
          + f"{'muutos':>9}")
    for t in order:
        vals = [results[b][t]["relegation"] * 100 for b in betas]
        print(f"{t:<10}{sim.BUDGET.get(t, float('nan')):>6.2f}{int(pts0[teams.index(t)]):>4}"
              + "".join(f"{v:>8.1f}%" for v in vals)
              + f"{results[DEFAULT_BETA][t]['relegation']*100 - vals[0]:>+8.1f}")
    print(f"\n'muutos' = käytössä oleva BETA vs. ei budjetteja (prosenttiyksikköä)")


if __name__ == "__main__":
    main()
