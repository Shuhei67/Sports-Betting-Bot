import os

from dotenv import load_dotenv
import requests
import pandas as pd



load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SPORTS = [
    "soccer_epl",
    "soccer_france_ligue_one",
    "soccer_france_ligue_two",
    "soccer_germany_bundesliga",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "basketball_nba",
    "boxing_boxing",
    "icehockey_nhl",
]
BOOKMAKERS = ["betclic_fr", "winamax_fr", "pmu_fr", "unibet_fr", "betfair_ex_eu", "williamhill", "sport888"]



# Vérifie le nombre de requêtes API restantes avant de lancer le bot
# Return True si il reste des crédits
def check_credits():

    url = f"{BASE_URL}/sports"
    params = {"apiKey": API_KEY}
    response = requests.get(url, params = params)
    remaining = int(response.headers.get("x-requests-remaining"))
    
    
    if remaining > 0:
        print(50 * "-")
        print(f"Requêtes API restantes : {remaining}")
        print(50 * "-")
        return True
    else:
        print("Plus de crédit API disponible, arrêt du bot.")
        return False


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


# Transforme les données brutes récupérer en DataFrame pandas pour "analyse"
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


# Détecte opportunité de surebet, si oui on stocke les infos pour les envoyer sur Telegram
def detect_surebet(df):
    
    opportunities = []

    for match_name, group in df.groupby("match"):  # On regroupe les lignes par match

        # On cherche la ligne avec la meilleure cote pour chaque issue
        # On accède a la meilleure cote ET au bookmaker pour l'envoyer sur Telegram
        best_home_row = group.loc[group["home_odds"].idxmax()]
        best_draw_row = group.loc[group["draw_odds"].idxmax()]
        best_away_row = group.loc[group["away_odds"].idxmax()]

        best_home = best_home_row["home_odds"]
        best_draw = best_draw_row["draw_odds"]
        best_away = best_away_row["away_odds"]

        # Formule mathématique du surebet :
        margin = (1/best_home) + (1/best_draw) + (1/best_away)

        if margin < 1:
            opportunities.append({
                "match": match_name,
                "margin": round(margin, 4),
                "profit": round((1 - margin) * 100, 2),  # Profit en %
                "best_home_book": best_home_row["bookmaker"],  # Bookmaker qui propose cette cote
                "best_draw": best_draw,
                "best_draw_book": best_draw_row["bookmaker"],
                "best_away": best_away,
                "best_away_book": best_away_row["bookmaker"],
            })

    return opportunities


# Fonction qui envoie le message sur Telegram en utilisant le token et chat_id du bot Telegram
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, params=params)
    
    if response.status_code == 200:
        print("Message Telegram envoyé !")
    else:
        print(f"Erreur Telegram : {response.status_code} : {response.text}")


# Format du message à envoyer sur Telegram avec les infos de l'opportunité de surebet
def format_surebet_message(opportunity):

    message = (
        f"⚡️ SUREBET ⚡️\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏆 {opportunity['match']}\n"
        f"💸 +{opportunity['profit']}% de profit garanti\n\n"
        f"🏠 Mise sur DOMICILE\n"
        f"   {opportunity['best_home']} chez {opportunity['best_home_book']}\n\n"
        f"🤝 Mise sur NUL\n"
        f"   {opportunity['best_draw']} chez {opportunity['best_draw_book']}\n\n"
        f"✈️ Mise sur EXTÉRIEUR\n"
        f"   {opportunity['best_away']} chez {opportunity['best_away_book']}\n"
        f"━━━━━━━━━━━━━━━"
    )

    return message



if check_credits():

    all_opportunities = []

    for sport in SPORTS:  # On boucle sur tous les sports qu'on a choisi
        odds_data = get_odds(sport)

        if not odds_data:  # Si pour un sport on a pas de données pas grave on continue
            continue       # plutot que de faire planter le script entier
        
        df = parse_odds(odds_data)
        opportunities = detect_surebet(df)
        all_opportunities.extend(opportunities)

    if all_opportunities:
        for o in all_opportunities:
            send_telegram(format_surebet_message(o))
    else:
        print("Aucun surebet détecté")



'''
Avec ça on peut tester l'envoi du message Telegram même sans surebet :

fake = {
    "match": "PSG vs Marseille",
    "profit": 2.5,
    "best_home": 2.10,
    "best_home_book": "Betclic (FR)",
    "best_draw": 3.60,
    "best_draw_book": "Winamax (FR)",
    "best_away": 4.50,
    "best_away_book": "PMU (FR)",
}
send_telegram(format_surebet_message(fake))
'''

'''
Fonction qui affiche la liste des bookmakers avec leurs clés, j'en ai eu besoin pour remplir la liste BOOKMAKERS
ET également pour vérifier auxquels j'ai accès dans la liste depuis la France
La fonction ne sert plus une fois le bot configuré mais pratique de la garder pour l'avenir :

def get_available_bookmakers():

    bookmakers = set()
    
    for sport in SPORTS:
        odds_data = get_odds(sport)
        for match in odds_data:
            for bookmaker in match["bookmakers"]:
                bookmakers.add((bookmaker["key"], bookmaker["title"]))
    
    print("Bookmakers disponibles sur l'API :")
    for key, title in sorted(bookmakers):
        print(f"{title} → clé : {key}")
'''