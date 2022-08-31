# from draftboard_brain import get_bottom_table, get_cheatsheet_data
import PySimpleGUI as sg


def update_all_tables(PP, window, roster_format, scoring_format):
    hide_d = window["-HIDE-DRAFTED-"].get()

    for cheat_sheet_pos in ["QB", "WR", "TE", "RB"]:  # "ALL",
        cheatsheet_data = get_cheatsheet_data(PP, roster=roster_format, scoring=scoring_format,
                                              table_pos=cheat_sheet_pos, hide_drafted=hide_d)
        window[f"-{cheat_sheet_pos}-TABLE-"].update(values=cheatsheet_data)
    # ----- Update the Bottom Table Data ----- #
    bottom_position = window['-BOTTOM-POS-DD-'].get()
    bottom_data = get_bottom_table(PP, pos=bottom_position.lower(), hide_drafted=hide_d, data_only=True)
    window['-BOTTOM-TABLE-'].update(values=bottom_data)


def update_buttons(window, MAX_COLS, MAX_ROWS, BG_COLORS, db_arr):
    for c in range(MAX_COLS):
        for r in range(MAX_ROWS):
            try:
                window[(r, c)].update(button_color=BG_COLORS[db_arr[r, c]["position"]],
                                      text=db_arr[r, c]['button_text'], )
                window[(r, c)].metadata["button_color"] = BG_COLORS[db_arr[r, c]["position"]]
                window[(r, c)].metadata["sleeper_id"] = db_arr[r, c]["sleeper_id"]
                window[(r, c)].metadata["yahoo_id"] = db_arr[r, c]["yahoo_id"]
            except KeyError:
                print(f"Error on {db_arr[r, c]}")


# ---- Update Window Functions ---- #
def get_cheatsheet_data(df, roster, scoring, table_pos="all", hide_drafted=False):
    """
    Cheat Sheet Data for the rows of the tables building
    """
    table_pos = table_pos.upper()  # Make pos var CAPS to align with values "QB, RB, WR TE" and sg element naming format
    # ------ Remove Kickers and Defenses ------- #
    df = df.loc[df["position"].isin(["QB", "RB", "WR", "TE"])]

    if hide_drafted:
        df = df.loc[df["is_keeper"].isin([False, None]), :]
        df = df.loc[df["is_drafted"].isin([False, None]), :]
    else:
        pass

    if table_pos == "ALL":
        df = df.sort_values(by=[f'{roster}_{scoring}_rank'], ascending=True, na_position='last')  # Format is overall or superflex
        cols = ['sleeper_id', 'superflex_tier_ecr', 'cheatsheet_text']
    elif table_pos == "BOTTOM":
        df = df.sort_values(by=["vbd_rank"], ascending=True, na_position="last")
        cols = ['name', 'fpts', 'vbd_rank', 'position_rank_vbd', 'vbd', 'vorp', 'vols', 'vona',
                'pass_att', 'pass_cmp', 'pass_yd', 'pass_td',
                'rec', 'rec_td', 'rec_yd',
                'rush_att', 'rush_yd', 'rush_td',
                'pass_int', 'fum_lost',
                'bonus_rec_te',
                'sleeper_id']
    else:
        df = df.loc[df.position == table_pos]
        if scoring.lower() in ['half', 'half-ppr', 'half_ppr']:
            scoring = 'half_ppr'
        elif scoring.lower() in ['non-ppr', 'non_ppr', 'standard']:
            scoring = 'non_ppr'
        cols = ['sleeper_id', f'chen_tier_{scoring.lower()}', 'cheatsheet_text', 'vbd']
        df = df.sort_values(by=[f"chen_pos_rank_{scoring.lower()}", "adp_pick_no"], ascending=[True, True], na_position="last")

    df = df[cols]
    df = df.fillna(value="999")
    table_data = df.values.tolist()
    return table_data


def get_cheatsheet_table(df, roster, scoring, pos="all", hide_drafted=False):
    table_data = get_cheatsheet_data(df, roster, scoring, pos, hide_drafted)
    table = sg.Table(table_data, headings=['sleeper_id', 'Tier', pos, 'vbd'],
                     col_widths=[0, 4, 15, 4],
                     visible_column_map=[False, True, True, False],
                     auto_size_columns=False,
                     max_col_width=20,
                     sbar_width=2,
                     display_row_numbers=False,
                     num_rows=min(10, len(table_data)), row_height=15, justification="left",
                     key=f"-{pos}-TABLE-", expand_x=False, expand_y=True, visible=True)
    return table


def get_bottom_table(df, pos='all', hide_drafted=False, data_only=False):
    if hide_drafted:
        df = df.loc[df["is_keeper"].isin([False, None]), :]
        df = df.loc[df["is_drafted"].isin([False, None]), :]
    else:
        pass

    if pos.lower() == 'all':
        pass
    elif pos.lower() == 'flex':
        df = df.loc[df['position'].isin(['RB', 'WR', 'TE'])]
    else:
        df = df.loc[df['position'] == pos.upper()]

    df = df.sort_values(by=["vbd_rank"], ascending=True, na_position="last")

    cols = ['name', 'fpts', 'vbd_rank', 'position_rank_vbd', 'vbd', 'vorp', 'vols', 'vona',
            'pass_att', 'pass_cmp', 'pass_yd', 'pass_td',
            'rec', 'rec_td', 'rec_yd',
            'rush_att', 'rush_yd', 'rush_td',
            'pass_int', 'fum_lost',
            'bonus_rec_te',
            'sleeper_id']
    vis_col = [True for item in cols]
    vis_col[-1] = False
    df = df[cols]
    fillna_vals = {col: 0 for col in cols if col not in ['sleeper_id', 'name']}
    df = df.fillna(fillna_vals)
    table_data = df.values.tolist()

    headings_list = ['name', 'fpts', 'vbd rank', 'vbd pos rank', 'vbd', 'vorp', 'vols', 'vona',
                     'pass_att', 'pass_cmp', 'pass_yd', 'pass_td',
                     'rec', 'rec_td', 'rec_yd',
                     'rush_att', 'rush_yd', 'rush_td',
                     'pass_int', 'fum_lost',
                     'bonus_rec_te',
                     'sleeper_id']
    table = sg.Table(table_data, headings=headings_list,
                     # col_widths=[0, 3, 20],
                     visible_column_map=vis_col,
                     auto_size_columns=False,
                     max_col_width=20,
                     sbar_width=2,
                     display_row_numbers=False,
                     vertical_scroll_only=False,
                     num_rows=min(50, len(table_data)), row_height=15, justification="left",
                     key=f"-BOTTOM-TABLE-", expand_x=False, expand_y=False, visible=True)
    if data_only:
        return table_data
    else:
        return table



