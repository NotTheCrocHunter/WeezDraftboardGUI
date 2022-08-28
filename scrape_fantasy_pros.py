import pdb
import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import time


def merge_dfs(df1, df2, col_to_match, how="left"):
    cols_to_use = df2.columns.difference(df1.columns).to_list()
    cols_to_use.append(col_to_match)
    df = pd.merge(df1, df2[cols_to_use], how=how, on=col_to_match)
    return df


def get_ranks(scoring, pos):
    print(f"Getting {scoring} ECR rankings for {pos}")

    if pos.lower() == "overall" and scoring == "standard":
        url = "https://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php"
    elif scoring == "standard" or pos.lower() == "qb":
        url = f"https://www.fantasypros.com/nfl/rankings/{pos.lower()}-cheatsheets.php"
    elif pos.lower() == "overall" and scoring != "standard":
        url = f"https://www.fantasypros.com/nfl/rankings/{scoring.lower()}-cheatsheets.php"
    else:
        url = f"https://www.fantasypros.com/nfl/rankings/{scoring.lower()}-{pos.lower()}-cheatsheets.php"

    # ----- Make Soup and find ecrData content ------- #
    results = requests.get(url).content
    soup = BeautifulSoup(results, "html.parser")
    pattern = re.compile(r"(?<=var ecrData = )[^;]+", re.MULTILINE)
    script = soup.find("script", {"type": "text/javascript"}, text=pattern)
    data = pattern.search(script.text).group(0)

    # make dict of json data
    position_dict = json.loads(data)
    ecr_rank_df = pd.DataFrame(position_dict["players"])

    if scoring.lower() == "half-point-ppr":
        scoring = "half_ppr"
    elif scoring.lower() == "standard":
        scoring = "non_ppr"

    #  'ecr_non_ppr_pos_rank'
    if pos.lower() not in ['overall', 'superflex']:
        ecr_rank_df["position"] = pos.upper()

        ecr_rank_df.rename(columns={"pos_rank": f"ecr_pos_rank_{scoring}",
                                    "tier": f"ecr_tier_{scoring}"},
                           inplace=True)

    else:
        ecr_rank_df[f"{pos.lower()}_{scoring}_rank"] = ecr_rank_df.index + 1
        ecr_rank_df.rename(columns={"pos_rank": f"{pos.lower()}_{scoring}_pos_rank",
                                    "tier": f"{pos.lower()}_{scoring}_tier"},
                           inplace=True)

    if pos.lower() == 'qb':
        for x in ['ppr', 'half_ppr']:
            # Position Ranks
            ecr_rank_df[f'ecr_pos_rank_{x}'] = ecr_rank_df["ecr_pos_rank_non_ppr"]
            ecr_rank_df[f'ecr_tier_{x}'] = ecr_rank_df["ecr_tier_non_ppr"]

    # --- After Each Position has gotten ranks for each score type, Append position DF to rank_df_list ----- #
    return ecr_rank_df


