# Meciuri AI Desktop

Aplicatie desktop Windows/Python pentru a cauta meciuri de fotbal cu probabilitate mare de victorie, inclusiv filtre pentru double chance si goluri.

## Ce include

- cautare de meciuri dintr-un API real de odds (The Odds API)
- fallback la date demo daca API-ul nu este configurat
- filtru pentru probabilitatea minima de victorie (ex: 70%)
- filtru pentru liga / competitie
- filtru pentru market de goluri (Over 1.5, Over 2.5, BTTS)
- tabela desktop cu rezultate si un panel de detalii
- export CSV
- suport pentru Windows si build .exe cu PyInstaller

## Important

Acest proiect este un instrument de analiza, nu un garantat de castig. Daca folosesti aceasta aplicatie pentru pariuri, fa-o doar ca sprijin informational si verifici datele in mod independent.

## Instalare pe Windows

1. Deschide CMD sau PowerShell in folderul proiectului.
2. Ruleaza:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configurare API reala

Copiaza `.env.example` in `.env` si completeaza:

```env
THE_ODDS_API_KEY=your_api_key_here
ODDS_SPORTS=soccer_epl,soccer_serie_a,soccer_bundesliga,soccer_laliga,soccer_ligue1
ODDS_REGION=uk
```

Daca nu setezi cheia, aplicatia va folosi date demo.

## Rulare desktop

```powershell
python main.py
```

## Rulare CLI

```powershell
python main.py --cli --source api --min-win-prob 0.7 --limit 10
```

## Build pentru Windows .exe

```powershell
.
\build_windows.ps1
```

Daca vrei, scriptul va genera un executabil in folderul `dist`.

## Exemple de rezultate

```json
[
  {
    "home_team": "Barcelona",
    "away_team": "Valencia",
    "league": "La Liga",
    "predicted_win_prob": 0.82,
    "double_chance_odds": 1.42,
    "goals_market": "Over 1.5"
  }
]
```
