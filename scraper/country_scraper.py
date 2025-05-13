import json
from config import JSONS_PATH
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from scraper.league_scraper import extract_leagues

def extract_countries(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, ".lmc__itemMore").click()
    except NoSuchElementException:
        driver.quit()

    try:
        countries_elements = driver.find_elements(By.CSS_SELECTOR, ".lmc__item")
    except NoSuchElementException:
        print("Country elements not found")
        driver.quit()

    countries = [el.text for el in countries_elements]

    with open(f"{JSONS_PATH}/countries.json", "w") as f:
        json.dump(countries, f, indent=4)

    return countries, countries_elements
    # Exemplo: extrair ligas do Brasil
    extract_leagues(driver, "Brazil", countries, countries_elements, jsons_path)