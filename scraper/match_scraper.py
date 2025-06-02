import json
from config import URL_MATCH
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from utils import find_if_exists_by_selector, insertFutureMatch, getMatchDb
from datetime import datetime

class MatchScraper:
    def __init__(self, driver):
        self.driver = driver

    def extract_matches_details(self, matches):
        """
        Extracts details for each match in the provided dictionary.
        Skips matches that are already ended in the database.
        Inserts future matches into the future_matches collection.
        Returns a dictionary of match details.
        """
        details = {}
        for matchId, match in matches.items():
            formattedMatchId = matchId.split("_")[-1]
            match = match.copy()  # avoid mutating input
            match["id"] = formattedMatchId

            if match.get("future"):
                insertFutureMatch(match)
            else:
                dbMatch = getMatchDb(match)
                if dbMatch.get("ended") is True:
                    print(f"Skipping ended match {formattedMatchId}")
                    continue

            match_details = self._extract_with_retries(formattedMatchId, match)
            if match_details is None:
                print(f"{formattedMatchId} Removed because is empty or failed after 3 attempts")
                continue
            match_details["round"] = match.get("round")
            details[formattedMatchId] = match_details
        return details

    def _extract_with_retries(self, matchId, match, max_attempts=3):
        """
        Tries to extract match details up to max_attempts times.
        """
        for attempt in range(max_attempts):
            try:
                return self.extract_match_details(matchId)
            except Exception as e:
                print(f"Error extracting match {matchId} (attempt {attempt+1}/{max_attempts}): {e}")
        return None

    def extract_match_details(self, matchId):
        """
        Extracts all details for a single match by its ID.
        Returns a dictionary with match details or None if not found.
        """
        from slugify import slugify
        from utils import save_team_image, safe_get
        print(f"extracting {matchId}")

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
            return None

        homeTeamLink = teamsElements[0].get_attribute("href")
        awayTeamLink = teamsElements[1].get_attribute("href")
        home_team_name = self.get_match_home_name()
        away_team_name = self.get_match_away_name()
        home_team_icon_url = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home img.participant__image").get_attribute("src")
        away_team_icon_url = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away img.participant__image").get_attribute("src")
        home_team_id = homeTeamLink.split("/")[-2]
        away_team_id = awayTeamLink.split("/")[-2]
        home_team_icon_name = home_team_id + "-" + slugify(home_team_name)
        away_team_icon_name = away_team_id + "-" + slugify(away_team_name)

        save_team_image(home_team_icon_url, home_team_icon_name)
        save_team_image(away_team_icon_url, away_team_icon_name)
        dateTime = datetime.strptime(date, "%d.%m.%Y %H:%M")

        matchDetails = {
            "date": date,
            "dateTime": dateTime,
            "home_team_id": home_team_id,
            "home_team_name": home_team_name,
            "home_team_icon": home_team_icon_name,
            "away_team_id": away_team_id,
            "away_team_name": away_team_name,
            "away_team_icon": away_team_icon_name,
            "home_score": homeScore,
            "away_score": awayScore,
            "ended": self._is_match_ended(date),
            "matchId": matchId
        }
        matchDetails["home_team_slug"] = slugify(matchDetails["home_team_name"])
        matchDetails["away_team_slug"] = slugify(matchDetails["away_team_name"])
        print(f"done {matchId}")
        return matchDetails

    def get_match_home_name(self):
        """Returns the home team name from the match page."""
        return self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home a.participant__participantName").text

    def get_match_away_name(self):
        """Returns the away team name from the match page."""
        return self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away a.participant__participantName").text

    def get_match_home_icon(self):
        from utils import image_link_to_base64String
        image = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home img.participant__image").get_attribute("src")
        return image_link_to_base64String(image)

    def get_match_away_icon(self):
        from utils import image_link_to_base64String
        image = self.driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away img.participant__image").get_attribute("src")
        return image_link_to_base64String(image)

    def _is_match_ended(self, date_str):
        """
        Returns True if the match date is in the past, otherwise False.
        """
        from datetime import datetime
        try:
            try:
                match_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            except ValueError:
                match_date = datetime.strptime(date_str, "%d.%m.%Y")
            return match_date < datetime.now()
        except Exception as e:
            print(f"Could not parse date '{date_str}' for ended check: {e}")
            return False