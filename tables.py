import argparse
from scraper.league_scraper import extract_league_tables
from scraper.driver_manager import get_driver

def main():
    print("Getting league tables...")

    parser = argparse.ArgumentParser(description="Run the scraper for a specific country or all countries.")
    parser.add_argument('--country', type=str, help='Country to process (slug, e.g. brazil). If not set, process all.')
    args = parser.parse_args()

    from scraper.firestore_manager import get_firestore_client


    driver = get_driver()

    db = get_firestore_client()
    countries_collection = db.collection("countries")
    all_countries = ['brazil', 'spain','germany', 'france', 'italy','argentina','england', 'portugal', 'netherlands']
    countries = [args.country] if args.country else all_countries

    for country in countries:
        country_id = country
        country_name = country
        
        print(f"Processing country: {country_name}")

        leagues_collection = countries_collection.document(country_id).collection("leagues")
        leagues = leagues_collection.get()
        league_count = 0

        for league_doc in leagues:
            league_id = league_doc.id
            league_name = league_doc.to_dict().get("name")
            print(f"  Processing league: {league_name}")

            extract_league_tables(country_name, league_name, driver)
            
    driver.quit()
        
if __name__ == "__main__":
    main()