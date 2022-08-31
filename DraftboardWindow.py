# !/usr/bin/env python
import pdb
from draftboard_brain import *
from window_helpers import *

SEC1_KEY = '-SECTION1-'
SEC2_KEY = '-SECTION2-'


def Collapsible(layout, key, title='', arrows=(sg.SYMBOL_DOWN, sg.SYMBOL_UP), collapsed=False):
    """
    User Defined Element
    A "collapsable section" element. Like a container element that can be collapsed and brought back
    :param layout:Tuple[List[sg.Element]]: The layout for the section
    :param key:Any: Key used to make this section visible / invisible
    :param title:str: Title to show next to arrow
    :param arrows:Tuple[str, str]: The strings to use to show the section is (Open, Closed).
    :param collapsed:bool: If True, then the section begins in a collapsed state
    :return:sg.Column: Column including the arrows, title and the layout that is pinned
    """
    return sg.Column([[sg.T((arrows[1] if collapsed else arrows[0]), enable_events=True, k=key+'-BUTTON-'),
                       sg.T(title, enable_events=True, key=key+'-TITLE-')],
                      [sg.pin(sg.Column(layout, key=key, visible=not collapsed, metadata=arrows))]], pad=(0,0))


def get(settings, theme):
    """
    Display data in a table format
    """
    sg.popup_quick_message('Hang on for a moment, this will take a bit to create....', auto_close=True,
                           non_blocking=True, font='Default 18')
    if theme:
        sg.theme(theme)
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
    BG_COLORS = {"WR": "DodgerBlue",
                 "QB": "DeepPink",
                 "RB": "LimeGreen",
                 "TE": "coral",
                 "PK": "purple",
                 "DEF": "sienna",
                 ".": "white",
                 "-": "wheat"}
    MAX_ROWS = 17
    MAX_COLS = 12
    BOARD_LENGTH = MAX_ROWS * MAX_COLS
    roster = settings["roster_format"]
    scoring = settings["scoring_format"]
    scoring_settings = settings["scoring_settings"]
    """
    roster = "overall"
    scoring = "ppr"
    """
    leauge_scoring_settings, draft_order, league_found = load_saved_league()
    # draft_order = [f'TEAM {x}' for x in range(13)]
    # scoring_settings = SettingsWindow.get()
    PP = get_player_pool()
    PP = calc_scores(PP, scoring_settings, roster)
    PP.loc[PP["is_keeper"] == True, 'is_drafted'] = True
    drafted_ids = PP.loc[PP["is_drafted"] == True, "sleeper_id"].tolist()
    # Reading the last used League ID to bring in league settings.
    # draft_order used to set the buttons for the board columns/teams.
    # The league info should change if a new league is loaded.

    print('# -------Draftboard Arrays--------#')
    print("ADP Array")
    adp_db = get_db_arr(PP, "adp", roster=roster, scoring=scoring)
    print("ECR Array")
    ecr_db = get_db_arr(PP, "ecr", roster=roster, scoring=scoring)
    print("Empty Draftboard Array")
    db = get_db_arr(PP, "keepers", roster=roster, scoring=scoring)

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
                                   "sleeper_id": db[r, c]["sleeper_id"],
                                   "yahoo_id": db[r, c]["yahoo_id"]}, )
                    for c in range(MAX_COLS)] for r in range(MAX_ROWS)]
    # section1 = col1_layout

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
    bottom_table = get_bottom_table(PP)
    bot_pos_list = ['All', 'QB', 'RB', 'WR', 'TE', 'Flex']
    col3_layout = [[sg.T("View Position: "),
                    sg.DropDown(values=bot_pos_list,
                                default_value=bot_pos_list[0],
                                enable_events=True,
                                key="-BOTTOM-POS-DD-")],
                   [bottom_table]]
    # section2 = col3_layout

    col_bottom = sg.Column(col3_layout, size=(1000, 300))
   
    pane1 = sg.Pane([col_db, col_bottom],
                    orientation="vertical",
                    handle_size=5,
                    expand_x=True,
                    expand_y=True,
                    size=(1250, 900))
    
    col_db_bottom_pane = sg.Column([[pane1]], expand_y=True, expand_x=True)


    pane2 = [sg.Pane([col_db_bottom_pane, col_cheatsheets],
                     orientation="horizontal",
                     handle_size=5,
                     expand_x=True,
                     expand_y=True)]

    options_layout = [[sg.Radio('PPR', "ScoringRadio", default=scoring == "ppr", enable_events=True, k='-R1-'),
                       sg.Radio('Half-PPR', "ScoringRadio", default=scoring == "half_ppr", enable_events=True,
                                k='-R2-'),
                       sg.Radio('Non-PPR', "ScoringRadio", default=scoring == "non_ppr", enable_events=True, k='-R3-'),
                       sg.Checkbox("SuperFlex", default=roster == "superflex", enable_events=True, key="-SUPERFLEX-"),
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
              pane2]

    """
    layout = [[sg.Menu(menu_def)],
              top_bar_layout,
              [Collapsible(section1, SEC1_KEY, 'Section 1', collapsed=False)],
              #### Section 2 part ####
              [Collapsible(section2, SEC2_KEY, 'Section 2', collapsed=False,
                           arrows=(sg.SYMBOL_TITLEBAR_MINIMIZE, sg.SYMBOL_TITLEBAR_MAXIMIZE))],
              ]
    """
    print('# -------Making Windows-------#')
    return sg.Window('Weez Draftboard', layout,
                     return_keyboard_events=True,
                     resizable=True,
                     scaling=1,
                     size=(1600, 900))


"""
# WeezDraftboard()

"""