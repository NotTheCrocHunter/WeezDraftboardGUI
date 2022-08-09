from sleeper_wrapper import Players
import re
import pandas as pd

players = Players()
players_df = players.get_players_df()


def get_sleeper_ids(df):
    # ----- Create the search_names (all lowercase, no spaces) ------ #

    search_names = []
    remove = ['jr', 'ii', 'sr']
    for idx, row in df.iterrows():
        if "team" in row.keys():
            if ["team"] == "JAC":
                df.loc[idx, "team"] = "JAX"
            if row['name'] == "Kyle Rudolph":
                row["team"] = "TB"
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
    # players_df = players.get_players_df()
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

