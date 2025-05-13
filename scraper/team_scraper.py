import json
from config import JSONS_PATH, URL_COUNTRY_TEAMS, URL_TEAM
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

# def open_diferent_window(driver, url):
#     # Abre uma nova aba
#     driver.execute_script("window.open('');")
#     # Muda para a nova aba
#     driver.switch_to.window(driver.window_handles[1])
#     # Abre a URL na nova aba
#     print("Opening URL in new window:", url)
#     driver.get(url)
#     return 

# def return_old_window(driver):
#     driver.close() 
#     driver.switch_to.window(driver.window_handles[0]) 

def extract_teams(driver, country):

    
    print("Extracting teams for:", country)

    driver.get(URL_COUNTRY_TEAMS + "/" + country.lower())

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".event__match"))
        )
    except TimeoutException:
        print("Timed out waiting for teams to load")
    
    matchs = driver.find_elements(By.CSS_SELECTOR, ".event__match")
    uniqueTeamNames = []

    # Remove matches that contain teams that are already in the list
    print("Total matches:", len(matchs))
    for currentMatch in matchs:
        testNameTeamsElements = currentMatch.find_elements(By.CSS_SELECTOR, "[data-testid=wcl-matchRow-participant]")
        countainsTeam1 = testNameTeamsElements[0].text not in uniqueTeamNames
        countainsTeam2 = testNameTeamsElements[1].text not in uniqueTeamNames
        removeMatch = True
        if not countainsTeam1:
            uniqueTeamNames.append(testNameTeamsElements[0].text)
            removeMatch = False
        if not countainsTeam2:
            removeMatch = False
            uniqueTeamNames.append(testNameTeamsElements[1].text)
        if removeMatch:
            matchs.remove(currentMatch)

    print("Total matches after removing duplicates:", len(matchs))


    matchLinks = [match.find_element(By.CSS_SELECTOR, "a").get_attribute('href') for match in matchs]

    teams = {}
    
    # mounting the teams:
    for matchLink in matchLinks:
        driver.get(matchLink)
        matchElement = driver.find_element(By.CSS_SELECTOR, ".duelParticipant")
        matchTeams = matchElement.find_elements(By.CSS_SELECTOR,'.duelParticipant__home,.duelParticipant__away')
        for currentMatchTeam in matchTeams:
            
            # avoiding duplicates
            link = currentMatchTeam.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
            tempId = link.replace(URL_TEAM, "").split("/")[1]
            if tempId in teams:
                continue

            
            tempTeam = {
                "name" : currentMatchTeam.find_element(By.CSS_SELECTOR, ".participant__participantName").text,
                "icon" : currentMatchTeam.find_element(By.CSS_SELECTOR, ".participant__image").get_attribute('src'),
            }
            
            tempTeam["tag"] = link.replace(URL_TEAM, "").split("/")[0]

            # add team to the dictionary
            teams[tempId] = tempTeam
            
    with open(f"{JSONS_PATH}/teams.json", "w") as f:
        json.dump(teams, f, indent=4)

    return
