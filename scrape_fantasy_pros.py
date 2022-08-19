import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from sleeper_ids import get_sleeper_ids
import time


def merge_dfs(df1, df2, col_to_match, how="left"):
    cols_to_use = df2.columns.difference(df1.columns).to_list()
    cols_to_use.append(col_to_match)
    df = pd.merge(df1, df2[cols_to_use], how=how, on=col_to_match)
    return df


def scrape_fantasy_pros(scoring="ppr", week="draft"):
    save_path = Path('data/fpros')
    save_path.mkdir(parents=True, exist_ok=True)
    TODAY = datetime.today().strftime('%Y-%m-%d')
    data_file = Path(f'data/fpros/fpros_{scoring}_data.json')

    try:
        with open(data_file, "r") as file:
            fpros_dict = json.load(file)
            fpros_saved_date = datetime.fromisoformat(fpros_dict["accessed"]).strftime('%Y-%m-%d')
    except FileNotFoundError:
        fpros_saved_date = None

    if fpros_saved_date == TODAY:
        print("Loading local fantasy pros data")
        df = pd.DataFrame(fpros_dict["players"])
        return df
    else:
        print("Updating data from Fantasy Pros. This may take a moment")
        start_time = time.time()
        pass

    positions = ["QB", "RB", "WR", "TE", "SuperFlex"]

    rank_df_list = []
    for pos in positions:
        print(f"Getting ECR rankings for {pos}")
        if pos == "QB":
            url = f"https://www.fantasypros.com/nfl/rankings/{pos.lower()}-cheatsheets.php"
        else:
            url = f"https://www.fantasypros.com/nfl/rankings/{scoring.lower()}-{pos.lower()}-cheatsheets.php"
        results = requests.get(url).content
        soup = BeautifulSoup(results, "html.parser")
        pattern = re.compile(r"(?<=var ecrData = )[^;]+", re.MULTILINE)
        script = soup.find("script", {"type": "text/javascript"}, text=pattern)
        data = pattern.search(script.text).group(0)
        # make dict of json data
        data = json.loads(data)
        temp_df = pd.DataFrame(data["players"])
        temp_df["position"] = pos
        # rename columns
        rank_df_list.append(temp_df)
        with open(f'data/fpros/fpros_{scoring}_rank_{pos.lower()}.json', "w") as file:
            json.dump(data, file, indent=4)

    superflex_df = rank_df_list.pop(-1)
    superflex_df.rename(columns={"rank_ecr": "superflex_rank_ecr", "tier": "superflex_tier_ecr"}, inplace=True)
    superflex_df = superflex_df[["player_id", "superflex_rank_ecr", "superflex_tier_ecr"]]

    df = pd.concat(rank_df_list)
    df.rename(columns={"rank_ecr": "position_rank_ecr", "tier": "position_tier_ecr"}, inplace=True)
    ecr_rank_df = merge_dfs(df, superflex_df, "player_id")
    ecr_rank_df[["superflex_rank_ecr", "superflex_tier_ecr"]] = ecr_rank_df[["superflex_rank_ecr", "superflex_tier_ecr"]].fillna(value=999).astype(int)

    # ----- Now get Projections. Requires BeautifulSoup to scrape the player ids ----- #
    # --- Pandas can read the table directly, and then use the id list from BS to add to the df -- #
    """
    projection URLs to test for filtering:
    https://www.fantasypros.com/nfl/projections/rb.php?filters=11:71&week=draft
    espn: 71
    cbs: 11
    fftoday: 152
    nfl: 286
    sports illustrated: 4421
    numberfire: 73
    """

    proj_df_list = []
    for pos in positions:
        print(f"Getting projections for {pos}")
        if pos == "SuperFlex":
            continue
        if pos == "QB":
            url = f"https://www.fantasypros.com/nfl/projections/qb.php?filters=11:71&week=draft"
        else:
            url = f"https://www.fantasypros.com/nfl/projections/{pos.lower()}.php?filters=71&week={week.lower()}&scoring={scoring.lower()}"

        results = requests.get(url).content
        soup = BeautifulSoup(results, "html.parser")
        # get easy df of each page
        temp_df = pd.read_html(url)[0]
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
        temp_df["player_id"] = id_list
        temp_df["player_id"] = temp_df["player_id"].str.replace('mpb-player-', '')
        proj_df_list.append(temp_df)

    print("Combining projections and rankings dataframes")
    proj_df = pd.concat(proj_df_list)
    proj_df.fillna(0, inplace=True)
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
                            'RECEIVING_TDS': 'rec_td'}, inplace=True)
    proj_df["player_id"] = proj_df["player_id"].astype(int)
    # proj_df.loc[""]
    fp_df = merge_dfs(ecr_rank_df, proj_df, "player_id", "inner")
    fp_df.rename(columns={'player_id': 'fantasy_pros_player_id',
                          'player_name': 'name',
                          'player_team_id': 'team',
                          'player_bye_week': 'bye'}, inplace=True)
    fp_df.loc[fp_df["team"] == "JAC", "team"] = "JAX"
    fp_df["bonus_rec_te"] = fp_df["rec"].loc[fp_df["position"] == "TE"]
    fp_df["bonus_rec_te"] = fp_df['bonus_rec_te'].fillna(0)
    print("getting sleeper ids")
    fp_df = get_sleeper_ids(fp_df)

    fpros_dict = {"accessed": TODAY, "players": fp_df.to_dict(orient="records")}
    with open(data_file, "w") as file:
        json.dump(fpros_dict, file, indent=4)
    end_time = time.time()
    print(f"Total time to get Fantasy Pros ECR and Projection data: {end_time - start_time}")

    return fp_df