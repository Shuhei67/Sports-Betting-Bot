import os

from dotenv import load_dotenv
import requests
import pandas as pd


load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"

SPORTS = [
    "soccer_epl",
    "soccer_ligue_1",
    "basketball_nba",
    "tennis_atp",
]
BOOKMAKERS = ["betclic_fr", "winamax_fr", "pmu_fr", "unibet_fr"]


# Récupère les cotes en format brut (JSON) pour être traité plus tard
def get_odds(sport):

    url = f"{BASE_URL}/sports/{sport}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()  # Retourne les données brutes pour être traiter
    else:
        print(f"Erreur {response.status_code} : {response.text}")
        return []  # Liste vide si erreur


# Transforme les données brutes en DataFrame pandas pour analyse
def parse_odds(odds_data):

    rows = []  

    for match in odds_data:
        home_team = match["home_team"]
        away_team = match["away_team"]
        match_name = f"{home_team} vs {away_team}"

        for bookmaker in match["bookmakers"]:
            if bookmaker["key"] not in BOOKMAKERS:  # Ignore ceux hors de ma liste
                continue

            for market in bookmaker["markets"]:  # Boucle sur les marchés du bookmaker
                if market["key"] != "h2h":  # Ignore si n'est pas "victoire / nul / défaite"
                    continue

                outcomes = {} # On crée un dict pour stocker les cotes de chaque issue (home, draw, away)
                for o in market["outcomes"]: # Pour chaque résulat dans le marché "h2h" ...
                    outcomes[o["name"]] = o["price"] # ... On récupère son nom et sa cote et on stocke dans le dict "outcomes"

                rows.append({  # On ajoute un dictionnaire à notre liste "rows" avec les infos gardées
                    "match": match_name,
                    "bookmaker": bookmaker["title"],
                    "home_odds": outcomes.get(home_team),
                    "draw_odds": outcomes.get("Draw"),
                    "away_odds": outcomes.get(away_team),
                })

    return pd.DataFrame(rows)  # On convertit la liste de dicts en DataFrame pandas


odds_data = get_odds("soccer_epl")
df = parse_odds(odds_data)
print(df.to_string())