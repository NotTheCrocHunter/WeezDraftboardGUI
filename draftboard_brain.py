import pdb
import re
import pandas as pd
import requests
from sleeper_wrapper import Players, Drafts, League
from pathlib import Path
import time
import json
import PySimpleGUI as sg
import numpy as np
from datetime import datetime
from scrape_data import merge_dfs, scrape_data  # , merge_dfs, get_player_pool
import SettingsWindow
from KeeperPopUp import *
from window_helpers import *

MAX_ROWS = 17
MAX_COLS = 12

YEAR = datetime.today().strftime('%Y')
TODAY = datetime.today().strftime('%Y-%m-%d')


def get_player_pool():
    start_time = time.time()
    p_pool = scrape_data()

    # ----Clean up columns to be INT values and fill NA ------ #
    cols = ["overall_half_ppr_rank",
            "overall_non_ppr_rank",
            "overall_ppr_rank",
            "superflex_half_ppr_rank",
            "superflex_non_ppr_rank",
            "superflex_ppr_rank"]
    
    p_pool[cols] = p_pool[cols].fillna(value=999).astype(int)
    for col in cols:
        p_pool[col] = pd.to_numeric(p_pool[col], errors="coerce", downcast='integer')
    p_pool['team'] = p_pool['team'].fillna("FA")

    # Now time to add the button_text and cheatsheet_text values
    p_pool["cheatsheet_text"] = p_pool['first_name'].astype(str).str[0] + '. ' + p_pool['last_name'] + ' ' + p_pool[
        'team']
    p_pool["button_text"] = p_pool['first_name'] + '\n' + p_pool['last_name'] + '\n' + p_pool[
        'position'] + ' (' + p_pool['team'] + ') ' + p_pool['bye'].astype(str)

    p_pool.drop_duplicates(subset=['sleeper_id'], keep='first', inplace=True)
    # Sort Keepers
    p_pool = sort_keepers(p_pool)
    end_time = time.time()
    print(f"Time to make Player Draft Pool: {end_time - start_time}")

    return p_pool



def get_cheatsheet_list(df, pos, roster, scoring):
    df = df[df["position"] == pos]  # ['position_tier_ecr', 'cheatsheet_text'].tolist()
    df = df[["position_tier_ecr", 'cheatsheet_text']]
    return df.values.tolist()


