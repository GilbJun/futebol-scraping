import json
import threading
from config import JSONS_PATH
from slugify import slugify
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from utils import find_if_exists_by_selector
from scraper.match_scraper import MatchScraper

def extract_leagues(driver, countries, countries_elements):
    from scraper.firestore_manager import get_firestore_client
    db = get_firestore_client()
    countries_collection = db.collection("countries")

    leagues = {}
    leaguesTotal = 0
    for currentCountry in countries:

        print("Extracting leagues for:", currentCountry)
        index = countries.index(currentCountry)
        countries_elements[index].click()

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".lmc__blockOpened .lmc__template"))
            )
        except TimeoutException:
            print("Timed out waiting for leagues to load")

        elements = driver.find_elements(By.CSS_SELECTOR, ".lmc__blockOpened .lmc__template")
        currentLeagues = [el.text for el in elements]
        
        # Encerra a seção de ligas 
        countries_elements[index].click()

        leagues[currentCountry] = currentLeagues
        leaguesTotal += len(currentLeagues)
        print(f"Leagues for {currentCountry}: {len(currentLeagues)}")

        # Salva o país na coleção 'countries'
        countryId = slugify(currentCountry)
        country_doc = countries_collection.document(countryId)
        country_doc.set({"name": currentCountry})

        # Salva as ligas como subcoleção 'leagues' dentro do país
        leagues_collection = country_doc.collection("leagues")
        for league_name in currentLeagues:
            league_id = slugify(league_name)
            leagues_collection.document(league_id).set({"name": league_name})


    # Save the leagues to a JSON file
    # with open(f"{JSONS_PATH}/leagues.json", "w") as f:
    #     json.dump(leagues, f, indent=4)

    return leagues, leaguesTotal

