import pandas as pd
import requests
import pandas as pd
from pathlib import Path
import re
from datetime import datetime
import json
from sleeper_ids import get_sleeper_ids
from scrape_fantasy_pros import merge_dfs


def get_chen_tiers():
    # ---- Declare Paths, URLs, and position list------ #
    save_path = Path('data')
    save_path.mkdir(parents=True, exist_ok=True)
    positions = ["QB", "RB", "WR", "TE"]

    TODAY = datetime.today().strftime('%Y-%m-%d')

    chen_json = Path(f"data/chen_tiers.json")

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
        # Going to Concat each position and then merge the 3 scoring_format DFs.
        score_df_list = []
        for s in ['ppr', 'half_ppr', 'non_ppr']:
            pos_df_list = []
            for p in positions:
                # ---- Assign the URL for the API call ---- #
                if p == "QB":
                    url = f"https://s3-us-west-1.amazonaws.com/fftiers/out/weekly-{p}.csv"
                elif s in ['standard', 'non-ppr', 'non_ppr']:
                    url = f"https://s3-us-west-1.amazonaws.com/fftiers/out/weekly-{p.upper()}.csv"
                elif s == 'half_ppr':
                    url = f"https://s3-us-west-1.amazonaws.com/fftiers/out/weekly-{p.upper()}-HALF.csv"
                else:
                    url = f"https://s3-us-west-1.amazonaws.com/fftiers/out/weekly-{p.upper()}-PPR.csv"
                temp_df = pd.read_csv(url)

                temp_df.rename(columns={'Rank': f'chen_pos_rank_{s}',
                                        'Tier': f'chen_tier_{s}',
                                        'Player.Name': 'name',
                                        'Position': 'position'}, inplace=True)
                temp_df['name_pos'] = temp_df['name'] + " " + p
                pos_df_list.append(temp_df)
            pos_df = pd.concat(pos_df_list)
            score_df_list.append(pos_df)

        ppr_df = score_df_list[0]
        half_df = score_df_list[1]
        non_df = score_df_list[2]

        chen_series = pd.concat([ppr_df['name_pos'], half_df['name_pos'], non_df['name_pos']])
        chen_series.drop_duplicates(inplace=True)
        chen_df = pd.DataFrame(chen_series)
        for x in score_df_list:
            chen_df = merge_dfs(chen_df, x, 'name_pos', how="left")

        # ---- Finally, after making the DF nad saving the CSVs, save all as JSON ------ #
        # df = df[["position_rank_chen", "position_tier_chen", "name", "sleeper_id"]]
        players_dict = chen_df.to_dict(orient="records")
        chen_dict = {"last_saved": TODAY, "players": players_dict}
        with open(chen_json, "w") as file:
            json.dump(chen_dict, file, indent=4)

        return chen_df


# df = get_chen_tiers()

# print("df")