def scrape_fantasy_pros(scoring="ppr", week="draft"):
    """
    Check Local File and date , If local file not found or date note today, script commences
    """
    save_path = Path('data')
    save_path.mkdir(parents=True, exist_ok=True)
    TODAY = datetime.today().strftime('%Y-%m-%d')
    fpros_json = Path('data/fpros_data.json')

    try:
        with open(fpros_json, "r") as file:
            fpros_dict = json.load(file)
            fpros_saved_date = datetime.fromisoformat(fpros_dict["accessed"]).strftime('%Y-%m-%d')
    except FileNotFoundError:
        fpros_saved_date = None

    if fpros_saved_date == TODAY:
        print("Loading local Fantasy Pros data")
        df = pd.DataFrame(fpros_dict["players"])
        return df
    else:
        print("Updating data from Fantasy Pros. This may take a moment")
        pass

    # Get ECR ranks starting with QB
    print("Getting Positional Ranks")
    start_time = time.time()
    ecr_ranks = get_ranks(scoring="standard", pos="qb")

    for pos in ['rb', 'wr', 'te', 'superflex', 'overall']:
        # get the scoring DFs
        ppr = get_ranks(scoring="ppr", pos=pos)
        std = get_ranks(scoring="standard", pos=pos)
        half = get_ranks(scoring="half-point-ppr", pos=pos)

        # Combining the positional DFs
        pos_df = merge_dfs(half, ppr, "player_id", how="left")
        pos_df = merge_dfs(pos_df, std, "player_id", how="left")

        # Concat the positional DFs, Merge the overall/superflex DFs
        if pos in ['rb', 'wr', 'te']:
            ecr_ranks = pd.concat([ecr_ranks, pos_df])
        else:
            ecr_ranks = merge_dfs(ecr_ranks, pos_df, "player_id", how="left")

    # Drop dupes and Fill NA rank columns
    ecr_ranks.drop_duplicates(subset=['player_id'], keep='last', inplace=True)  # Dropping the dupes because Taysom Hill
    for rank in ["superflex", "overall"]:
        for s in ["ppr", "half_ppr", "non_ppr"]:
            ecr_ranks[f'{rank}_{s}_rank'].fillna(999, inplace=True)
            ecr_ranks.astype({f'{rank}_{s}_rank': int})

    end_time = time.time()
    print(f"Total time to scrape Fantasy Pros ranks: {end_time - start_time}")

    # ----- Now get Projections. Requires BeautifulSoup to scrape the player ids ----- #
    # --- Pandas can read the table directly, and then use the id list from BS to add to the df -- #


    """
    GETTING PROJECTIONS
    """
    start_time = time.time()
    proj_df_list = []
    for pos in ["QB", "RB", "WR", "TE"]:
        print(f"Getting projections for {pos}")
        if pos == "QB":
            url = f"https://www.fantasypros.com/nfl/projections/qb.php?week=draft"
        else:
            url = f"https://www.fantasypros.com/nfl/projections/{pos.lower()}.php?week={week.lower()}&scoring={scoring.lower()}"

        results = requests.get(url).content
        soup = BeautifulSoup(results, "html.parser")
        # get easy df of each page
        temp_df = pd.read_html(url)[0]
        temp_df['position'] = pos.upper()
        # find rows to grab the player ids
        rows = soup.find_all('tr')
        id_list = []
        # iterate through rows to extract the IDs (each item returns as a list w/ 2 elements. only getting the first)
        for row in rows:
            cls = row.attrs.get("class")
            if cls:
                id_list.append(cls[0])
            else:
                pass
        # each ID list is by position. add that to the easy df
        if len(temp_df) == len(id_list):
            temp_df["player_id"] = id_list
            temp_df["player_id"] = temp_df["player_id"].str.replace('mpb-player-', '')
        else:
            temp_df["player_id"] = None

        proj_df_list.append(temp_df)

    print("Combining projections and rankings dataframes")
    proj_df = pd.concat(proj_df_list)
    end_time = time.time()
    print(f"Total time to scrape Fantasy Pros projections: {end_time - start_time}")

    print("Cleaning up Projection Columns")
    proj_df.columns = proj_df.columns.get_level_values(0) + '_' + proj_df.columns.get_level_values(1)
    proj_df.rename(columns={'Unnamed: 0_level_0_Player': 'name_team',
                            'PASSING_ATT': 'pass_att',
                            'PASSING_CMP': 'pass_cmp',
                            'PASSING_YDS': 'pass_yd',
                            'PASSING_TDS': 'pass_td',
                            'PASSING_INTS': 'pass_int',
                            'RUSHING_ATT': 'rush_att',
                            'RUSHING_YDS': 'rush_yd',
                            'RUSHING_TDS': 'rush_td',
                            'MISC_FL': 'fum_lost',
                            'MISC_FPTS': 'fpts',
                            'player_id_': 'player_id',
                            'RECEIVING_REC': 'rec',
                            'RECEIVING_YDS': 'rec_yd',
                            'RECEIVING_TDS': 'rec_td',
                            'position_': 'position'}, inplace=True)

    # Adding name_team_pos to join with the projections DF bc the player_id was breaking
    ecr_ranks['name_team_pos'] = ecr_ranks['player_name'] + " " + ecr_ranks['player_team_id'] + " " + ecr_ranks[
        'player_position_id']
    proj_df['name_team_pos'] = proj_df['name_team'] + " " + proj_df['position']
    fp_df = merge_dfs(ecr_ranks, proj_df, "name_team_pos", "left")
    fp_df.rename(columns={'player_id': 'fantasy_pros_player_id',
                          'player_name': 'name',
                          'player_team_id': 'team',
                          'player_bye_week': 'bye'}, inplace=True)
    fp_df['name_pos'] = fp_df['name'] + " " + fp_df['position']
    fp_df.loc[fp_df["team"] == "JAC", "team"] = "JAX"
    score_cols = ['rec_yd', 'rec_td', 'rec', 'pass_yd', 'pass_td', 'pass_int', 'pass_att', 'pass_cmp', 'rush_yd',
                  'rush_td', 'rush_att']
    fp_df[score_cols] = fp_df[score_cols].fillna(0)  # .update(fp_df[].fillna(0, inplace=True))
    # Fill Bonus Columns
    for pos in ['rb', 'wr', 'te']:
        fp_df[f"bonus_rec_{pos}"] = fp_df["rec"].loc[fp_df["position"] == pos.upper()]
        fp_df[f"bonus_rec_{pos}"] = fp_df[f'bonus_rec_{pos}'].fillna(0)
    # print("getting sleeper ids")
    # fp_df = get_sleeper_ids(fp_df)
    # Drop dupes and NA after the sleeper_id grab  TODO: Work on the Sleeper ID
    fp_df.drop_duplicates(subset=['fantasy_pros_player_id'], keep='last', inplace=True)
    # fp_df.dropna(subset=['sleeper_id'], inplace=True)
    fpros_dict = {"accessed": TODAY, "players": fp_df.to_dict(orient="records")}
    with open(fpros_json, "w") as file:
        json.dump(fpros_dict, file, indent=4)
    end_time = time.time()
    print(f"Total time to get Fantasy Pros ECR and Projection data: {end_time - start_time}")

    return fp_df
"""
_a = scrape_fantasy_pros()

print(_a)
"""
