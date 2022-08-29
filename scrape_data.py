import pandas as pd
from scrape_bchen import get_chen_tiers
from scrape_ffcalc_adp import get_adp_df
from scrape_fantasy_pros import merge_dfs, scrape_fantasy_pros
import time
from sleeper_ids import get_sleeper_ids
from sleeper_wrapper import Players


def scrape_data():
    # Get all the dataframes
    # Fix Chen and FPro Tiers and ranks to be: ecr_tier_ppr, chen_tier_half_ppr, etc. 
    players = Players()
    ply = players.get_players_df()
    fdf = scrape_fantasy_pros()
    cdf = get_chen_tiers()
    p_pool = merge_dfs(fdf, cdf, "name_pos", how="left")
    p_pool = get_sleeper_ids(p_pool, ply)
    p_pool.loc[p_pool['player_yahoo_id'] == '33996', 'sleeper_id'] = '8151'  #  = p_pool['sleeper_id']8151
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
    
    # Get ADP DF of only position groups
    adf = adf.loc[adf['position'].isin(["QB", "WR", "TE", "RB"])]
    
    # merge adp w/out K and D to the fpros dataframe
    p_pool = merge_dfs(p_pool, adf, "sleeper_id", how="left")
    p_pool = p_pool.loc[p_pool['sleeper_id'].isna() == False]
    p_pool = pd.concat([p_pool, adp_kd])

    """
    Fix Nan Columns
    """
    for s in ['ppr', 'non_ppr', 'half_ppr']:
        p_pool[f'chen_tier_{s}'].fillna(p_pool[f'chen_tier_{s}'].max() + 1, inplace=True) # .astype(int) #  == True,  'ecr_tier_ppr']
        p_pool[f'chen_tier_{s}'] = p_pool[f'chen_tier_{s}'].astype("Int64")
    return p_pool


# df = get_chen_tiers('non-ppr')
# df = scrape_data()
# print(df)
