import json
import threading
from config import JSONS_PATH
from slugify import slugify
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

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

def extract_league_matches(driver, country, league):
    from config import URL_LEAGUE_MATCHS
    from scraper.driver_manager import get_driver 
    from utils import chunk_dict

    def worker(matches_chunk, results, idx):
        local_driver = get_driver()  # Cria um novo driver para a thread
        try:
            scraper = MatchScraper(local_driver)
            results[idx] = scraper.extract_matches_details(matches_chunk)
        finally:
            local_driver.quit()

    # Preparing vars
    matches = {}
    leagueSlug = slugify(league)
    countrySlug = slugify(country)
    urlsToFind = [
        URL_LEAGUE_MATCHS + countrySlug + "/" + leagueSlug + "/results",
        URL_LEAGUE_MATCHS + countrySlug + "/" + leagueSlug + "/fixtures"
    ]

    # Get Match List for to consult details
    for currentUrl in urlsToFind:
        driver.get(currentUrl)
        leagueElement = driver.find_element(By.CSS_SELECTOR, ".leagues--static.event--leagues")
        matchElements = leagueElement.find_elements(By.CSS_SELECTOR, ".event__match, .event__round")
        currentRound = ""
        for matchElement in matchElements:
            if "event__round" in matchElement.get_attribute("class").split(' '):
                currentRound = matchElement.text
                continue
            matchId = matchElement.get_attribute("id")
            matches[matchId] = {
                "id": matchId,
                "round": currentRound
            }

    # Running threads to find details in paralalel
    num_threads = 4
    match_chunks = chunk_dict(matches, num_threads)
    threads = []
    results = [None] * num_threads
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(match_chunks[i], results, i))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    detaliedMatches = {}

    # Including result by result from the threads to our dictionary
    for r in results:
        if r:
            detaliedMatches.update(r)

    # # Save the leagues to a JSON file
    # with open(f"{JSONS_PATH}/matches.json", "w") as f:
    #     json.dump(detaliedMatches, f, indent=4)


    # Salva no Firestore ao invés de JSON
    from scraper.firestore_manager import get_firestore_client
    db = get_firestore_client()
    countryId   = slugify(country)
    leagueId    = slugify(league)

    collection_ref = db.collection("countries").document(countryId).collection("leagues").document(leagueId).collection("matches")
    for match_id, match_data in detaliedMatches.items():
        # Salva cada match como um documento, usando o match_id como ID
        collection_ref.document(str(match_id)).set(match_data)

    return detaliedMatches