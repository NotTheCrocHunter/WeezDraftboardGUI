# from sleeper_wrapper import Players
import re
import pandas as pd
import json
from datetime import datetime
import requests
from pathlib import Path
import time
import pdb
# from sleeper_ids import get_sleeper_ids
from scrape_fantasy_pros import merge_dfs

YEAR = datetime.today().strftime('%Y')


def get_adp_df(teams=12, year=YEAR):
    start_time = time.time()
    """
    Check Local File and date , If local file not found or date note today, script commences
    """
    save_path = Path('data')
    save_path.mkdir(parents=True, exist_ok=True)
    TODAY = datetime.today().strftime('%Y-%m-%d')
    adp_json = Path('data/adp_data.json')

    try:
        with open(adp_json, "r") as data_file:
            adp_data = json.load(data_file)
            adp_end_date = adp_data["last_saved"]
    except FileNotFoundError:
        adp_end_date = None

    if adp_end_date == TODAY:
        print(f"Loading local ADP data")
        return pd.DataFrame(adp_data['players'])
    else:
        print(f"Updating ADP Data from Fantasy Football Calculator")
        pass

    adp_dict = {'last_saved': TODAY}

    api_points = ["2qb", 'ppr', 'half-ppr', 'standard']
    cols = {"2qb": 'superflex', 'ppr': 'ppr', 'half-ppr': 'half_ppr', 'standard': 'non_ppr'}
    df_list = []
    for adp_type in api_points:
        url = f"https://fantasyfootballcalculator.com/api/v1/adp/{adp_type}?teams={teams}&year=2021&position=all"

        response = requests.get(url)
        adp_data = response.json()

        temp_df = pd.DataFrame(adp_data['players'])

        # Rename Cols
        col = cols[adp_type]
        temp_df[f'adp_pick_{col}'] = temp_df.index + 1
        temp_df.rename(columns={"player_id": "ffcalc_id"}, inplace=True)

        df_list.append(temp_df)

    adp_id = pd.concat([_df['ffcalc_id'] for _df in df_list])
    adp_id.drop_duplicates(inplace=True)
    adp_id_df = pd.DataFrame(adp_id)
    adp_name_id = pd.concat([_df[['ffcalc_id', 'name', 'position', 'team']] for _df in df_list]) 
    adp_df = merge_dfs(adp_id_df, adp_name_id, 'ffcalc_id', how="left")
    adp_df.drop_duplicates(inplace=True)
    for x in df_list:
        adp_df = merge_dfs(adp_df, x, 'ffcalc_id', how="left")
    adp_df['name_pos'] = adp_df['name'] + ' ' + adp_df['position']
    adp_df['name_team_pos'] = adp_df['name'] + ' ' + adp_df['team'] + ' ' + adp_df['position']
    adp_dict['players'] = adp_df.to_dict(orient='records')
    with open(adp_json, 'w') as data_file:
        json.dump(adp_dict, data_file, indent=4)

    end_time = time.time()
    print(f"Time to get ADP DF: {end_time - start_time}")

    return adp_df

"""
df = get_adp_df()
df.to_html('data/calc.html')
print(df)

"""