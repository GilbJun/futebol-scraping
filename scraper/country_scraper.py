import json
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from scraper.league_scraper import extract_leagues

def extract_countries(driver, jsons_path):
    try:
        driver.find_element(By.CSS_SELECTOR, ".lmc__itemMore").click()
        print("More leagues button clicked")
    except NoSuchElementException:
        print("More leagues button not found")
        driver.quit()

    try:
        countries_elements = driver.find_elements(By.CSS_SELECTOR, ".lmc__item")
    except NoSuchElementException:
        print("Country elements not found")
        driver.quit()

    countries = [el.text for el in countries_elements]

    with open(f"{jsons_path}/countries.json", "w") as f:
        json.dump(countries, f, indent=4)

    # Exemplo: extrair ligas do Brasil
    extract_leagues(driver, "Brazil", countries, countries_elements, jsons_path)