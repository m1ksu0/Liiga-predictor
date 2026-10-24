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

Aja neljä vaihetta järjestyksessä (virtuaaliympäristö aktivoituna):

```bash
python fetch_data.py
python simulate.py --sims 20000
python append_history.py
python build_html.py
```

1. `fetch_data.py` hakee otteluohjelman ja tulokset tiedostoon `games.json`.
2. `simulate.py` ajaa simulaation, tulostaa taulukon ja kirjoittaa `result.json`. Valinta `--sims` määrää simulaatioiden määrän (oletus 20 000).
3. `append_history.py` lisää tilannekuvan tiedostoon `data/history.csv`, jos pelattujen otteluiden määrä on muuttunut.
4. `build_html.py` tekee `report.html`:n, jossa myös putoamisriskin kehityskaavio historiasta. Avaa se selaimessa.

Aja uudelleen aina, kun uusia otteluita on pelattu.

Windowsin konsolissa ääkköset voivat näkyä väärin. Korjaus: aseta `PYTHONIOENCODING=utf-8`.

## Automaattinen päivitys (GitHub Actions + Pages)

Työnkulku `.github/workflows/update.yml` ajetaan joka yö kello 04:00 UTC. Se hakee datan, simuloi, lisää historiaan uuden tilannekuvan (vain jos otteluita on pelattu lisää, ja commitoi sen repoon) ja julkaisee raportin GitHub Pagesiin.

Käyttöönotto kerran: repon **Settings → Pages → Build and deployment → Source: GitHub Actions**. Sen jälkeen työnkulun voi ajaa heti käsin välilehdeltä **Actions → Päivitä Liiga-ennuste → Run workflow**. Sivun osoite on `https://<käyttäjä>.github.io/<repo>/`.

## Miten malli toimii

1. **Nykytila.** Pelatuista otteluista lasketaan pisteet (3-2-1-0), maalit ja ottelumäärät.
2. **Voimatasot.** Jokaiselle joukkueelle arvioidaan hyökkäys- ja puolustuskerroin sekä yhteinen kotietu. Vastustajien taso huomioidaan iteroimalla. Pienen otoksen luvut vedetään kohti ennakkoa (`SHRINK`, 18 pseudo-ottelua), joka tulee pelaajabudjetista (katso alla). Kauden edetessä pelatut ottelut painavat yhä enemmän ja budjetin vaikutus pienenee.
3. **Simulointi.** Jokainen jäljellä oleva ottelu arvotaan Poisson-jakaumalla. Joukkueiden voimat arvotaan jokaisessa simuloinnissa uudelleen estimaatin ympäriltä, jotta epävarmuus näkyy tuloksissa. Tasapelit ratkaistaan jatkoajalla tai rankkareilla voimasuhteen mukaan.
4. **Sijoitus.** Jokaisen simuloidun kauden joukkueet järjestetään pisteiden, maalieron ja tehtyjen maalien mukaan. Tasatilanteessa ratkaisee arpa.
5. **Tulokset.** Putoamis-% on osuus simuloinneista, joissa joukkue jäi kolmen viimeisen joukkoon. Odotetut pisteet ja sijoitus ovat simulaatioiden keskiarvoja.

## Pelaajabudjetit ennakkotietona

Pelaajabudjetit (`budgets.py`) kertovat jotain joukkueen todellisesta tasosta, joten malli ei lähde jokaisen joukkueen kohdalla liigan keskiarvosta vaan budjetin ennustamasta tasosta. Budjetti on vain ennakko: kun otteluita kertyy, tulokset ohjaavat arviota.

**Kerroin `BETA` = 0,3** (maalieroa per ottelu per budjettimiljoona). Sen merkitys käytännössä: joukkue, jonka budjetti on miljoona euroa keskiarvoa suurempi, on ennakkoon noin 0,3 maalia per ottelu vahvempi. Maalimäärän keskiarvolla se vastaa noin 0,15 pistettä per ottelu.

Kertoimen perustelu:
- Mittasin budjetin yhteyden loppusijoituksiin kausilta 2024–25 ja 2025–26 (16 joukkuetta per kausi). Budjetti selitti 13–18 % pistemäärien vaihtelusta (R² 0,13–0,18). Kulmakertoimet olivat 0,36 ja 0,51 maalieroa per ottelu per miljoona.
- Käytössä on näiden keskiarvoa (noin 0,43) varovaisempi 0,3, koska otos on vain kaksi kautta ja budjetit ovat seurojen ilmoittamia lukuja.
- Käytännössä budjetti **ei määrää** tuloksia: noin 85 % joukkueiden välisistä eroista tulee muista tekijöistä. Se on kuitenkin parempi lähtöarvaus kuin keskiarvo, kun otteluita on vasta 15.

Budjettien vaikutus nykytilanteessa on suurin joukkueille, joiden budjetti ja tulokset ovat ristiriidassa (esim. iso budjetti mutta huonot tulokset: putoamisriski laskee). Voit tutkia herkkyyttä ajamalla `python sensitivity_budget.py`, joka näyttää putoamis-%:t eri kertoimilla (0, 0,2, 0,3, 0,4, 0,6). Arvon 0 voi asettaa tiedostossa `budgets.py`, jos haluat poistaa budjetit käytöstä.

Uuden kauden alussa päivitä `BUDGET` tiedostossa `budgets.py` ja harkitse kertoimen mittaamista uudelleen.

**Huomio historiasta:** `data/history.csv`:n varhaisimmat tilannekuvat on laskettu ilman budjetteja. Kaaviossa näkyy siksi hyppy kohdassa, jossa budjetit otettiin käyttöön.

## Tiedostot

| Tiedosto | Sisältö |
|---|---|
| `fetch_data.py` | Hakee ottelut rajapinnasta tiedostoon `games.json` |
| `simulate.py` | Voimatasojen sovitus ja Monte Carlo -simulaatio |
| `budgets.py` | Pelaajabudjetit ja kerroin `BETA` |
| `sensitivity_budget.py` | Herkkyysanalyysi: putoamis-% eri budjettikertoimilla |
| `append_history.py` | Tallentaa tilannekuvan tiedostoon `data/history.csv` |
| `build_html.py` | Tekee `report.html`:n tuloksista ja historiasta |
| `.github/workflows/update.yml` | Ajastettu päivitys ja julkaisu GitHub Pagesiin |
| `data/history.csv` | Putoamisriskin historia (versionhallinnassa) |
| `requirements.txt` | Python-riippuvuudet (`numpy`, `requests`, `tzdata`) |

`games.json`, `result.json` ja `report.html` generoidaan ajossa eikä niitä tallenneta repoon.

## Rajoitukset

- Malli käyttää vain tämän kauden pelatuista otteluista saatuja maaleja. Se ei tunne pelaajia, loukkaantumisia eikä maaliodottamia. Aiempia kausia on käytetty vain budjettikertoimen mittaamiseen.
- Mallia ei ole validoitu historiadatalla, joten luvut ovat arvioita eivätkä tarkkoja ennusteita.
- Putoamissääntönä on kolme viimeistä suoraan (`RELEGATED` tiedostossa `simulate.py`). Tasapisteissä sijoitus ratkeaa maalieron ja tehtyjen maalien mukaan.
- Kausi ja joukkuemäärä on kiinteä. Kauden voi vaihtaa komentoriviltä (`python fetch_data.py <kausi>`), mutta putoajien määrä ja muut säännöt on muutettava koodiin.
