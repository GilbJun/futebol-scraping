import json
from config import URL_MATCH
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from utils import find_if_exists_by_selector

class MatchScraper:
    def __init__(self, driver):
        self.driver = driver

    def extract_matches_details(self, matches):
        matchesDetails = {}
        for matchId, match in matches.items():
            formattedMatchId = matchId.split("_")[-1]
            matchesDetails[formattedMatchId] = self.extract_match_details(formattedMatchId)
            if(matchesDetails[formattedMatchId] == None):
                print(formattedMatchId + " Removed because is empty")
                del matchesDetails[formattedMatchId]
            else: matchesDetails[formattedMatchId]["round"] = match["round"]
        return matchesDetails

    def extract_match_details(self, matchId):
        from slugify import slugify
        from utils import save_team_image, safe_get
        print("extracting " + matchId)

        urlMatch = URL_MATCH + matchId
        safe_get(self.driver, urlMatch)
        teamsElements = find_if_exists_by_selector("a.participant__participantName", self.driver)
        date = find_if_exists_by_selector(".duelParticipant__startTime", self.driver)[0].text
        scoreElement = find_if_exists_by_selector(".detailScore__wrapper span:not(.detailScore__divider)", self.driver)
        if scoreElement:
            homeScore = scoreElement[0].text
            awayScore = scoreElement[1].text
        else:
            homeScore = None
            awayScore = None

        if not teamsElements or len(teamsElements) < 2:
            print(f"Warning: Could not find both team elements for match {matchId}")
            return None  # or return an empty dict, or handle as you prefer

        homeTeamLink = teamsElements[0].get_attribute("href")
        awayTeamLink = teamsElements[1].get_attribute("href")
        home_team_name = self.get_match_home_name()
        away_team_name = self.get_match_away_name()
        home_team_icon_url = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home img.participant__image").get_attribute("src")
        away_team_icon_url = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away img.participant__image").get_attribute("src")
        home_team_id = homeTeamLink.split("/")[-2]
        away_team_id = awayTeamLink.split("/")[-2]
        home_team_icon_name = home_team_id + "-"+ slugify(home_team_name)
        away_team_icon_name = away_team_id + "-"+ slugify(away_team_name)

        save_team_image(home_team_icon_url, home_team_icon_name)
        save_team_image(away_team_icon_url, away_team_icon_name)
            


        matchDetails = {
            "date": date,
            "home_team_id": home_team_id,
            "home_team_name": home_team_name,
            "home_team_icon": home_team_icon_name,
            "away_team_id": away_team_id,
            "away_team_name": away_team_name,
            "away_team_icon": away_team_icon_name,
            "home_score": homeScore,
            "away_score": awayScore,
            "matchId": matchId
        }

        matchDetails["home_team_slug"] = slugify(matchDetails["home_team_name"])
        matchDetails["away_team_slug"] = slugify(matchDetails["away_team_name"])

        print("done " + matchId)
        return matchDetails

    def get_match_home_name(self):
        name = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home a.participant__participantName").text
        return name

    def get_match_away_name(self):
        name = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away a.participant__participantName").text
        return name

    def get_match_home_icon(self):
        from utils import image_link_to_base64String
        image = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home img.participant__image").get_attribute("src")
        imageStringBase64 = image_link_to_base64String(image)
        return imageStringBase64

    def get_match_away_icon(self):
        from utils import image_link_to_base64String
        image = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away img.participant__image").get_attribute("src")
        imageStringBase64 = image_link_to_base64String(image)
        return imageStringBase64

