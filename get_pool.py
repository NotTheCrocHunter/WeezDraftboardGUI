import pandas as pd

# from scrape_fpros import get_fpros_data, merge_dfs
from scrape_bchen import get_chen_tiers
from scrape_ffcalc_adp import get_adp_df
from scrape_fantasy_pros import merge_dfs, scrape_fantasy_pros

def make_player_pool(player_count=400, adp_type='2qb'):
    fdf = scrape_fantasy_pros()
    cdf = get_chen_tiers()
    p_pool = merge_dfs(fdf, cdf, "sleeper_id", how="left")

    # ---- Get ADP info, split K and DEF, fix DEF names, Merge adf, concat K and D back into p_pool
    adf = get_adp_df(adp_type)
    # remove kickers and defenses
    adp_kd = adf.loc[adf['position'].isin(["PK", "DEF"])]

    # Fix Defensive Names
    adp_kd.loc[adp_kd["position"] == "DEF", "last_name"] = adp_kd.name.str.split(' ').str[-1]
    adp_kd.loc[adp_kd["position"] == "DEF", "first_name"] = adp_kd.name.str.replace(' Defense', '')

    # Get ADP DF of only position groups
    adf = adf.loc[adf['position'].isin(["QB", "WR", "TE", "RB"])]
    # merge adp w/out K and D to the fpros dataframe
    p_pool = merge_dfs(p_pool, adf, "sleeper_id", how="outer")

    p_pool = pd.concat([p_pool, adp_kd])

    return p_pool
