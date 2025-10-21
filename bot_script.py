import os
import requests
from bs4 import BeautifulSoup
import telegram

# --- CONFIGURATION ---
# Récupération sécurisée des secrets depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

BASE_URL = "https://www.sportcorico.com"
TEAM_PAGE_IDENTIFIER = "U18 2" # Le texte qui permet d'identifier le lien de l'équipe

# --- FONCTIONS ---

async def get_match_info():
    """
    Navigue sur le site pour trouver les informations du prochain match.
    Retourne un message formaté ou une erreur.
    """
    try:
        # Étape 1: Aller sur la page principale du club
        club_url = f"{BASE_URL}/clubs/bresse-tonic-foot"
        response = requests.get(club_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Étape 2: Trouver le lien de la page de l'équipe
        team_link_tag = soup.find("span", string=lambda text: TEAM_PAGE_IDENTIFIER in text if text else False)
        if not team_link_tag:
            return "Erreur : Impossible de trouver le lien de l'équipe sur la page du club."

        # remonter à la balise <a> parente
        team_page_url_suffix = team_link_tag.find_parent('a')['href']
        team_page_url = f"{BASE_URL}{team_page_url_suffix}"

        # Étape 3: Aller sur la page de l'équipe et trouver le lien du match
        response = requests.get(team_page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        next_match_link_tag = soup.find("h2", string="Prochain Match")
        if not next_match_link_tag:
            return "Aucun prochain match trouvé sur la page de l'équipe pour le moment."

        match_details_url_suffix = next_match_link_tag.find_parent('a')['href']
        match_details_url = f"{BASE_URL}{match_details_url_suffix}"

        # Sauvegarder les noms d'équipes depuis cette page
        parent_block = next_match_link_tag.find_parent(class_="card")
        teams = parent_block.find_all("span", class_="font-extrabold")
        team_home = teams[0].text.strip()
        team_away = teams[1].text.strip()

        # Étape 4: Aller sur la page de détails du match
        response = requests.get(match_details_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Étape 5: Extraire les informations finales
        info_block = soup.find("p", string=lambda text: "STADE" in text if text else False)
        if not info_block:
            return "Erreur: Impossible de trouver le bloc d'informations sur la page du match."

        stade = info_block.text.strip()
        date_time_p = info_block.find_next_sibling("div").find("p")
        date_time = date_time_p.text.strip()
        
        address_p = soup.find("p", string=lambda text: "ROUTE" in text if text else False)
        adresse = address_p.text.strip() if address_p else "Adresse non trouvée"

        # Formatage du message
        message = (
            f"🔔 *Rappel de Match à Venir*\n\n"
            f"⚽ {team_home} vs {team_away}\n\n"
            f"📅 *Date et Heure :* {date_time}\n"
            f"🏟️ *Lieu :* {stade}\n"
            f"📍 *Adresse :* {adresse}"
        )
        return message

    except requests.exceptions.RequestException as e:
        return f"Erreur de réseau : {e}"
    except Exception as e:
        return f"Une erreur inattendue est survenue : {e}"

async def send_telegram_message(message):
    """Envoie un message sur Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Erreur : Le token du bot ou l'ID de chat n'est pas défini.")
        return

    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        print("Message de notification envoyé avec succès sur Telegram !")
    except Exception as e:
        print(f"Une erreur est survenue lors de l'envoi du message Telegram : {e}")

async def main():
    """Fonction principale du script."""
    print("Lancement de la recherche d'informations sur le prochain match...")
    match_message = await get_match_info()
    await send_telegram_message(match_message)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
