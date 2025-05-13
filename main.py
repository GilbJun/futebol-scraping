import json
from scraper.driver_manager import get_driver
from scraper.country_scraper import extract_countries
from scraper.league_scraper import extract_leagues
from scraper.team_scraper import extract_teams

def main():
    driver = get_driver(True)
    # countries, countriesElements    = extract_countries(driver)
    # leagues, totalLeagues           = extract_leagues(driver, countries, countriesElements)
    # print(f"Total leagues: {totalLeagues}")
    # print("Total countries:", len(countries))
    
    teams = extract_teams(driver, "Brazil")

    
    
    

        

    driver.quit()

if __name__ == "__main__":
    main()