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

    if league_data and league_data.get("updated_at") == today_date:
        print(f"Skipping update for league: {league} (already updated today)")
        
        return
    
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

    return detaliedMatches