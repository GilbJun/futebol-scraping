import json
from config import JSONS_PATH
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

def extract_leagues(driver, countries, countries_elements):

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


    # Save the leagues to a JSON file
    with open(f"{JSONS_PATH}/leagues.json", "w") as f:
        json.dump(leagues, f, indent=4)

    return leagues, leaguesTotal