def extract_league_matches(pool, country, league):
    from config import URL_LEAGUE_MATCHS
    from utils import chunk_dict
    from datetime import datetime
    from scraper.firestore_manager import get_firestore_client

    db = get_firestore_client()
    countryId = slugify(country)
    leagueId = slugify(league)
    country_doc = db.collection("countries").document(countryId)
    league_doc = country_doc.collection("leagues").document(leagueId)
    league_data = league_doc.get().to_dict()
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    end_date_str = league_data.get("endDate") if league_data else None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            today = datetime.strptime(today_date, "%Y-%m-%d").date()
            if end_date < today:
                print(f"Skipping update for league: {league} (League has finished)")
                return
        except Exception as e:
            print(f"Warning: Could not parse endDate '{end_date_str}' for league {league}: {e}")

    # if league_data and league_data.get("updated_at") == today_date:
    #     print(f"Skipping update for league: {league} (already updated today)")
        
        # return
    
    # Prepare URLs for results and fixtures
    leagueSlug = slugify(league)
    countrySlug = slugify(country)
    urlsToFind = [
        URL_LEAGUE_MATCHS + countrySlug + "/" + leagueSlug + "/results",
        URL_LEAGUE_MATCHS + countrySlug + "/" + leagueSlug + "/fixtures"
    ]

    # Worker function: each thread creates its own driver and scrapes its chunk
    def worker(matches_chunk, idx, urlsToFind, country, league):
        from scraper.driver_manager import get_driver
        from utils import find_if_exists_by_selector, safe_get
        from slugify import slugify
            
        local_driver = get_driver()
        matches = {}
        leagueSlug = slugify(league)
        countrySlug = slugify(country)
        for currentUrl in urlsToFind:

            safe_get(local_driver, currentUrl)
            leagueElement = find_if_exists_by_selector(".leagues--static.event--leagues", local_driver)
            if leagueElement != False and len(leagueElement) > 0:
                matchElements = leagueElement[0].find_elements(By.CSS_SELECTOR, ".event__match, .event__round")
            else:
                matchElements = []
            currentRound = ""
            for matchElement in matchElements:
                if "event__round" in matchElement.get_attribute("class").split(' '):
                    currentRound = matchElement.text
                    continue
                matchId = matchElement.get_attribute("id")
                matches[matchId] = {
                    "id": matchId,
                    "round": currentRound,
                }
        try:
            scraper = MatchScraper(local_driver)
            result = scraper.extract_matches_details(matches_chunk)
            return idx, result
        finally:
            local_driver.quit()

    # Get all matches (serially, with a temporary driver)
    from scraper.driver_manager import get_driver
    from utils import find_if_exists_by_selector, safe_get
    matches = {}
    temp_driver = get_driver()
    for currentUrl in urlsToFind:
        futureMatch = False
        if "fixtures" in currentUrl: futureMatch = True
        
        safe_get(temp_driver, currentUrl)
        leagueElement = find_if_exists_by_selector(".leagues--static.event--leagues", temp_driver)
        if leagueElement != False and len(leagueElement) > 0:
            matchElements = leagueElement[0].find_elements(By.CSS_SELECTOR, ".event__match, .event__round")
        else:
            matchElements = []
        currentRound = ""
        for matchElement in matchElements:
            if "event__round" in matchElement.get_attribute("class").split(' '):
                currentRound = matchElement.text
                continue
            matchId = matchElement.get_attribute("id")
            matches[matchId] = {
                "id": matchId,
                "round": currentRound,
                "country": country,
                "league": league,
                "future" : futureMatch
            }
    temp_driver.quit()

    # Split matches for threads
    num_threads = 2
    match_chunks = chunk_dict(matches, num_threads)

    # Submit tasks to the pool
    from concurrent.futures import as_completed
    futures = []
    for i in range(num_threads):
        futures.append(pool.submit(worker, match_chunks[i], i, urlsToFind, country, league))

    detaliedMatches = {}
    for future in as_completed(futures):
        idx, result = future.result()
        if result:
            detaliedMatches.update(result)

    # Find startDate and endDate
    startDate = None
    endDate = None
    date_format = "%d.%m.%Y %H:%M"
    for match_id, match_data in detaliedMatches.items():
        match_date_str = match_data.get("date")
        if match_date_str:
            try:
                match_date = datetime.strptime(match_date_str, date_format)
            except ValueError:
                # Try without time if needed
                date_format_simple = "%d.%m.%Y"
                match_date = datetime.strptime(match_date_str, date_format_simple)
            if startDate is None or match_date < startDate:
                startDate = match_date
            if endDate is None or match_date > endDate:
                endDate = match_date
        # Save each match as a document
        collection_ref = db.collection("countries").document(countryId).collection("leagues").document(leagueId).collection("matches")
        collection_ref.document(str(match_id)).set(match_data)

    print(len(detaliedMatches), " matches updated")
    if len(detaliedMatches):
        country_doc.update({"hasMatches": True})
        league_doc.update({
            "hasMatches": True,
            "updated_at": today_date,
            "startDate": startDate.strftime("%Y-%m-%d") if startDate else None,
            "endDate": endDate.strftime("%Y-%m-%d") if endDate else None
        })

    # After updating matches, also update next_matches collection with closest games from the week
    save_next_matches_week(db, league_doc, countryId, leagueId, detaliedMatches)

    return detaliedMatches

def save_next_matches_week(db, league_doc, countryId, leagueId, detaliedMatches):
    """
    Save matches from the next 7 days to both per-league and global collections.
    """
    from datetime import datetime, timedelta
    today = datetime.now()
    week_later = today + timedelta(days=7)
    next_matches = []
    for match_id, match_data in detaliedMatches.items():
        match_date_str = match_data.get("date")
        if not match_date_str:
            continue
        try:
            try:
                match_date = datetime.strptime(match_date_str, "%d.%m.%Y %H:%M")
            except ValueError:
                match_date = datetime.strptime(match_date_str, "%d.%m.%Y")
            if today <= match_date <= week_later:
                next_matches.append({"id": match_id, **match_data})
        except Exception as e:
            print(f"Could not parse date '{match_date_str}' for next_matches: {e}")
    # Save next_matches to a new collection (per-league)
    next_matches_ref = league_doc.collection("next_matches")
    global_next_matches_ref = db.collection("next_matches_global")
    # Only delete past matches from next_matches using Firestore query on dateTime
    # Per-league: delete only docs with dateTime < now
    for doc in next_matches_ref.where("dateTime", "<", today).stream():
        doc.reference.delete()
    # Global: delete only docs for this league/country with dateTime < now
    for doc in global_next_matches_ref.where("dateTime", "<", today).stream():
        if doc.id.startswith(f"{countryId}_{leagueId}_"):
            doc.reference.delete()
    # Save new next_matches (per-league)
    for match in next_matches:
        print("saving week match:", match["id"])
        next_matches_ref.document(str(match["id"])).set(match)
    # Save new next_matches (global)
    for match in next_matches:
        global_id = f"{countryId}_{leagueId}_{match['id']}"
        global_next_matches_ref.document(global_id).set(match)

