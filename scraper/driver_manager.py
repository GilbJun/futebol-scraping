from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

def get_driver(debbug = False):
    
    options = Options()
    if debbug:
        options.add_experimental_option("detach", True)
    else:
        options.add_experimental_option("detach", False)  # Fecha o navegador após o término do script
        options.add_argument("--headless")  # Executa sem abrir janela
        options.add_argument("--disable-gpu")  # Recomendado no modo headless
        options.add_argument("--window-size=1920,1080")  # Define um tamanho de tela "normal"
        options.add_argument("--no-sandbox")  # Útil em alguns sistemas
        options.add_argument("--disable-dev-shm-usage")  # Evita erros em containers Linux
        
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)
    driver.get("http://www.flashscore.com")

    # Fecha o banner de cookies
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except NoSuchElementException:
        print("Cookie banner not found")

    return driver