def get_db_arr(df, key, roster, scoring):
    if key == "empty":
        arr = np.empty([MAX_ROWS, MAX_COLS])
        arr = np.reshape(arr, (MAX_ROWS, MAX_COLS))
        arr[1::2, :] = arr[1::2, ::-1]
        return arr

    if scoring.lower() in ['standard', 'non-ppr', 'non_ppr']:
        scoring = 'non_ppr'
    elif scoring.lower() in ['half', 'half-ppr', 'half_ppr']:
        scoring = 'half_ppr'
    # else:
    #     scoring = scoring.lower()
    if roster.lower() == 'superflex':
        adp_sort = roster.lower()
    else:
        adp_sort = scoring.lower()

    keys = {"adp": {"sort": f"adp_pick_{adp_sort}", "pick_no": "adp_pick_no"},
            "ecr": {"sort": f"{roster}_{scoring}_rank", "pick_no": 'ecr_pick_no'},
            "keepers": {"sort": "", "pick_no": ""}
            }
    print(f"Array Sorting by key: {key}")
    if key in ["adp", "ecr"]:
        sort = keys[key]['sort']
        pick_no = keys[key]['pick_no']

        non_kept_picks = [n + 1 for n in range(len(df)) if n + 1 not in df['pick_no'].to_list()]
        df[pick_no] = df["pick_no"]
        df.sort_values(by=sort.lower(), ascending=True, inplace=True, na_position="last")
        df.loc[df['is_drafted'] != True, f'{key}_pick_no'] = non_kept_picks
        df.sort_values(by=pick_no, ascending=True, inplace=True)
        arr = np.array(df[:MAX_ROWS * MAX_COLS].to_dict("records"))
        arr = np.reshape(arr, (MAX_ROWS, MAX_COLS))
        arr[1::2, :] = arr[1::2, ::-1]
    elif key == "keepers":
        arr = np.empty([MAX_ROWS, MAX_COLS])
        arr = np.reshape(arr, (MAX_ROWS, MAX_COLS))
        arr[1::2, :] = arr[1::2, ::-1]
        arr = np.full((MAX_ROWS, MAX_COLS), {"button_text": "\n\n", "position": "-", "sleeper_id": "-", "yahoo_id": "-"})
        # Placing keepers on the empty draft board
        keeper_pool = df.loc[df["is_keeper"] == True].to_dict("records")
        for p in keeper_pool:
            loc = (p["round"] - 1, p["draft_slot"] - 1)
            arr[loc] = {"button_text": p["button_text"], "position": p["position"],
                        "sleeper_id": p["sleeper_id"],
                        "yahoo_id": p["yahoo_id"]}
    elif key == "live":
        arr = np.empty([MAX_ROWS, MAX_COLS])
        arr = np.reshape(arr, (MAX_ROWS, MAX_COLS))
        arr[1::2, :] = arr[1::2, ::-1]
        arr = np.full((MAX_ROWS, MAX_COLS), {"button_text": "\n\n", "position": "-", "sleeper_id": "-", "yahoo_id": "-"})
        # Placing keepers on the empty draft board
        drafted_pool = df.loc[df["is_drafted"] == True].to_dict("records")

        for p in drafted_pool:
            try:
                loc = (int(p["round"]) - 1, int(p["draft_slot"]) - 1)
                arr[loc] = {"button_text": p["button_text"],
                            "position": p["position"],
                            "sleeper_id": p["sleeper_id"],
                            "yahoo_id": p["yahoo_id"]}
            except TypeError:
                print("TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'")
    return arr


def DraftIdPopUp():
    sg.PopupScrolled('Select Draft ID')
    pass


def get_draft_order(league):
    """
      Get League and user/map
      """

    user_map = league.map_users_to_team_name()
    """
    Get all picks in sleeper draft
    """
    league_dict = league.get_league()
    draft_id = league_dict["draft_id"]
    # DRAFT_IDs
    # = 859302163317399552  # 850087629952249857  # 858793089177886720  # 855693188285992960  # mock 858792885288538112
    # DRAFT_ID_2022_WEEZ_LEAGUE = 850087629952249857  # 854953046042583040

    """
    get draft order from weez league, map to the user names, and sort by the draft position
    """
    draft = Drafts(draft_id)
    draft_info = draft.get_specific_draft()

    try:
        draft_order = draft_info['draft_order']
        draft_order = {v: user_map[k] for k, v in draft_order.items()}
    except:
        draft_order = [x for x in range(MAX_COLS)]

    return draft_order


#################
# SCORING FUNCS #
#################

