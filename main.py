import json
from scraper.driver_manager import get_driver
from scraper.country_scraper import extract_countries
from scraper.league_scraper import extract_leagues, extract_league_matches
from scraper.team_scraper import extract_teams
from scraper.match_scraper import MatchScraper

def main():
    driver = get_driver(True)
    # Exemplo de uso:
    # countries, countriesElements = extract_countries(driver)
    # leagues, totalLeagues = extract_leagues(driver, countries, countriesElements)
    # print(f"Total leagues: {totalLeagues}")
    # print("Total countries:", len(countries))
    # teams = extract_teams(driver, "Brazil")

    # Para extrair detalhes dos jogos de uma liga específica:
    matches_dict = extract_league_matches(driver, "Brazil", "Serie A Betano")
    

    driver.quit()

if __name__ == "__main__":
    main()