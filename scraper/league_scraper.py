import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

def extract_leagues(driver, country, countries, countries_elements, jsons_path):
    print("Extracting leagues for:", country)
    index = countries.index(country)
    countries_elements[index].click()

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".lmc__blockOpened .lmc__template"))
        )
    except TimeoutException:
        print("Timed out waiting for leagues to load")

    elements = driver.find_elements(By.CSS_SELECTOR, ".lmc__blockOpened .lmc__template")
    leagues = [el.text for el in elements]

    with open(f"{jsons_path}/leagues.json", "w") as f:
        json.dump({country.lower(): leagues}, f, indent=4)