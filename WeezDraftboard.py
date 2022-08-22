# !/usr/bin/env python
import pdb
from draftboard_brain import *
from KeeperPopUp import KeeperPopUp
from LeaguePopUp import LeaguePopUp
from ViewPlayerPool import ViewPlayerPool
from window_helpers import update_all_tables, update_buttons


def WeezDraftboard():
    """
    Display data in a table format
    """
    sg.popup_quick_message('Hang on for a moment, this will take a bit to create....', auto_close=True,
                           non_blocking=True, font='Default 18')

    sg.set_options(element_padding=(1, 1))
    sg.set_options(font=("Calibri", 10, "normal"))
    # --- GUI Definitions ------- #
    menu_def = [['File', ['Open', 'Save', 'Exit']],
                ['Draft ID', ['Select Draft ID']],
                ['League', ['Select League']],
                ['ADP', ['2QB', 'PPR', 'Half-PPR', 'Standard']],
                ['Player Pool', ['View Player Pool', 'View Projections', 'View Rank Differences']],
                ['Keepers', ['Set Keepers', 'Clear All Keepers']],
                ['Edit', ['Edit Me', 'Paste', ['Special', 'Normal', ], 'Undo'], ],
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
    PP, draft_order, league_found = get_player_pool('2qb')

    """
    Reading the last used League ID to bring in league settings. 
    draft_order used to set the buttons for the board columns/teams.
    The league info should change if a new league is loaded. 
    """

    # -------Draftboard Arrays--------#
    adp_db = get_db_arr(PP, "adp")
    ecr_db = get_db_arr(PP, "ecr")
    db = get_db_arr(PP, "keepers")

    """
    Column and Tab Layouts
    """
    # noinspection PyTypeChecker
    col1_layout = [[sg.T("", size=(3, 1), justification='left')] +
                   [sg.B(button_text=draft_order[c + 1],
                         auto_size_button=True,
                         expand_x=True,
                         expand_y=True,
                         border_width=0, p=(1, 1),
                         key=f"TEAM{c}",
                         size=(13, 0))
                    for c in range(MAX_COLS)]] + \
                  [[sg.T(f"R{str(r + 1)}", size=(3, 1), justification='left')] +
                   [sg.B(button_text=f"{db[r, c]['button_text']}",
                         enable_events=True,
                         size=(13, 0),
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
                                   "sleeper_id": "-",
                                   },
                         )
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
                   [get_cheatsheet_table(PP, pos="QB", hide_drafted=False)],
                   [get_cheatsheet_table(PP, pos="RB", hide_drafted=False)],
                   [get_cheatsheet_table(PP, pos="WR", hide_drafted=False)],
                   [get_cheatsheet_table(PP, pos="TE", hide_drafted=False)],
                   ]
    col_cheatsheets = sg.Column(col2_layout, scrollable=False, grab=True, pad=(1, 1), size=(600, 900))
    table = get_bottom_table(PP)
    bot_pos_list = ['SuperFlex', 'QB', 'RB', 'WR', 'TE', 'Flex']
    col3_layout = [[sg.T("View Position: "), sg.DropDown(values=bot_pos_list,
                                            default_value=bot_pos_list[0],
                                            enable_events=True,
                                            key="-BOTTOM-POS-DD-")],
                   [table]]
    col_bottom = sg.Column(col3_layout, size=(1000, 300))
    # wrapping col_db in another column before the pane for scrolling
    # col1_1 = sg.Column([[col_db]], expand_x=True, expand_y=True)
    pane1 = sg.Pane([col_db, col_bottom],
                    orientation="vertical",
                    handle_size=5,
                    expand_x=True,
                    expand_y=True,
                    size=(1269, 900))

    col4 = sg.Column([[pane1]], expand_y=True, expand_x=True)

    pane2 = sg.Pane([col4, col_cheatsheets],
                    orientation="horizontal",
                    handle_size=5,
                    expand_x=True,
                    expand_y=True)

    """  
    pane1 = sg.Pane([col_db, col_cheatsheets],
                    orientation="horizontal",
                    handle_size=5,
                    expand_x=True,
                    expand_y=True)
    """

    """
    pane2 = sg.Pane([col4, col_bottom],
                    orientation="vertical",
                    handle_size=5,
                    expand_x=True,
                    expand_y=True)"""
    layout = [[sg.Menu(menu_def)],
              [sg.Text('Weez Draftboard', font='Any 18'),
               sg.Button('Load ECR', key="-LOAD-ECR-"),
               sg.Button('Load ADP', key="-LOAD-ADP-"),
               sg.Button('Load Draftboard', key="-LOAD-DB-"),
               sg.Button('Refresh', key="-Refresh-"),
               sg.Button('Connect to Draft', key="-CONNECT-TO-LIVE-DRAFT-"),
               sg.Text('Status: OFFLINE', key="-STATUS-"),
               sg.Push(),
               sg.Text('Search: '),
               sg.Input(key='-Search-', enable_events=True, focus=True, tooltip="Find Player"),
               sg.Checkbox("Hide Drafted Players", enable_events=True, key="-HIDE-DRAFTED-")],
              [pane2],
              ]

    window = sg.Window('Weez Draftboard',
                       layout,
                       return_keyboard_events=True,
                       resizable=True,
                       scaling=1,
                       size=(1600, 900)
                       # right_click_menu_tearoff=1
                       )
    """
    WHILE LOOP
    create and turn live_draft off
    """
    live_draft = False
    # This is for the DB array/view.  This should turn off when loading the ADP/ECR boards.
    # If both live_board and live_draft, refresh will update the live board
    live_board = True
    while True:
        event, values = window.read(timeout=1000)
        # --- Break While Loop --- #
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        # ---- Refresh Window Event ---- #
        elif event in ("-Refresh-", sg.TIMEOUT_KEY):
            """
            if we have a successful connection to a live draft:
                Update the status window text
                get all of the picks and drafted IDs from the sleeper_wrapper draft class
                Set those drafted IDs to True in the dataframe
                For loop to update the PP dataframe on the sleeper_ids for draft position info
                After updating PP, recreate the db_array with new picks
                If live_board (main db view), the picks will update on screen, by calling the LOAD-DB button
            Type error to handle a disconnect of the draft. 
            """
            if not live_draft:
                drafted_ids = PP.loc[PP["is_keeper"] == True, "sleeper_id"].tolist()
                window["-STATUS-"].update(value="Status: OFFLINE")
            else:
                try:
                    window["-STATUS-"].update(value="Status: Connected")
                    all_picks = draft.get_all_picks()
                    drafted_ids = [x['player_id'] for x in all_picks]
                    PP.loc[PP['sleeper_id'].isin(drafted_ids), "is_drafted"] = True
                    for pick in all_picks:
                        PP.loc[PP['sleeper_id'] == pick['player_id'], ["round", "draft_slot", "pick_no"]] = [
                            pick["round"], pick["draft_slot"], pick["pick_no"]]
                    db = get_db_arr(PP, "live")
                    # ---- set the drafted_ids as True ---- #
                    PP.loc[PP["sleeper_id"].isin(drafted_ids), "is_drafted"] = True
                    # ---- Update the Cheat Sheets and Bottom Tables ----- #
                    update_all_tables(PP, window)

                except TypeError:
                    live_draft = False
                    sg.popup_quick_message("Connection to Draft Lost")
                finally:
                    # update_buttons(window, MAX_COLS, MAX_ROWS, BG_COLORS, db_arr=db)
                    if live_board:
                        window["-LOAD-DB-"].click()
                # ----- UPDATE BUTTONS - for loop to set the drafted players as "clicked" ---- #
                for col in range(MAX_COLS):
                    for row in range(MAX_ROWS):
                        cur_id = window[(row, col)].metadata['sleeper_id']
                        if cur_id in drafted_ids:
                            window[(row, col)].metadata["is_clicked"] = True
                            window[(row, col)].update(button_color='white on gray')
                        else:
                            pass
        elif event in ['2QB', 'PPR', 'Half-PPR', 'STD']:
            PP, draft_order, league_found = get_player_pool(scoring_type=event.lower())
            adp_db = get_db_arr(PP, "adp")
            ecr_db = get_db_arr(PP, "ecr")
            # TODO Map out the ecr_db to not sort by superflex
            #   Make calls for half-ppr and standard rankings as well.
            window["-LOAD-ADP-"].click()
        elif event == 'Select League':
            league = LeaguePopUp()
            if league:
                draft_order = get_draft_order(league)
                for c in range(MAX_COLS):
                    window[f"TEAM{c}"].update(text=f"{draft_order[c + 1]}")
                sg.popup_quick_message("Calculating Custom Score")
                PP['fpts'] = PP.apply(lambda row: get_custom_score_row(row, league.scoring_settings), axis=1)
                PP = add_vbd(PP)
            else:
                pass
        elif event == "-HIDE-DRAFTED-":
            update_all_tables(PP, window)
            # --- After updating the tables, if the draft is not live, then update those to gray as "hidden" --- #
            if live_draft:
                drafted_ids = PP.loc[PP["is_drafted"] == True, "sleeper_id"].tolist()
            else:
                drafted_ids = PP.loc[PP["is_keeper"] == True, "sleeper_id"].tolist()
            for col in range(MAX_COLS):
                for row in range(MAX_ROWS):
                    cur_id = window[(row, col)].metadata['sleeper_id']
                    if cur_id in drafted_ids:
                        window[(row, col)].metadata["is_clicked"] = True
                        window[(row, col)].update(button_color='white on gray')

        # Select position dropdown in bottom table
        elif event == '-BOTTOM-POS-DD-':
            update_all_tables(PP, window)

        # click on button event
        elif event in [(r, c) for c in range(MAX_COLS) for r in range(MAX_ROWS)]:
            r, c = event
            s_id = window[(r, c)].metadata["sleeper_id"]
            print(f"Current ID: {s_id}")
            window[(r, c)].metadata["is_clicked"] = not window[(r, c)].metadata["is_clicked"]
            if window[(r, c)].metadata["is_clicked"]:
                window[(r, c)].update(button_color='white on gray')
                PP.loc[PP["sleeper_id"] == s_id, "is_drafted"] = True
            else:
                button_reset_color = window[(r, c)].metadata['button_color']
                window[(r, c)].update(button_color=button_reset_color)
                PP.loc[PP["sleeper_id"] == s_id, "is_drafted"] = False
            # --- Update the Cheatsheets and Bottom Table (Note: these will also update automatically on refresh) --- #
            update_all_tables(PP, window)
        elif event == "-CONNECT-TO-LIVE-DRAFT-":
            """
            Get Draft ID
            Validate Draft ID 
            Create Draft Object
            Update PP for is_drafted
            Remake Draftboard array
            Place "is_drafted" players on empty DB 
            Turn live_draft on 
            drafted_ids = [x['player_id'] for x in all_picks]
            """
            # TODO: Figure out how to avoid HTTPError when the sleeper draft ID is not filled out.
            draft_id = sg.PopupGetText("Enter the Sleeper Draft ID.")
            print(draft_id)
            if not draft_id:
                sg.PopupQuick("No ID Entered")
                live_draft = False
                pass
            else:
                draft = Drafts(draft_id)  # create draft object
                all_picks = draft.get_all_picks()
                try:
                    # update the PP dataframe
                    PP["pick_no"] = None
                    PP["adp_pick_no"] = None
                    PP["ecr_pick_no"] = None
                    for pick in all_picks:
                        r = pick['round']
                        c = pick['draft_slot']
                        p_no = pick['pick_no']
                        sleeper_id = pick['player_id']  # 2449
                        PP.loc[PP["sleeper_id"] == sleeper_id, ['is_drafted', 'pick_no', 'draft_slot', 'round', ]] = [
                            True, p_no, c, r]
                    db = get_db_arr(PP, "live")
                    adp_db = get_db_arr(PP, "adp", df_loc_col="is_drafted")
                    ecr_db = get_db_arr(PP, "ecr", df_loc_col="is_drafted")
                    live_draft = True  # turn live draft on
                except TypeError:
                    sg.popup_quick_message("Error Connecting to Draft")
                    live_draft = False
        elif event == '-Search-':
            search_text = values["-Search-"].lower()
            for c in range(MAX_COLS):
                for r in range(MAX_ROWS):
                    if search_text == "":
                        if window[(r, c)].metadata["is_clicked"]:
                            window[(r, c)].update(button_color='white on gray')
                        else:
                            window[(r, c)].update(button_color=window[(r, c)].metadata["button_color"])
                    elif search_text in window[(r, c)].get_text().lower():
                        window[(r, c)].update(button_color="black on yellow")
                    else:
                        if window[(r, c)].metadata["is_clicked"]:
                            window[(r, c)].update(button_color='white on gray')
                        else:
                            window[(r, c)].update(button_color=window[(r, c)].metadata["button_color"])
        elif event == '-Drafted-':
            search_text = values["-Drafted-"].lower()
            for player in drafted_list:
                for c in range(MAX_COLS):
                    for r in range(MAX_ROWS):
                        if player in window[(r, c)].get_text().lower():
                            window[(r, c)].update(button_color="gray")
                        else:
                            print("Line 349 - update button color")
                            pdb.set_trace()

                        button_reset_color = f"white on {BG_COLORS[db[r, c]['position']]}"
                        if search_text == "":
                            window[(r, c)].update(button_color=button_reset_color)
                        elif search_text in window[(r, c)].get_text().lower():
                            window[(r, c)].update(button_color="gray")
                        else:
                            window[(r, c)].update(button_color=button_reset_color)
        elif event == "-LOAD-ADP-":
            live_board = False
            update_buttons(window, MAX_COLS, MAX_ROWS, BG_COLORS, db_arr=adp_db)
        elif event == "-LOAD-ECR-":
            live_board = False
            update_buttons(window, MAX_COLS, MAX_ROWS, BG_COLORS, db_arr=ecr_db)
        elif event == "-LOAD-DB-":
            live_board = True
            for col in range(MAX_COLS):
                for row in range(MAX_ROWS):
                    window[(row, col)].update(button_color=BG_COLORS[db[row, col]["position"]],
                                              text=db[row, col]['button_text'])
                    window[(row, col)].metadata["button_color"] = BG_COLORS[db[row, col]["position"]]
                    window[(row, col)].metadata["sleeper_id"] = db[row, col]["sleeper_id"]
        elif event == "View Player Pool":
            ViewPlayerPool(PP)
        elif event == 'About...':
            sg.popup('Demo of table capabilities')
        elif event == 'Set Keepers':
            PP = KeeperPopUp(PP)
            # Refresh Arrays after Keeper Pop Up
            adp_db = get_db_arr(PP, "adp")
            ecr_db = get_db_arr(PP, "ecr")
            db = get_db_arr(PP, "keepers")

            # Placing keepers on the empty draft board
            keeper_pool = PP.loc[PP["is_keeper"] == True].to_dict("records")
            for p in keeper_pool:
                loc = (p["round"] - 1, p["draft_slot"] - 1)
                db[loc] = {"button_text": p["button_text"],
                           "position": p["position"],
                           "sleeper_id": p["sleeper_id"]}
            window["-LOAD-DB-"].click()
        elif event == 'Clear All Keepers':
            sg.popup('Clear All Keepers')
        elif event == 'Select Draft ID':
            sg.PopupScrolled('Select Draft ID')
            """
              Now create draft for the mock draft we are using
              """
            draft = Drafts()
            live_draft = True

            if live_draft:
                drafted_list = draft.get_all_picks()
            else:
                drafted_list = PP.loc[PP["is_keeper"] == True, 'sleeper_id'].to_list()

    window.close()


# WeezDraftboard()

"""
      
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
