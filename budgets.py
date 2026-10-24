"""Pelaajabudjetit ennakkotietona voimatasoille.

BUDGET: kauden 2026-27 pelaajabudjetit (milj. euroa). Päivitä aina uuden kauden alussa.
BETA: budjetin vaikutus maalieroon, maalia per ottelu per budjettimiljoona.
  Mitattu kausilta 2024-25 (0,36) ja 2025-26 (0,51); käytössä varovaisempi 0,3.
  Arvo 0 poistaa budjetit käytöstä (ennakko on liigan keskiarvo).
Joukkue, jolta budjetti puuttuu, saa keskimääräisen ennakon.
"""
BETA = 0.3

BUDGET = {
    "HIFK": 4.0, "Kärpät": 3.9, "Jokerit": 3.737, "Tappara": 3.72, "Lukko": 3.65,
    "Ilves": 3.45, "JYP": 3.3, "KalPa": 3.0, "K-Espoo": 3.0, "TPS": 3.0,
    "Pelicans": 2.6, "SaiPa": 2.5, "Ässät": 2.45, "Sport": 2.416, "HPK": 2.2,
    "KooKoo": 2.2, "Jukurit": 1.8,
}
