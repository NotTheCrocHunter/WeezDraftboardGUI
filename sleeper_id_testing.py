from sleeper_wrapper import Players
import re
import pandas as pd
from scrape_fantasy_pros import scrape_fantasy_pros
from scrape_ffcalc_adp import get_adp_df
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pdb
import difflib
from sleeper_ids import get_sleeper_ids


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


def merge_dfs(df1, df2, col_to_match, how="left"):
    cols_to_use = df2.columns.difference(df1.columns).to_list()
    cols_to_use.append(col_to_match)
    df = pd.merge(df1, df2[cols_to_use], how=how, on=col_to_match)
    return df


players = Players()

ply = players.get_players_df()


ply_qb = ply.loc[ply["position"] == "QB"]
ply_rb = ply.loc[ply["position"] == "RB"]
ply_wr = ply.loc[ply["position"] == "WR"]
ply_te = ply.loc[ply["position"] == "TE"]

adp = get_adp_df()

adp['search_name'] = adp['name'].str.replace(r'[\W\s]+', '').str.lower()   # adp['name'].str.replace(" ", "").str.lower().replace(r'[^\W\s]+', '').str.replace('.', '')


adp_qb = adp.loc[adp["position"] == "QB"]
adp_rb = adp.loc[adp["position"] == "RB"]
adp_wr = adp.loc[adp["position"] == "WR"]
adp_te = adp.loc[adp["position"] == "TE"]

adp2 = pd.concat([get_sleeper_ids(adp.loc[adp["position"] == x], ply.loc[ply["position"] == x]) for x in ['QB', 'RB', 'WR', 'TE']])
adp = get_sleeper_ids(adp, ply)



f = scrape_fantasy_pros()
f['key'] = f['name_pos'].str.replace(" ", "").str.lower()
# p['key'] = p['name_team_pos'].str.replace(" ", "").str.lower()
p.loc[p['team'].isna() == True] = '_'
p['key'] = p['search_full_name'] + p['position']
p['key'] = p['key'].str.replace(" ", "").str.lower()
p['sleeper_id'] = p['player_id']

qf = f.loc[f['position'] == 'RB']
qa = a.loc[a['position'] == 'RB']
qp = p.loc[p['position'] == 'RB']

df1 = qf
df2 = qp
df1.set_index('key', drop=True, inplace=True)
df2.set_index('key', drop=True, inplace=True)


df2['key'] = df2['key'].apply(lambda x: difflib.get_close_matches(x, df1['key'])[0])
df1.merge(df2)
print(df1)
# n = df.index.map(lambda x: difflib)
# n.index = df2.index.map(lambda x: difflib.get_close_matches(x, df.index)[0])
# df.join(mf)
# qf = fuzzy_merge(qf, qp, 'key', 'key', threshold=90, limit=1)
# qp = fuzzy_merge(qp, qf, 'key', 'key', threshold=90, limit=1)
# qpf = fuzzy_merge(p, qf, 'key', 'key', threshold=90, limit=2)

# qa1 = fuzzy_merge(qa, p, 'key', 'key', threshold=90, limit=2)
# qpa = fuzzy_merge(p, qa, 'key', 'key', threshold=90, limit=2)
# n3 = merge_dfs(qf, qp, 'matches', how="left")



# df = pd.merge(qf, qp, how='inner', left_on='matches', right_on='key')
print("hi")
