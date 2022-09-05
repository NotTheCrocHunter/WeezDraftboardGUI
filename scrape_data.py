import pandas as pd
from scrape_bchen import get_chen_tiers
from scrape_ffcalc_adp import get_adp_df
from scrape_fantasy_pros import merge_dfs, scrape_fantasy_pros
import time
from sleeper_ids import get_sleeper_ids
from sleeper_wrapper import Players
from datetime import datetime
from pathlib import Path
import json
from clay_projections import get_clay_projections


players = Players()
ply = players.get_players_df()
fdf = scrape_fantasy_pros()
cdf = get_chen_tiers()
adf = get_adp_df()


def scrape_data():
    """
    Check Local File and date , If local file not found or date note today, script commences
    """
    save_path = Path('data')
    save_path.mkdir(parents=True, exist_ok=True)
    TODAY = datetime.today().strftime('%Y-%m-%d')
    p_pool_json = Path('data/player_pool_data.json')
    try:
        with open(p_pool_json, "r") as file:
            player_pool_dict = json.load(file)
            p_pool_saved_date = datetime.fromisoformat(player_pool_dict["accessed"]).strftime('%Y-%m-%d')
    except FileNotFoundError:
        p_pool_saved_date = None

    if p_pool_saved_date == TODAY:
        print("Loading local Fantasy Pros data")
        df = pd.DataFrame(player_pool_dict["players"])
        return df
    else:
        print("Updating data the Player Pool. This may take a moment")
        pass
    
    # Get all the dataframes
    # Fix Chen and FPro Tiers and ranks to be: ecr_tier_ppr, chen_tier_half_ppr, etc. 
    players = Players()
    ply = players.get_players_df()
    fdf = scrape_fantasy_pros()
    cdf = get_chen_tiers()
    p_pool = merge_dfs(fdf, cdf, "name_pos", how="left")
    p_pool = get_sleeper_ids(p_pool, ply)
    p_pool.loc[p_pool['yahoo_id'] == '33996', 'sleeper_id'] = '8151'  # = p_pool['sleeper_id']8151
    p_pool.loc[p_pool['fantasy_pros_player_id'] == '12091', 'sleeper_id'] = '1895'  # = p_pool['sleeper_id']8151

    adf = get_adp_df()
    adf = get_sleeper_ids(adf, ply)
    adf.loc[adf['ffcalc_id'] == '5625', 'sleeper_id'] = '8151' # Ken Walker
    adf.loc[adf['ffcalc_id'] == '5232', 'sleeper_id'] = '7670'  # Josh Palmer
    adf.loc[adf['ffcalc_id'] == '3043', 'sleeper_id'] = '8151'  # Jeff Wilson
    adf.loc[adf['ffcalc_id'] == '2360', 'sleeper_id '] = '8151'  # Kenyan Drake
    # remove kickers and defenses
    adp_kd = adf.loc[adf['position'].isin(["PK", "DEF"])]

    # Fix Defensive Names
    adp_kd.loc[adp_kd["position"] == "DEF", "last_name"] = adp_kd.name.str.split(' ').str[-1]
    adp_kd.loc[adp_kd["position"] == "DEF", "first_name"] = adp_kd.name.str.replace(' Defense', '')
    # adp_kd.loc[adp_kd["position"] == "PK", "position"] = "K"
    adp_kd = get_sleeper_ids(adp_kd, ply)
    # Get ADP DF of only position groups
    adf = adf.loc[adf['position'].isin(["QB", "WR", "TE", "RB"])]
    
    # merge adp w/out K and D to the fpros dataframe
    p_pool = merge_dfs(p_pool, adf, "sleeper_id", how="left")
    p_pool = p_pool.loc[p_pool['sleeper_id'].isna() == False]
    p_pool = pd.concat([p_pool, adp_kd])

    """
    DROP SCORING COLUMNS AND MERGE CLAY PROJECTIONS
    
    """
    # removes empty sleeper_id columns from p_pool
    p_pool.drop(p_pool.columns[[-1, -2, -3]], axis=1, inplace=True)
    # remove ecr_projection columns for now
    p_pool.drop(['fpts', 'pass_att', 'pass_cmp', 'pass_yd', 'pass_td',
                       'pass_int', 'rush_yd', 'rush_td', 'rec',
               'rec_yd', 'rec_td'], axis=1, inplace=True)
    clay_df = get_clay_projections()
    clay_df.rename(columns={'carry': 'rush_att'}, inplace=True)
    clay_cols = ['clay_pos_rank', 'fpts', 'games', 'pass_att', 'pass_cmp', 'pass_yd', 'pass_td', 'pass_int', 'sk',
                 'rush_att', 'rush_yd', 'rush_td', 'targets', 'rec', 'rec_yd', 'rec_td', 'car% ', 'targ%']
    clay_df.fillna(0, inplace=True)
    clay_df[clay_cols] = clay_df[clay_cols].apply(pd.to_numeric, errors='coerce', axis=1)
    #    = clay_df[clay_cols].
    p_pool = merge_dfs(p_pool, clay_df, 'sleeper_id', how="left")
    print(clay_df.columns)

    """
    Fix Nan Columns
    """
    for s in ['ppr', 'non_ppr', 'half_ppr']:
        p_pool[f'chen_tier_{s}'].fillna(p_pool[f'chen_tier_{s}'].max() + 1, inplace=True) # .astype(int) #  == True,  'ecr_tier_ppr']
        p_pool[f'chen_tier_{s}'] = p_pool[f'chen_tier_{s}'].astype("Int64")
    
    player_pool_dict = {"accessed": TODAY, "players": p_pool.to_dict(orient="records")}
    with open(p_pool_json, "w") as file:
        json.dump(player_pool_dict, file, indent=4)
    return p_pool


# df = get_chen_tiers('non-ppr')
df = scrape_data()
print(df)
