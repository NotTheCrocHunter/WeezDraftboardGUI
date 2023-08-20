import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from sleeper_ids import get_sleeper_ids
import time
from scrape_data import merge_dfs

positions = ["QB", "RB", "WR", "TE"]
scoring_cats = ['standard', 'ppr', 'half-point-ppr']
group_positions = ['overall, superflex']

# --- Get Position DFs for each scoring_format type --- #
# Rename Position Columns
# Merge Position DFs

# --- Concat Position Types  --- #

# -- Get group DFs for each scoring_format type ---- #
# --- Rename Group DF columns --- #
# ---- Merge Group DFs  to one --- #
# --- Merge Group DFs to Position DF --- #


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
    score_df = pd.DataFrame(position_dict["players"])

    if scoring.lower() == "half-point-ppr":
        scoring = "half_ppr"
    elif scoring.lower() == "standard":
        scoring = "non_ppr"

    if pos.lower() not in ['overall', 'superflex']:
        score_df["position"] = pos
        score_df.rename(columns={"pos_rank": f"ecr_{scoring}_pos_rank",
                                 "tier": f"ecr_{scoring}_tier"},
                        inplace=True)
    else:
        score_df[f"{pos.lower()}_{scoring}_rank"] = score_df.index + 1
        score_df.rename(columns={"pos_rank": f"{pos.lower()}_{scoring}_pos_rank",
                                 "tier": f"{pos.lower()}_{scoring}_tier"},
                        inplace=True)

    with open(f'data/fpros/fpros_{scoring.replace("-", "_")}_rank_{pos.lower()}.json', "w") as file:
        json.dump(data, file, indent=4)

    # --- After Each Position has gotten ranks for each score type, Append position DF to rank_df_list ----- #
    return score_df


qb_df = get_ranks(scoring="standard", pos="qb")

ppr_wr = get_ranks(scoring="ppr", pos="wr")
std_wr = get_ranks(scoring="standard", pos="wr")
half_wr = get_ranks(scoring="half-point-ppr", pos="wr")
wr_df = merge_dfs(ppr_wr, std_wr, "player_id", how="inner")
wr_df = merge_dfs(wr_df, half_wr, "player_id", how="left")

ppr_rb = get_ranks(scoring="ppr", pos="rb")
std_rb = get_ranks(scoring="standard", pos="rb")
half_rb = get_ranks(scoring="half-point-ppr", pos="rb")
rb_df = merge_dfs(ppr_rb, std_rb, "player_id", how="inner")
rb_df = merge_dfs(rb_df, half_rb, "player_id", how="left")

ppr_te = get_ranks(scoring="ppr", pos="te")
std_te = get_ranks(scoring="standard", pos="te")
half_te = get_ranks(scoring="half-point-ppr", pos="te")
te_df = merge_dfs(ppr_te, std_te, "player_id", how="inner")
te_df = merge_dfs(te_df, half_te, "player_id", how="left")

pos_df = pd.concat([qb_df, rb_df, wr_df, te_df])

ppr_sf = get_ranks(scoring="ppr", pos="superflex")
half_sf = get_ranks(scoring="half-point-ppr", pos="superflex")
std_sf = get_ranks(scoring="standard", pos="superflex")
sf_df = merge_dfs(ppr_sf, std_sf, "player_id", how="inner")
sf_df = merge_dfs(sf_df, half_sf, "player_id", how="left")

ppr_ovr = get_ranks(scoring="ppr", pos="overall")
half_ovr = get_ranks(scoring="half-point-ppr", pos="overall")
std_ovr = get_ranks(scoring="standard", pos="overall")
ovr_df = merge_dfs(ppr_ovr, std_ovr, "player_id", how="inner")
ovr_df = merge_dfs(ovr_df, half_ovr, "player_id", how="inner")



rank_df = merge_dfs(sf_df, pos_df, "player_id", how="inner")
rank_df = merge_dfs(pos_df, ovr_df, "player_id", how="inner")

print(rank_df)






""""
superflex_df = rank_df_list.pop(-1)
superflex_df.rename(columns={"rank_ecr": "superflex_rank_ecr", "tier": "superflex_tier_ecr"}, inplace=True)
superflex_df = superflex_df[["player_id", "superflex_rank_ecr", "superflex_tier_ecr"]]

df = pd.concat(rank_df_list)
df.rename(columns={"rank_ecr": "position_rank_ecr", "tier": "position_tier_ecr"}, inplace=True)
ecr_rank_df = merge_dfs(df, superflex_df, "player_id")
ecr_rank_df[["superflex_rank_ecr", "superflex_tier_ecr"]] = ecr_rank_df[
    ["superflex_rank_ecr", "superflex_tier_ecr"]].fillna(value=999).astype(int)"""