import os

from dotenv import load_dotenv
import requests

load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"  # URL de base pour accéder à l'API


def get_sports():
    
    url = f"{BASE_URL}/sports"  # URL pour récupérer les sports dispo
    params = {"apiKey": API_KEY}  # Paramètres envoyer avec la requête
    response = requests.get(url, params=params)

    if response.status_code == 200:
        sports = response.json()  # On convertit la réponse en liste Python
        print(f"Connexion réussie ! {len(sports)} sports disponibles.\n")
        
        for sport in sports[:5]:  # 5 premiers seulement pour pas surcharger le terminal
            print(f"- {sport['title']} ({sport['key']})")
    else:
        print(f"Une erreur est survenue : {response.status_code} : {response.text}")


get_sports()
