import camelot
import tabula
import os
import pandas as pd
from sleeper_ids import *
from sleeper_wrapper import Players
import requests
from datetime import datetime
from pathlib import Path
import json
import time
import re

def download_clay_pdf():
    clay_url = 'https://g.espncdn.com/s/ffldraftkit/22/NFLDK2022_CS_ClayProjections2022.pdf'
    file_name = 'data/clay/clay_projections.pdf'
    response = requests.get(clay_url)
    # Save the PDF
    if response.status_code == 200:
        print("Successful Response, Clay Projection PDF downloading")
        with open(file_name, "wb") as f:
            f.write(response.content)
    else:
        print(response.status_code)


def rename_teams(df):
    df.loc[df["team"] == 'ARZ', 'team'] = 'ARI'
    df.loc[df["team"] == 'BLT', 'team'] = 'BAL'
    df.loc[df["team"] == 'CLV', 'team'] = 'CLE'
    df.loc[df["team"] == 'HST', 'team'] = 'HOU'
    df.loc[df["team"].isna() == True, 'team'] = 'FA'
    return df


def get_clay_projections():
    save_path = Path('data/clay')
    save_path.mkdir(parents=True, exist_ok=True)
    TODAY = datetime.today().strftime('%Y-%m-%d')
    clay_json = Path('data/clay/clay_data.json')

    try:
        with open(clay_json, "r") as file:
            clay_dict = json.load(file)
            clay_saved_date = datetime.fromisoformat(clay_dict["accessed"]).strftime('%Y-%m-%d')
    except FileNotFoundError:
        clay_saved_date = None

    if clay_saved_date == TODAY:
        print("Loading local Mike Clay data")
        df = pd.DataFrame(clay_dict["players"])
        return df
    else:
        print("Updating Mike Clay projections. This may take a moment")
        pass
    start_time = time.time()
    download_clay_pdf()
    file = 'data/clay/clay_projections.pdf'

    print("Reading QB Table")
    qb_tables = camelot.read_pdf(file, pages='35', flavor="stream")
    qb_tables.export('data/clay/clay_qb.csv', f='csv')
    clay_qb = qb_tables[0].df
    clay_qb.drop(labels=[0, 1], inplace=True)
    clay_qb.columns = ['name', 'team', 'clay_pos_rank', 'fpts', 'games', 'pass_att', 'pass_cmp', 'pass_yd', 'pass_td',
                       'pass_int', 'sk', 'carry', 'rush_yd', 'rush_td']
    clay_qb.loc[:, 'position'] = "QB"
    clay_qb = rename_teams(clay_qb)

    print("Reading RB Tables")
    rb_cols = ['name', 'team', 'clay_pos_rank', 'fpts', 'games', 'carry', 'rush_yd', 'rush_td', 'targets', 'rec',
               'rec_yd', 'rec_td', 'car% ', 'targ%']
    rb_tables = camelot.read_pdf(file, pages='36,37,38', flavor="stream")
    rb_tables.export('data/clay/clay_rb.csv', f='csv')
    rb_df_list = []
    for x in range(len(rb_tables)):
        rb = rb_tables[x].df
        rb.drop(labels=[0, 1], inplace=True)
        rb.columns = rb_cols
        rb.loc[:, 'position'] = "RB"
        rb = rename_teams(rb)
        rb_df_list.append(rb)

    clay_rb = pd.concat(rb_df_list)

    print("Reading WR Tables")
    wr_cols = ['name', 'team', 'clay_pos_rank', 'fpts', 'games', 'carry', 'rush_yd', 'rush_td', 'targets', 'rec', 'rec_yd', 'rec_td', 'car% ', 'targ%']
    wr_tables = camelot.read_pdf(file, pages='39, 40, 41, 42, 43', flavor="stream")
    wr_tables.export('data/clay/clay_wr.csv', f='csv')
    wr_df_list = []
    for x in range(len(wr_tables)):
        wr = wr_tables[x].df
        wr.drop(labels=[0, 1], inplace=True)
        wr.columns = wr_cols
        wr.loc[:, 'position'] = "WR"
        wr = rename_teams(wr)
        wr_df_list.append(wr)
    clay_wr = pd.concat(wr_df_list)

    print("Reading TE Table")
    te_cols = ['name', 'team', 'clay_pos_rank', 'fpts', 'games', 'carry', 'rush_yd', 'rush_td', 'targets', 'rec', 'rec_yd', 'rec_td', 'car% ', 'targ%']
    te_tables = camelot.read_pdf(file, pages='44, 45', flavor="stream")
    te_tables.export('data/clay/clay_te.csv', f='csv')
    te_df_list = []
    for x in range(len(te_tables)):
        te = te_tables[x].df
        te.drop(labels=[0, 1], inplace=True)
        te.columns = te_cols
        te.loc[:, 'position'] = "TE"
        te['bonus_rec_te'] = te['rec']
        te = rename_teams(te)
        te_df_list.append(te)

    clay_te = pd.concat(te_df_list)

    # Combine positional columns and create the search_full_name column for matching
    clay_df = pd.concat([clay_qb, clay_rb, clay_wr, clay_te])
    clay_df.fillna(value=0, inplace=True)
    clay_df.loc[:, "search_full_name"] = clay_df["name"].str.lower().replace(r'[^a-zA-Z]', '').str.\
        replace(r'(?:iii|ii|iv|jr|Jr)','', regex=True).str.replace(" ", "").str.replace("-", "").str.replace(".", "")
    clay_df.loc[clay_df["name"] == "Michael A. Thomas"] = "Michael Thomas"

    # iterate through the positions to grab the sleeper ids
    clay_sl_list = []
    for pos in ["QB", "WR", "RB", "TE"]:
        sleeper = Players().get_players_df([pos])
        sleeper = sleeper.loc[sleeper["team"].isna() == False]
        s_cols = ['full_name', 'player_id', 'team', 'search_full_name', 'first_name', 'last_name']
        sleeper = sleeper[s_cols]
        clay = clay_df.loc[clay_df["position"] == pos]
        clay = get_sleeper_ids(clay, sleeper)
        clay_sl_list.append(clay)

    clay_df = pd.concat(clay_sl_list)

    clay_df.to_csv('data/clay/clay_projections.csv', index=False)
    clay_dict = {"accessed": TODAY, "players": clay_df.to_dict(orient="records")}

    with open(clay_json, "w") as file:
        json.dump(clay_dict, file, indent=4)
    end_time = time.time()
    print(f"Total time to get Clay Projections: {end_time - start_time}")
    return clay_df


"""
scoring_settings = {
    "pass_yd": 0.04,
    "pass_td": 4.0,
    "pass_int": -2.0,
    "rec": 1.0,
    "rec_yd": 0.1,
    "rec_td": 6.0,
    "rush_yd": 0.1,
    "rush_td": 6.0,
    "fum": -2.0,
    "bonus_rec_te": 0.5,
    "bonus_rec_rb": 0.0,
    "bonus_rec_wr": 0.0}
tables = camelot.read_pdf(file, pages='35', flavor="stream")
tables.export('data/clay_qb.csv', f='csv')
df = tables[0].df

print(df.head())
sleeper_players = Players()

s_qb = sleeper_players.get_players_df(["QB"])
s_rb = sleeper_players.get_players_df(["RB"])
s_wr = sleeper_players.get_players_df(["WR"])
s_te = sleeper_players.get_players_df(["TE"])

"""