def extract_league_tables(country, league, local_driver):
    from scraper.firestore_manager import get_firestore_client
    from config import URL_TABLE
    from utils import find_if_exists_by_selector, save_league_image

    
    db = get_firestore_client()
    countryId = slugify(country)
    leagueId = slugify(league)
    country_doc = db.collection("countries").document(countryId)
    league_doc = country_doc.collection("leagues").document(leagueId)
    league_data = league_doc.get().to_dict()

    url_table = URL_TABLE.replace("<country>", countryId).replace("<league>", leagueId)
    local_driver.get(url_table)
    
    # Getting table element
    table_element = find_if_exists_by_selector("#tournament-table-tabs-and-content", local_driver)
    if table_element == False or len(table_element) == 0:
        print("Not able to load table for league:", league, "Error or not exists")
        return False

    positionsElements = find_if_exists_by_selector(".ui-table__body .ui-table__row", local_driver)
    
    positions = []

    leagueYear      = find_if_exists_by_selector(".heading__info", local_driver)[0].text
    leagueImage     = find_if_exists_by_selector(".heading__logo", local_driver)[0].get_attribute("src")
    leagueYearSlug  = slugify(leagueYear)
    save_league_image(leagueImage, slugify(league))

    if positionsElements == False or len(positionsElements) == 0:
        print("probably league is not table, needs to implement a function to get elimination competitions")
        return False
    
    for positionElement in positionsElements:

        teamId = positionElement \
            .find_element(By.CSS_SELECTOR, ".tableCellParticipant__block a") \
            .get_attribute("href").split("/")[-2]
        
        position = {}
        position["rank"]            = getTableRank(positionElement)
        position["teamId"]          = teamId
        position["name"]            = getTableTeamName(positionElement)
        position["matches_played"]  = getTableMatchesPlayed(positionElement)
        position["wins"]            = getTableWins(positionElement)
        position["defeats"]         = getTableWins(positionElement)
        position["draws"]           = getTableDraws(positionElement)
        position["losses"]          = getTableWins(positionElement)
        position["goals"]           = getTableGoals(positionElement)
        position["goal_difference"] = getTableGoalDifference(positionElement)
        position["points"]          = getTablePoints(positionElement)
        position["last_games"]      = getTableLastGames(positionElement)

        positions.append(position)
        
        



    # Save to Firestore
    league_doc.collection("tables") \
        .document(leagueYearSlug).set({"positions": positions})

    

    return True

def getTableRank(positionElement):
    """
    Extracts the rank from a position element.
    """
    return positionElement.find_element(By.CSS_SELECTOR, ".tableCellRank").text

def getTableTeamName(positionElement):
    """
    Extracts the Team Name from a position element.
    """
    return positionElement.find_element(By.CSS_SELECTOR, ".tableCellParticipant__name").text
def getTableMatchesPlayed(positionElement):
    return getTableInfo(positionElement, "MP")
        
def getTableWins(positionElement):
    return getTableInfo(positionElement, "W")
def getTableDraws(positionElement):
    return getTableInfo(positionElement, "D")
def getTableLosses(positionElement):
    return getTableInfo(positionElement, "L")
def getTableGoals(positionElement):
    return getTableInfo(positionElement, "G")
def getTableGoalDifference(positionElement):
    return getTableInfo(positionElement, "GD")
def getTablePoints(positionElement):
    return getTableInfo(positionElement, "PTS")
def getTableLastGames(positionElement):
    return getTableInfo(positionElement, "FORM")

def getTableInfo(positionElement, info):
    infos = {
        "MP": 2,
        "W": 3,
        "D": 4,
        "L": 5,
        "G": 6,
        "GD": 7,
        "PTS": 8,
        "FORM": 9
    }

    indexSearch = infos[info]

    """
    Extracts the number of matches played from a position element.
    """
    table = positionElement.find_element(By.XPATH, "./ancestor::*[@class='ui-table'][1]")
    headers = table.find_elements(By.CSS_SELECTOR, ".ui-table__header .ui-table__headerCell")

    if headers[indexSearch].text == info: 
        return positionElement.find_elements(By.CSS_SELECTOR, ".table__cell")[indexSearch].text
    else:
        print("Warning: Could not find ",info," in expected position, using fallback")