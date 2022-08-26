import pandas as pd
import requests
import pandas as pd
from pathlib import Path
import re
from datetime import datetime
import json
from sleeper_ids import get_sleeper_ids
from scrape_fantasy_pros import merge_dfs


def get_chen_tiers(scoring):
    # ---- Declare Paths, URLs, and position list------ #
    save_path = Path('data/rankings')
    save_path.mkdir(parents=True, exist_ok=True)
    positions = ["QB", "RB", "WR", "TE"]

    if scoring.lower() in ['half-ppr', 'half_ppr']:
        scoring = 'half'

    TODAY = datetime.today().strftime('%Y-%m-%d')
    if scoring.lower() == 'half':
        score_path = 'half-ppr'
    else:
        score_path = scoring.lower()

    chen_json = Path(f"data/rankings/chen_tiers.json")

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
                       "Worst.Rank": "worst_rank",
                       "Avg.Rank": "avg_rank",
                       "Std.Dev": "std_dev"}
        cols_for_df = [v for k, v in col_changes.items()]

        # ----- Nested For Loop to get the cheat sheet for each position for each score type ----#
        # Going to Concat each position and then merge the 3 scoring DFs.
        score_df_list = []
        for s in ['ppr', 'half', 'standard']:
            pos_df_list = []
            for p in positions:
                # ---- Assign the URL for the API call ---- #
                if p == "QB":
                    url = f"https://s3-us-west-1.amazonaws.com/fftiers/out/weekly-{p}.csv"
                elif s in ['standard', 'non-ppr', 'non_ppr']:
                    url = f"https://s3-us-west-1.amazonaws.com/fftiers/out/weekly-{p.upper()}.csv"
                else:
                    url = f"https://s3-us-west-1.amazonaws.com/fftiers/out/weekly-{p.upper()}-{scoring.upper()}.csv"
                temp_df = pd.read_csv(url)
                temp_df.rename(columns={'Rank': f'chen_pos_rank_{s}',
                                        'Tier': f'chen_tier_{s}',
                                        'Player.Name': 'name',
                                        'Position': 'position'}, inplace=True)
                temp_df['name_pos'] = temp_df['name'] + " " + temp_df['position']
                pos_df_list.append(temp_df)
            pos_df = pd.concat(pos_df_list)
            score_df_list.append(pos_df)

        # Merge the 3 chen dataframes
        chen_df = merge_dfs(score_df_list[0], score_df_list[1], 'name_pos', how='outer')
        chen_df = merge_dfs(chen_df, score_df_list[2], 'name_pos', how='left')

        # TODO fix the dupe sleeper values. Either merge the Chen df on the FPros on another column, or fix sleeper
        chen_df = get_sleeper_ids(chen_df)

        # Fill the NA values, recast those columns as integers
        chen_df.fillna(999, inplace=True)
        for col in ['standard', 'half', 'ppr']:
            chen_df[[f'chen_pos_rank_{col}', f'chen_tier_{col}']] = \
                chen_df[[f'chen_pos_rank_{col}', f'chen_tier_{col}']].astype(int)

        # ---- Finally, after making the DF nad saving the CSVs, save all as JSON ------ #
        # df = df[["position_rank_chen", "position_tier_chen", "name", "sleeper_id"]]
        players_dict = chen_df.to_dict(orient="records")
        chen_dict = {"last_saved": TODAY, "players": players_dict}
        with open(chen_json, "w") as file:
            json.dump(chen_dict, file, indent=4)

        return chen_df


# df = get_chen_tiers()

