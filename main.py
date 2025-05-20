import json
from scraper.driver_manager import get_driver
from scraper.country_scraper import extract_countries
from scraper.league_scraper import extract_leagues, extract_league_matches
from scraper.team_scraper import extract_teams
from scraper.match_scraper import MatchScraper
from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    # driver = get_driver(True)
    # Exemplo de uso:
    # countries, countriesElements = extract_countries(driver)
    # leagues, totalLeagues = extract_leagues(driver, countries, countriesElements)
    # print(f"Total leagues: {totalLeagues}")
    # print("Total countries:", len(countries))
    # teams = extract_teams(driver, "Brazil")

    # Para extrair detalhes dos jogos de uma liga específica:
    # matches_dict = extract_league_matches(driver, "Brazil", "Serie A Betano")

    from scraper.firestore_manager import get_firestore_client

    db = get_firestore_client()
    countries_collection = db.collection("countries")
    countries = ['brazil','spain','germany','argentina','italia','equador']
    with ThreadPoolExecutor(max_workers=2) as pool:
    
    # league_executions = 0
        for country in countries:
            country_id = country
            country_name = country

            # if league_executions >= 1:
            #     print("interrompe looping paises, 1 ligas processadas")
            #     break
            
            print(f"Processing country: {country_name}")

            leagues_collection = countries_collection.document(country_id).collection("leagues")
            leagues = leagues_collection.get()
            league_count = 0

            for league_doc in leagues:
                league_id = league_doc.id
                league_name = league_doc.to_dict().get("name")
                print(f"  Processing league: {league_name}")

                # Call extract_league_matches for each league
                extract_league_matches(pool, country_name, league_name)
                # if leagues != None: league_executions += 1

if __name__ == "__main__":
    main()