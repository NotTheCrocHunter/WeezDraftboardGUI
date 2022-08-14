import pandas as pd
import requests
import pandas as pd
from pathlib import Path
import re
# from draftboard_brain import get_sleeper_ids
from datetime import datetime
import json
# from sleeper_wrapper import Players
from sleeper_ids import get_sleeper_ids


def get_chen_tiers():
    # ---- Declare Paths, URLs, and position list------ #
    save_path = Path('data/rankings/chen')
    Path('data/rankings/chen').mkdir(parents=True, exist_ok=True)
    positions = ["QB", "RB", "WR", "TE"]
    scoring_type = "PPR"
    TODAY = datetime.today().strftime('%Y-%m-%d')
    chen_json = Path("data/rankings/chen/chen_tiers.json")

    try:
        with open(chen_json, "r") as file:
            chen_dict = json.load(file)
            chen_date = chen_dict["last_saved"]
    except FileNotFoundError:
        chen_date = None

    if chen_date == TODAY:
        df = pd.DataFrame(chen_dict["players"])
        return df
    else:
        print(f"Updating Chen tiers.")
        # ---- File doesn't exist, make the CSV calls ----- #
        # --- Dict to rename columns ---- #
        col_changes = {"Rank": "position_rank_chen",
                       "Tier": "position_tier_chen",
                       "Player.Name": "name",
                       "Position": "position",
                       "Best.Rank": "bye",
                       "Worst.Rank": "worst_rank",
                       "Avg.Rank": "avg_rank",
                       "Std.Dev": "std_dev"}
        cols_for_df = [v for k, v in col_changes.items()]
        # ----- For Loop to get the cheat sheet for each position ----#
        pos_df_list = []
        for p in positions:
            # ---- Assign the URL for the API call ---- #
            if p == "QB":
                url = "https://s3-us-west-1.amazonaws.com/fftiers/out/weekly-QB.csv"
            else:
                url = f"https://s3-us-west-1.amazonaws.com/fftiers/out/weekly-{p}-{scoring_type}.csv"
            # -- Make the request and save the CSV locally ---- #
            r = requests.get(url)
            temp_save_path = save_path / f"{p}.csv"
            with open(temp_save_path, 'wb') as file:
                file.write(r.content)
            # ---- Make dataframe of CSV ------ #
            temp_df = pd.read_csv(temp_save_path)
            print(f"Length of {p} df = {len(temp_df)}")
            # ----- Rename Columns ------ #
            temp_df.rename(columns=col_changes, inplace=True)
            # ----- Get Sleeper IDs ------ #
            temp_df = get_sleeper_ids(temp_df)
            print(f"Length of {p} df AFTER sleeper IDs = {len(temp_df)}")
            # ----- Concat to df ----
            pos_df_list.append(temp_df)

        # ---- Finally, after making the DF nad saving the CSVs, save all as JSON ------ #
        df = pd.concat(pos_df_list, axis=0)
        print(f"Length of whole df = {len(df)}")
        df = df[["position_rank_chen", "position_tier_chen", "name", "sleeper_id"]]
        players_list = df.to_dict(orient="records")
        chen_dict = {"last_saved": TODAY, "scoring_type": scoring_type, "players": players_list}
        with open(chen_json, "w") as file:
            json.dump(chen_dict, file, indent=4)
        print(df.columns)

        return df


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
                row["team"] == "TB"
            if row["team"] == "FA":
                df.loc[idx, "team"] = None
        new_name = re.sub(r'\W+', '', row['name']).lower()
        if new_name[-3:] == "iii":
            new_name = new_name[:-3]
        elif new_name[-2:] in remove:
            new_name = new_name[:-2]

        if new_name == "kennethwalker":
            new_name = "kenwalker"

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
# df = get_chen_tiers()

# print(df[df['sleeper_id'].isnull()])