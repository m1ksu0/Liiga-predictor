# Liiga putoamisriski

Monte Carlo -simulaatio, joka laskee SM-liigan kauden 2026–27 putoamistodennäköisyydet. Kaudella on 17 joukkuetta, 64 runkosarjaottelua per joukkue, ja kolme heikointa putoaa suoraan.

Data haetaan Liigan rajapinnasta (`https://liiga.fi/api/v2/games`). Tulokset tallentuvat HTML-raportiksi (`report.html`), jossa on sarjataulukko, putoamis-% ja odotettu loppusijoitus.

## Vaatimukset

- Python 3.10 tai uudempi
- Internet-yhteys (datan haku)

## Asennus

Luo virtuaaliympäristö ja asenna riippuvuudet.

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Windows (Git Bash):

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Jos PowerShell estää aktivoinnin, aja kerran: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Ympäristön voi myös jättää aktivoimatta ja kutsua Pythonia suoraan, esim. `.venv/Scripts/python fetch_data.py`.

## Ajaminen

Aja kolme vaihetta järjestyksessä (virtuaaliympäristö aktivoituna):

```bash
python fetch_data.py
python simulate.py --sims 20000
python build_html.py
```

1. `fetch_data.py` hakee otteluohjelman ja tulokset tiedostoon `games.json`.
2. `simulate.py` ajaa simulaation, tulostaa taulukon ja kirjoittaa `result.json`. Valinta `--sims` määrää simulaatioiden määrän (oletus 20 000).
3. `build_html.py` tekee `result.json`:sta tiedoston `report.html`. Avaa se selaimessa.

Aja uudelleen aina, kun uusia otteluita on pelattu.

Windowsin konsolissa ääkköset voivat näkyä väärin. Korjaus: aseta `PYTHONIOENCODING=utf-8`.

## Miten malli toimii

1. **Nykytila.** Pelatuista otteluista lasketaan pisteet (3-2-1-0), maalit ja ottelumäärät.
2. **Voimatasot.** Jokaiselle joukkueelle arvioidaan hyökkäys- ja puolustuskerroin sekä yhteinen kotietu. Vastustajien taso huomioidaan iteroimalla, ja pienen otoksen luvut vedetään kohti keskiarvoa (`SHRINK`).
3. **Simulointi.** Jokainen jäljellä oleva ottelu arvotaan Poisson-jakaumalla. Joukkueiden voimat arvotaan jokaisessa simuloinnissa uudelleen estimaatin ympäriltä, jotta epävarmuus näkyy tuloksissa. Tasapelit ratkaistaan jatkoajalla tai rankkareilla voimasuhteen mukaan.
4. **Sijoitus.** Jokaisen simuloidun kauden joukkueet järjestetään pisteiden, maalieron ja tehtyjen maalien mukaan. Tasatilanteessa ratkaisee arpa.
5. **Tulokset.** Putoamis-% on osuus simuloinneista, joissa joukkue jäi kolmen viimeisen joukkoon. Odotetut pisteet ja sijoitus ovat simulaatioiden keskiarvoja.

## Tiedostot

| Tiedosto | Sisältö |
|---|---|
| `fetch_data.py` | Hakee ottelut rajapinnasta tiedostoon `games.json` |
| `simulate.py` | Voimatasojen sovitus ja Monte Carlo -simulaatio |
| `build_html.py` | Tekee `report.html`:n tuloksista |
| `requirements.txt` | Python-riippuvuudet (`numpy`, `requests`) |

`games.json`, `result.json` ja `report.html` generoidaan ajossa.

## Rajoitukset

- Malli käyttää vain tämän kauden pelatuista otteluista saatuja maaleja. Se ei tunne pelaajia, loukkaantumisia, aiempia kausia eikä maaliodottamia.
- Mallia ei ole validoitu historiadatalla, joten luvut ovat arvioita eivätkä tarkkoja ennusteita.
- Putoamissääntönä on kolme viimeistä suoraan (`RELEGATED` tiedostossa `simulate.py`). Tasapisteissä sijoitus ratkeaa maalieron ja tehtyjen maalien mukaan.
- Kausi ja joukkuemäärä on kiinteä. Kauden voi vaihtaa komentoriviltä (`python fetch_data.py <kausi>`), mutta putoajien määrä ja muut säännöt on muutettava koodiin.
