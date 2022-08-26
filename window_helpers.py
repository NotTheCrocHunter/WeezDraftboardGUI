from draftboard_brain import get_bottom_table, get_cheatsheet_data


# ---- Update Window Functions ---- #
def update_all_tables(PP, window, roster, scoring):
    hide_d = window["-HIDE-DRAFTED-"].get()
    for cheat_sheet_pos in ["QB", "WR", "TE", "RB"]:  # "ALL",
        cheatsheet_data = get_cheatsheet_data(PP, roster=roster, scoring=scoring, table_pos=cheat_sheet_pos, hide_drafted=hide_d)
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
            except KeyError:
                print(f"Error on {db_arr[r, c]}")

