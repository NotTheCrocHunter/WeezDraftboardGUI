from sleeper_wrapper import Players
import re
import pandas as pd
# from scrape_fantasy_pros import scrape_fantasy_pros, merge_dfs
# from scrape_ffcalc_adp import get_adp_df
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pdb
import difflib


def fuzzy_merge(df_1, df_2, key1, key2, threshold=90, limit=2):
    """
    :param df_1: the left table to join
    :param df_2: the right table to join
    :param key1: key column of the left table
    :param key2: key column of the right table
    :param threshold: how close the matches should be to return a match, based on Levenshtein distance
    :param limit: the amount of matches that will get returned, these are sorted high to low
    :return: dataframe with boths keys and matches
    """
    s = df_2[key2].tolist()

    m = df_1[key1].apply(lambda x: process.extract(x, s, limit=limit))
    df_1['matches'] = m

    m2 = df_1['matches'].apply(lambda x: ', '.join([i[0] for i in x if i[1] >= threshold]))
    df_1['matches'] = m2

    return df_1


def strip_names(df, key):
    try:
        df[key] = df[key].str.replace(r'[^\w\s]+', '')
    except KeyError:
        df[key] = df[key].str.replace(r'[^\w\s]+', '')
        df.rename(columns={'Name': 'name'}, inplace=True)
    return df


def get_sleeper_ids(df, players_df):
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

        if new_name == "kenwalker":
            new_name = "kennethwalker"

        if new_name == "mitchelltrubisky":
            new_name = "mitchtrubisky"

        if new_name == "williamfullerv":
            new_name = "williamfuller"

        if new_name == "gabrieldavis":
            new_name = "gabedavis"

        if new_name == "isaihpacheco":
            new_name = "isiahpacheco"
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


"""
a = get_adp_df()

a = get_sleeper_ids(a)

print(a)

"""
