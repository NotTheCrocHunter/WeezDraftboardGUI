import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path
from datetime import datetime
import pandas as pd


def scrape_fantasy_pros_rankings():

    save_path = Path('data/fpros')
    save_path.mkdir(parents=True, exist_ok=True)
    TODAY = datetime.today().strftime('%Y-%m-%d')
    data_file = Path('data/fpros/fpros_data.json')

    try:
        with open(data_file, "r") as file:
            fpros_dict = json.load(file)
            fpros_saved_date = fpros_dict["last_saved"]
    except FileNotFoundError:
        fpros_saved_date = None

    if fpros_saved_date == TODAY:
        df = pd.DataFrame(fpros_dict["players"])
        return df
    else:
        print("Updating data from Fantasy Pros.")
        pages = ["rankings", "projections"]
        positions = ["QB", "RB", "WR", "TE", "SuperFlex"]
        "https://www.fantasypros.com/nfl/projections/rb.php?week=draft&scoring=PPR&week=draft"
    page = "rankings"
    week = "draft"
    s = "ppr"
    pos = "superflex"
    proj_url = "https://www.fantasypros.com/nfl/projections/rb.php?week=draft&scoring=PPR"
    base_url = f"https://www.fantasypros.com/nfl/{page}/{s}-{pos}-cheatsheets.php"
    u = "https://www.fantasypros.com/nfl/rankings/ppr-superflex-cheatsheets.php"
    results = requests.get(base_url).content

    soup = BeautifulSoup(results, "html.parser")

    pattern = re.compile(r"(?<=var ecrData = )[^;]+", re.MULTILINE)
    script = soup.find("script", {"type": "text/javascript"}, text=pattern)
    data = pattern.search(script.text).group(0)
    # make dict of json data
    data = json.loads(data)
    # player list here
    print(data['players'])
    # last accessed here
    # check for previously accessed when running this script
    print(data['accessed'])
    pass

scrape_fantasy_pros_rankings()

def scrape_fantasy_pros_projections(pos):
    page = "projections"
    week = "draft"
    s = "PPR"

    base_url = f"https://www.fantasypros.com/nfl/{page}/{s}-{pos}-cheatsheets.php"
    url2 = "https://www.fantasypros.com/nfl/rankings/ppr-wr-cheatsheets.php"
    u3 = "https://www.fantasypros.com/nfl/projections/rb.php?week=draft&scoring=PPR&week=draft"
    u4 -= "https://www.fantasypros.com/nfl/projections/qb.php?week=draft&scoring=PPR"

    pass