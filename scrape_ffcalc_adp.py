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

"""
def get_sleeper_ids(df):
    # ----- Create the search_names (all lowercase, no spaces) ------ #
    players = Players()
    search_names = []
    remove = ['jr', 'ii', 'sr']
    for idx, row in df.iterrows():
        if "team" in row.keys():
            if ["team"] == "JAC":
                df.loc[idx, "team"] = "JAX"
            if row['name'] == "Kyle Rudolph":
                row["team"] = "TB"
            if row["team"] == "FA":
                df.loc[idx, "team"] = None
        new_name = re.sub(r'\W+', '', row['name']).lower()
        if new_name[-3:] == "iii":
            new_name = new_name[:-3]
        elif new_name[-2:] in remove:
            new_name = new_name[:-2]

        if new_name == "kennethwalker":
            new_name = "kenwalker"
        if new_name == "isaihpacheco":
            new_name = "isiahpacheco"
        if new_name == "mitchelltrubisky":
            new_name = "mitchtrubisky"

        if new_name == "williamfullerv":
            new_name = "williamfuller"

        if new_name == "gabrieldavis":
            new_name = "gabedavis"
        search_names.append(new_name)

    df['search_full_name'] = search_names
    players_df = players.get_players_df()
    if "team" in df.columns:
        search_name_tuples = list(zip(df.search_full_name, df.team))
        players_match_df = players_df[
            players_df[['search_full_name', 'team']].apply(tuple, axis=1).isin(search_name_tuples)]
    else:
        search_name_tuples = list(zip(df.search_full_name, df.position))
        players_match_df = players_df[
            players_df[['search_full_name', 'position']].apply(tuple, axis=1).isin(search_name_tuples)]

    cols_to_use = players_match_df.columns.difference(df.columns).to_list()
    cols_to_use.append("search_full_name")
    df = pd.merge(df, players_match_df[cols_to_use], how="left", on="search_full_name")
    for index, row in df.iterrows():
        if row["position"] == "DEF":
            df.loc[index, "sleeper_id"] = row["team"]
        else:
            df.loc[index, "sleeper_id"] = row["player_id"]
    match_search_names = df['search_full_name'].to_list()
    missing_search_names = [n for n in search_names if n not in match_search_names]
    if missing_search_names:
        print(f"Missing Search Names: {missing_search_names}")
    return df

"""


def get_adp_df(adp_type="2qb", adp_year=YEAR, teams_count=12, positions="all"):
    start_time = time.time()
    adp_type = adp_type.lower()
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


# df = get_adp_df()

# print(df[df['sleeper_id'].isnull()])


