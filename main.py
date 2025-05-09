from config import JSONS_PATH
from scraper.driver_manager import get_driver
from scraper.country_scraper import extract_countries

def main():
    driver = get_driver()
    extract_countries(driver, JSONS_PATH)
    driver.quit()

if __name__ == "__main__":
    main()