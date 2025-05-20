from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import shutil
import os

def ensure_chromedriver():
    if shutil.which("chromedriver") is None:
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            os.environ["PATH"] += os.pathsep + os.path.dirname(driver_path)
        except ImportError:
            print("webdriver-manager not installed. Please install it or ensure chromedriver is in PATH.")
            raise

def get_driver(debbug = False):
    ensure_chromedriver()
    options = Options()
    if debbug:
        options.add_experimental_option("detach", True)
    else:
        options.add_experimental_option("detach", False)
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)
    driver.get("http://www.flashscore.com")

    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except NoSuchElementException:
        print("Cookie banner not found")

    return driver