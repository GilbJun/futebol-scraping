# Fufutebol Scraping Project

## Overview
The Fufutebol Scraping Project is a Python-based web scraping application designed to extract football-related data, including countries, leagues, matches, and teams. The data is stored in Google Firestore for further analysis and use. Additionally, team images are downloaded and saved locally to enhance the dataset.

## Features
- **Country and League Extraction**: Extracts countries and their respective leagues and saves them in Firestore.
- **Match Data Extraction**: Retrieves match details and stores them in Firestore under the appropriate country and league hierarchy.
- **Team Image Handling**: Downloads and saves team images locally if they do not already exist.
- **Multithreaded Scraping**: Utilizes threading to speed up the scraping process for match details.

## Project Structure
```
config.py
main.py
utils.py
scraper/
    country_scraper.py
    driver_manager.py
    firestore_manager.py
    league_scraper.py
    match_scraper.py
    team_scraper.py
files/
    images/teams/
```

## Setup

### Prerequisites
- Python 3.10 or higher
- Google Firestore credentials (place the `key.json` file in the `database/` directory)
- Selenium WebDriver (e.g., ChromeDriver)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd fufutebol-scraping
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up Firestore credentials:
   - Place your Firestore `key.json` file in the `database/` directory.

4. Ensure you have the correct WebDriver version for your browser in the `driver/` directory.

## Usage

### Extract Countries and Leagues
Run the following command to extract countries and leagues:
```bash
python main.py extract_leagues
```

### Extract Matches
Run the following command to extract matches for a specific country and league:
```bash
python main.py extract_matches --country "<country_name>" --league "<league_name>"
```

### Save Team Images
Ensure team images are saved locally by running:
```bash
python main.py save_team_images
```

## Firestore Structure
The data is stored in Firestore with the following hierarchy:
```
countries/{countryId}
    leagues/{leagueId}
        matches/{matchId}
```

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- [Selenium](https://www.selenium.dev/)
- [Google Firestore](https://firebase.google.com/products/firestore)
- [Python Slugify](https://github.com/un33k/python-slugify)
