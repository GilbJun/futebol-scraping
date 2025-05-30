import datetime
import os

# Data de hoje como string
DATE = datetime.date.today().strftime("%Y-%m-%d")

# Caminho para salvar os JSONs
JSONS_PATH = f"files/{DATE}"
os.makedirs(JSONS_PATH, exist_ok=True)
URL_COUNTRY_TEAMS   = "https://www.flashscore.com/football/"
URL_TEAM            = "https://www.flashscore.com/team/"
URL_LEAGUE_MATCHS   = "https://www.flashscore.com/football/"
URL_MATCH           = "https://www.flashscore.com/match/football/"
URL_TABLE           = "https://www.flashscore.com/football/<country>/<league>/standings"