def calc_scores(df, scoring_settings, roster):
    start_time = time.time()
    sg.popup_quick_message("Calculating Custom Score")
    df['fpts'] = df.apply(lambda row: get_custom_score_row(row, scoring_settings), axis=1)
    df['fpts'].fillna(0)
    end_time = time.time()
    sg.popup_quick_message(f"Time to Calculate Custom Scores: {end_time-start_time}")
    print(f"Time to calc custom scores: {end_time - start_time}")

    """
    After Calculating the Fantasy Points, we get the VBD
    """
    start_time = time.time()
    df = sort_reset_index(df, sort_by=["fpts"])
    kd_df = df.loc[df['position'].isin(['DEF', 'K', 'PK'])]
    if roster.lower() in ['superflex', '2qb']:
        vols_cutoff = {"QB": 22, "RB": 25, "WR": 25, "TE": 10}
        vorp_cutoff = {"QB": 30, "RB": 55, "WR": 63, "TE": 18}
    else:
        vols_cutoff = {"QB": 12, "RB": 25, "WR": 25, "TE": 10}
        vorp_cutoff = {"QB": 18, "RB": 55, "WR": 63, "TE": 18}

    new_df = pd.DataFrame()
    for pos in ["QB", "RB", "WR", "TE"]:
        temp_df = df.loc[df["position"] == pos]
        vols_threshold = temp_df.iloc[vols_cutoff[pos]]
        vorp_threshold = temp_df.iloc[vorp_cutoff[pos]]

        # TODO Figure out this chained_assignment issue with the error message of:
        #       SettingWithCopyError:
        #       A value is trying to be set on a copy of a slice from a DataFrame.
        #       Try using .loc[row_indexer,col_indexer] = value instead
        pd.options.mode.chained_assignment = None
        temp_df["vols"] = temp_df.apply(lambda row: calc_vols(row, vols_threshold), axis=1)
        temp_df["vorp"] = temp_df.apply(lambda row: calc_vorp(row, vorp_threshold), axis=1)
        temp_df["vbd"] = temp_df.apply(lambda row: calc_vbd(row), axis=1)
        temp_df['vona'] = round(temp_df.fpts.diff(periods=-1))
        temp_df = sort_reset_index(temp_df, sort_by=["vbd", "fpts"])
        temp_df["position_rank_vbd"] = temp_df.index + 1
        new_df = pd.concat([new_df, temp_df], axis=0)

    new_df = pd.concat([new_df, kd_df], axis=0)

    new_df = sort_reset_index(new_df, sort_by=["vbd", "fpts"])
    new_df['vbd_rank'] = new_df.index + 1

    name1 = df["name"].tolist()
    name2 = new_df["name"].tolist()
    names_not_in = list(set(name1) - set(name2))
    print(names_not_in)
    cols_to_fill = ['position_rank_vbd', 'vbd_rank']
    new_df[cols_to_fill] = new_df[cols_to_fill].fillna(999).astype(int)
    end_time = time.time()
    sg.popup_quick_message(f"Time to Calculate Custom Scores: {end_time - start_time}")
    print(f"Time to calc VBD: {end_time - start_time}")

    return new_df


def get_custom_score_row(row, scoring_keys):
    score = 0
    for k, v in scoring_keys.items():
        try:
            score += scoring_keys[k] * row[k]
        except KeyError:
            pass
    return round(score, 2)


def calc_vols(row, vols_threshold):
    return int(max(0, row['fpts'] - vols_threshold['fpts']))


def calc_vorp(row, vorp_threshold):
    return int(max(0, row['fpts'] - vorp_threshold['fpts']))


def calc_vbd(row):
    return int(max(0, row['vols'] + row['vorp']))


def load_saved_league():
    """
    Reading the last used League ID to bring in league settings.
    draft_order used to set the buttons for the board columns/teams.
    The league info should change if a new league is loaded.
    """
    league_id_json = Path('data/league_ids/league_ids.json')
    try:
        with open(league_id_json, "r") as file:
            league_id_list = json.load(file)
            league_id_list = list(set(league_id_list))
            # ----Get Text for Draft Order Buttons (teams) ------#
            league = League(league_id_list[0])
            scoring_settings = league.scoring_settings
            draft_order = get_draft_order(league)
            league_found = True
    except FileNotFoundError:
        sg.popup_quick_message("League not found.")
        league_found = False
        Path('data/league_ids').mkdir(parents=True, exist_ok=True)
        scoring_settings = SettingsWindow.create(silent_mode=True)
        draft_order = [x for x in range(MAX_COLS + 1)]

    return scoring_settings, draft_order, league_found


def sort_reset_index(df, sort_by):
    """
    This gets called every time we add vbd to sort by vbd and reset the index
    """
    df.sort_values(by=sort_by, ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
