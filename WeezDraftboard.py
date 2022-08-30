# !/usr/bin/env python
import pdb
from draftboard_brain import *
from KeeperPopUp import KeeperPopUp
from LeaguePopUp import LeaguePopUp
from ViewPlayerPool import ViewPlayerPool
import SettingsWindow
from window_helpers import *
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa


def get():
    """
    Display data in a table format
    """
    sg.popup_quick_message('Hang on for a moment, this will take a bit to create....', auto_close=True,
                           non_blocking=True, font='Default 18')
    sg.theme()
    sg.set_options(element_padding=(1, 1))
    sg.set_options(font=("Calibri", 12, "normal"))
    # --- GUI Definitions ------- #
    menu_def = [['File', ['Open', 'Save', 'Exit']],
                ['Live Draft', ['Connect to Sleeper Draft', 'Connect to Yahoo Draft', 'Disconnect']],
                ['Settings', ['Scoring Settings']],
                ['League', ['Select League']],
                ['ADP', ['2QB', 'PPR', 'Half-PPR', 'Non-PPR']],
                ['Player Pool', ['View Player Pool']],
                ['Keepers', ['Set Keepers', 'Clear All Keepers']],
                ['Theme', ['Change Theme']],
                ['Edit', ['Refresh', 'Edit Me', 'Paste', ['Special', 'Normal', ], 'Undo'], ],
                ['Help', 'About...'], ]

    RELIEF_ = "flat"  # "groove" "raised" "sunken" "solid" "ridge"
    BG_COLORS = {"WR": "white on DodgerBlue",
                 "QB": "white on DeepPink",
                 "RB": "white on LimeGreen",
                 "TE": "white on coral",
                 "PK": "white on purple",
                 "DEF": "white on sienna",
                 ".": "white",
                 "-": "wheat"}

    MAX_ROWS = 17
    MAX_COLS = 12
    BOARD_LENGTH = MAX_ROWS * MAX_COLS
    roster = "superflex"
    scoring = "ppr"

    scoring_settings, draft_order, league_found = load_saved_league()
    # draft_order = [f'TEAM {x}' for x in range(13)]
    # scoring_settings = SettingsWindow.get()
    PP = get_player_pool()
    PP = calc_scores(PP, scoring_settings, roster)

    # Reading the last used League ID to bring in league settings.
    # draft_order used to set the buttons for the board columns/teams.
    # The league info should change if a new league is loaded.

    print('# -------Draftboard Arrays--------#')
    print("ADP Array")
    adp_db = get_db_arr(PP, "adp", roster=roster, scoring=scoring)
    print("ECR Array")
    ecr_db = get_db_arr(PP, "ecr", roster=roster, scoring=scoring)
    print("Empty Draftboard Array")
    db = get_db_arr(PP, "keepers")

    """
    # Column and Tab Layouts
    """
    print('# -------Making Columns and Tab Layouts--------#')
    # noinspection PyTypeChecker
    col1_layout = [[sg.T("", size=(3, 1), justification='left')] +
                   [sg.B(button_text=draft_order[c + 1],
                         auto_size_button=True,
                         expand_x=True,
                         expand_y=True,
                         border_width=0, p=(1, 1),
                         key=f"TEAM{c}",
                         size=(11, 0))
                    for c in range(MAX_COLS)]] + \
                  [[sg.T(f"R{str(r + 1)}", size=(3, 1), justification='left')] +
                   [sg.B(button_text=f"{db[r, c]['button_text']}",
                         enable_events=True,
                         size=(11, 0),
                         p=(1, 1),
                         border_width=0,
                         button_color=BG_COLORS[db[r, c]["position"]],
                         mouseover_colors="gray",
                         disabled=False,
                         disabled_button_color="white on gray",
                         highlight_colors=("black", "white"),
                         auto_size_button=True,
                         expand_x=True,
                         expand_y=True,
                         key=(r, c),
                         metadata={"is_clicked": False,  # False,  # Leave this off by default #
                                   "button_color": BG_COLORS[db[r, c]["position"]],
                                   "sleeper_id": "-"}, )
                    for c in range(MAX_COLS)] for r in range(MAX_ROWS)]

    col_db = sg.Column([[sg.Column(col1_layout,
                                   scrollable=True,
                                   vertical_alignment="bottom",
                                   size=(1000, 600),
                                   justification="left",
                                   vertical_scroll_only=False,
                                   element_justification="left",
                                   sbar_width=2,
                                   expand_y=True,
                                   expand_x=True,
                                   pad=1)]],
                       expand_x=True,
                       expand_y=True)
    col2_layout = [[sg.T("Cheat Sheets")],
                   [get_cheatsheet_table(PP, roster=roster, scoring=scoring, pos="QB", hide_drafted=False)],
                   [get_cheatsheet_table(PP, roster=roster, scoring=scoring, pos="RB", hide_drafted=False)],
                   [get_cheatsheet_table(PP, roster=roster, scoring=scoring, pos="WR", hide_drafted=False)],
                   [get_cheatsheet_table(PP, roster=roster, scoring=scoring, pos="TE", hide_drafted=False)],
                   ]
    col_cheatsheets = sg.Column(col2_layout, scrollable=False, grab=True, pad=(1, 1), size=(600, 900))
    table = get_bottom_table(PP)
    bot_pos_list = ['All', 'QB', 'RB', 'WR', 'TE', 'Flex']
    col3_layout = [[sg.T("View Position: "),
                    sg.DropDown(values=bot_pos_list,
                                default_value=bot_pos_list[0],
                                enable_events=True,
                                key="-BOTTOM-POS-DD-")],
                   [table]]

    col_bottom = sg.Column(col3_layout, size=(1000, 300))

    pane1 = sg.Pane([col_db, col_bottom],
                    orientation="vertical",
                    handle_size=5,
                    expand_x=True,
                    expand_y=True,
                    size=(1250, 900))

    col4 = sg.Column([[pane1]], expand_y=True, expand_x=True)

    pane2 = [sg.Pane([col4, col_cheatsheets],
                     orientation="horizontal",
                     handle_size=5,
                     expand_x=True,
                     expand_y=True)]

    options_layout = [[sg.Radio('PPR', "ScoringRadio", default=True, enable_events=True, k='-R1-'),
                       sg.Radio('Half-PPR', "ScoringRadio", default=False, enable_events=True, k='-R2-'),
                       sg.Radio('Non-PPR', "ScoringRadio", default=False, enable_events=True, k='-R3-'),
                       sg.Checkbox("SuperFlex", default=True, enable_events=True, key="-SUPERFLEX-"),
                       sg.Push(),
                       sg.VerticalSeparator(),
                       sg.Push(),
                       sg.Checkbox("Hide Drafted Players", enable_events=True, key="-HIDE-DRAFTED-")]]
    top_bar_layout = [sg.Text('Weez Draftboard', font='Any 18'),
                      sg.Push(),
                      sg.VerticalSeparator(),
                      sg.Push(),
                      sg.Button('Load ECR', border_width=0, key="-LOAD-ECR-"),
                      sg.Button('Load ADP', border_width=0, key="-LOAD-ADP-"),
                      sg.Button('Load Draftboard', border_width=0, key="-LOAD-DB-"),
                      sg.Push(),
                      sg.VerticalSeparator(),
                      sg.Push(),
                      sg.Frame("Options", layout=options_layout),
                      sg.Push(),
                      sg.VerticalSeparator(),
                      sg.Push(),
                      sg.Button(f'Refresh', key="-Refresh-"),
                      # sg.Button('Connect to Draft', border_width=0, key="-CONNECT-TO-LIVE-DRAFT-"),
                      sg.Text(f'Scoring: {scoring.upper()}. Status: OFFLINE', key="-STATUS-"),
                      sg.Push(),
                      sg.VerticalSeparator(),
                      sg.Push(),
                      sg.Text('Search: '),
                      sg.Input(key='-Search-', size=15, enable_events=True, focus=True, tooltip="Find Player"),
                      ]
    layout = [[sg.Menu(menu_def)],
              top_bar_layout,
              pane2,
              ]
    print('# -------Making Windows-------#')
    return sg.Window('Weez Draftboard', layout,
                     return_keyboard_events=True, resizable=True, scaling=1, size=(1600, 900))


"""
# WeezDraftboard()


      
        elif event == 'Open':
            filename = sg.popup_get_file(
                'filename to open', no_window=True, file_types=(("CSV Files", "*.csv"),))
            # --- populate table with file contents --- #
            if filename is not None:
                with open(filename, "r") as infile:
                    reader = csv.reader(infile)
                    try:
                        # read everything else into a list of rows
                        data = list(reader)
                    except:
                        sg.popup_error('Error reading file')
                        continue
                # clear the table
                [window[(i, j)].update('') for j in range(MAX_COLS)
                 for i in range(MAX_ROWS)]

                for i, row in enumerate(data):
                    for j, item in enumerate(row):
                        location = (i, j)
                        try:  # try the best we can at reading and filling the table
                            target_element = window[location]
                            new_value = item
                            if target_element is not None and new_value != '':
                                target_element.update(new_value)
                        except:
                            pass
        
        
"""
