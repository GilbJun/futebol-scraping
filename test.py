import json
import datetime
from pathlib import Path
import os


from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

def extract_leagues(country):
    
    indexCountrie = countries.index(country)
    print(countriesElements[indexCountrie].text)
  

# Dev options
options = Options()
options.add_experimental_option("detach", False)

# prepare the Chrome driver
driver = webdriver.Chrome(options=options)
driver.get("http://www.flashscore.com")
wait = WebDriverWait(driver, 20)

# Closing the cookie banner
try:
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
except NoSuchElementException:  
    print("Cookie banner not found")
    pass

# Creating a path to save the contents
date = datetime.date.today()
date = date.strftime("%Y-%m-%d")
jsonsPath = "files/" + date
import os
if not os.path.exists(jsonsPath):
    os.makedirs(jsonsPath)

try: 
    buttonMoreLeagues = driver.find_element(By.CSS_SELECTOR, ".lmc__itemMore")
    buttonMoreLeagues.click()

except NoSuchElementException:
    print("More leagues button not found")
    driver.close()
print("More leagues button clicked")

try:
    countriesElements = driver.find_elements(By.CSS_SELECTOR, ".lmc__item")
except NoSuchElementException:
    print("Element not found")
    driver.close()

countries = [league.text for league in countriesElements]
# print(countries)

with open(jsonsPath + "/leagues.json", "w") as file:
    json.dump(countries, file, indent=4)

extract_leagues('Brazil')


driver.close()