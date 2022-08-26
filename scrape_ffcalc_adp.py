from sleeper_wrapper import Players
import re
import pandas as pd
import json
from datetime import datetime
import requests
from pathlib import Path
import time
import pdb
from sleeper_ids import get_sleeper_ids

YEAR = datetime.today().strftime('%Y')
TODAY = datetime.today().strftime('%Y-%m-%d')


def get_adp_df(adp_type="2qb", adp_year=YEAR, teams_count=12, positions="all"):
    start_time = time.time()
    adp_type = adp_type.lower()
    if adp_type == "non-ppr":
        adp_type = "standard"
    standard_url = "https://fantasyfootballcalculator.com/api/v1/adp/standard?teams=12&year=2022&position=all"
    base_url = f"https://fantasyfootballcalculator.com/api/v1/adp/" \
               f"{adp_type}?teams={teams_count}&{adp_year}&position={positions}"
    file_path = Path(f'data/adp/adp_{adp_type}.json')
    try:
        with open(file_path, "r") as data_file:
            adp_data = json.load(data_file)
            adp_end_date = adp_data["meta"]["end_date"]
    except FileNotFoundError:
        adp_end_date = None
        pass

    if adp_end_date == TODAY:
        print(f"Loading local ADP data from {adp_end_date}")
    else:
        print(f"Local ADP data does not match today's date, {TODAY}. Making call to FFCalc.")
        try:
            response = requests.get(base_url)
            adp_data = response.json()
        except requests.exceptions.RequestException as e:
            if adp_end_date:
                print(f"Error {e} when making the remote call.  Using local data from {adp_end_date}")
                pass
            else:
                print("Error reading local copy and error reading remote copy.  Must break. ")
                pass
        finally:
            adp_dir = Path('data/adp')
            adp_dir.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as data_file:
                json.dump(adp_data, data_file, indent=4)

    with open(file_path, 'r') as file:
        adp_data = json.load(file)

    adp_dict = adp_data["players"]
    print(f"Length of adp_dict: {len(adp_dict)}")
    adp_df = pd.DataFrame(adp_dict)
    print(f"Length of adp_df: {len(adp_df)}")
    adp_df.rename(columns={"player_id": "ffcalc_id"}, inplace=True)
    adp_df["adp_pick"] = adp_df.index + 1
    adp_df = get_sleeper_ids(adp_df)
    print(f"Length of adp_df AFTER get sleeper_id: {len(adp_df)}")
    end_time = time.time()
    print(f"Time to get ADP DF: {end_time - start_time}")

    return adp_df


df = get_adp_df(adp_type='half-ppr')

# print(df[df['sleeper_id'].isnull()])


