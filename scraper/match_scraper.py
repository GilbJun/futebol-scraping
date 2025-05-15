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
            matchesDetails[formattedMatchId]["round"] = match["round"]
        return matchesDetails

    def extract_match_details(self, matchId):
        from slugify import slugify

        urlMatch = URL_MATCH + matchId
        self.driver.get(urlMatch)
        teamsElements = self.driver.find_elements(By.CSS_SELECTOR, "a.participant__participantName")
        date = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__startTime").text
        scoreElement = find_if_exists_by_selector(".detailScore__wrapper span:not(.detailScore__divider)", self.driver)
        if scoreElement:
            homeScore = scoreElement[0].text
            awayScore = scoreElement[1].text
        else:
            homeScore = None
            awayScore = None
        homeTeamLink = teamsElements[0].get_attribute("href")
        awayTeamLink = teamsElements[1].get_attribute("href")
        matchDetails = {
            "date": date,
            "home_team_id": homeTeamLink.split("/")[-2],
            "home_team_name": self.get_match_home_name(),
            "home_team_icon": self.get_match_home_icon(),
            "away_team_id": awayTeamLink.split("/")[-2],
            "away_team_name": self.get_match_away_name(),
            "away_team_icon": self.get_match_away_icon(),
            "home_score": homeScore,
            "away_score": awayScore,
            "matchId": matchId
        }

        matchDetails["home_team_slug"] = slugify(matchDetails["home_team_name"])
        matchDetails["away_team_slug"] = slugify(matchDetails["away_team_name"])

        print("extracted match " + matchId)
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

