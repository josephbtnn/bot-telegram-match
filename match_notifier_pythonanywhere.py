# -*- coding: utf-8 -*-

import os
import requests
import telegram
import asyncio
from bs4 import BeautifulSoup

# URL de base du site et page de départ du club
BASE_URL = "https://www.sportcorico.com"
CLUB_URL = f"{BASE_URL}/clubs/bresse-tonic-foot"

def get_next_match_info():
    """
    Navigue sur le site pour trouver les informations complètes du prochain match.
    """
    try:
        # --- ÉTAPE 1: Trouver la page de l'équipe ---
        print("Étape 1: Recherche de la page de l'équipe 'U18 2'...")
        response_club = requests.get(CLUB_URL)
        response_club.raise_for_status()
        soup_club = BeautifulSoup(response_club.content, 'html.parser')

        team_span = soup_club.find('span', string=lambda t: t and 'U18 2' in t.strip())
        if not team_span:
            return "Impossible de trouver l'équipe 'U18 2' sur la page du club."
        
        team_link_tag = team_span.find_parent('a')
        if not team_link_tag or not team_link_tag.has_attr('href'):
            return "Lien vers la page de l'équipe introuvable."
            
        team_page_url = BASE_URL + team_link_tag['href']
        print(f"Page de l'équipe trouvée : {team_page_url}")

        # --- ÉTAPE 2: Trouver le lien du match ET récupérer les noms des équipes ---
        print("Étape 2: Recherche du prochain match et des noms d'équipes...")
        response_team = requests.get(team_page_url)
        response_team.raise_for_status()
        soup_team = BeautifulSoup(response_team.content, 'html.parser')

        prochain_match_header = soup_team.find('h2', string=lambda t: t and 'Prochain Match' in t)
        if not prochain_match_header:
            return "Bloc 'Prochain Match' introuvable sur la page de l'équipe."
            
        match_link_tag = prochain_match_header.find_parent('a')
        if not match_link_tag or not match_link_tag.has_attr('href'):
            return "Lien vers la page du match introuvable."

        teams_on_preview = match_link_tag.find_all('span', class_='font-extrabold')
        if len(teams_on_preview) < 2:
            return "Noms des équipes introuvables sur la page de l'équipe."
        equipe_gauche = teams_on_preview[0].text.strip()
        equipe_droite = teams_on_preview[1].text.strip()
        print(f"Équipes trouvées : {equipe_gauche} vs {equipe_droite}")

        match_details_url = BASE_URL + match_link_tag['href']
        print(f"Page de détails du match trouvée : {match_details_url}")

        # --- ÉTAPE 3: Scraper les informations finales (lieu, date, heure) ---
        print("Étape 3: Extraction des informations finales...")
        response_match = requests.get(match_details_url)
        response_match.raise_for_status()
        soup_match = BeautifulSoup(response_match.content, 'html.parser')

        info_block = soup_match.find('div', class_='border-primary')
        if not info_block:
            return "Bloc d'informations détaillé introuvable sur la page du match."

        stade = info_block.find('p', class_='font-bold').text.strip()
        date_heure_p = info_block.find('img', alt='horloge').find_next_sibling('p')
        date_heure = date_heure_p.text.strip().split(' - ')
        date_match = date_heure[0]
        heure_match = date_heure[1] if len(date_heure) > 1 else "Heure non spécifiée"
        
        adresse_p = info_block.find('p', string=lambda t: t and 'ROUTE DE' in t)
        adresse = adresse_p.text.strip() if adresse_p else "Adresse non trouvée"

        # On assemble le message final
        message = (
            f"📅 *Prochain Match : {equipe_gauche} vs {equipe_droite}* ⚽\n\n"
            f"▪️ *Date* : {date_match}\n"
            f"▪️ *Heure* : {heure_match}\n"
            f"▪️ *Stade* : {stade}\n"
            f"▪️ *Adresse* : {adresse}"
        )
        return message

    except requests.RequestException as e:
        return f"Erreur de réseau ou de page : {e}"
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")
        return "Une erreur est survenue lors du processus de scraping."

async def send_telegram_message(message):
    """Envoie un message formaté sur Telegram."""
    try:
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("Erreur : Le token ou le chat ID ne sont pas définis dans les secrets GitHub.")
            return
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')
        print("Message de notification envoyé avec succès sur Telegram !")
    except Exception as e:
        print(f"Une erreur est survenue lors de l'envoi du message Telegram : {e}")

# --- Section principale du script ---
if __name__ == "__main__":
    print("Démarrage de la tâche GitHub Action...")
    asyncio.run(send_telegram_message("🤖 Le bot se réveille pour sa vérification hebdomadaire..."))
    match_info = get_next_match_info()
    if match_info:
        asyncio.run(send_telegram_message(match_info))
    print("Fin de la tâche.")
