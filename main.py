import DraftboardWindow
from DraftboardWindow import SEC1_KEY, SEC2_KEY
import pdb
from draftboard_brain import *
from KeeperPopUp import KeeperPopUp
from LeaguePopUp import LeaguePopUp, PopUpDropDown
from ViewPlayerPool import ViewPlayerPool
import SettingsWindow
from window_helpers import *
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
import os


if __name__ == '__main__':
    RELIEF_ = "flat"  # "groove" "raised" "sunken" "solid" "ridge"
    BG_COLORS = {"WR": "white on DodgerBlue",
                 "QB": "white on DeepPink",
                 "RB": "white on LimeGreen",
                 "TE": "white on coral",
                 "PK": "white on purple",
                 "DEF": "white on sienna",
                 ".": "white",
                 "-": "wheat"}
    SETTINGS_PATH = Path('data/settings.json')
    MAX_ROWS = 17
    MAX_COLS = 12
    BOARD_LENGTH = MAX_ROWS * MAX_COLS
    CONSUMER_KEY = os.getenv('YAHOO_CONSUMER_KEY')
    CONSUMER_SECRET = os.getenv('YAHOO_CONSUMER_SECRET')
    OAUTH = OAuth2(None, None, from_file='data/yahoo/oauth2.json')

    with open(SETTINGS_PATH, "r") as file:
        settings = json.load(file)
    roster_format = settings["roster_format"]
    scoring_format = settings["scoring_format"]
    scoring_settings = settings["scoring_settings"]
    """
    Reading the last used League ID to bring in league settings. 
    draft_order used to set the buttons for the board columns/teams.
    The league info should change if a new league is loaded. 
    """
    leauge_scoring_settings, draft_order, league_found = load_saved_league()
    # draft_order = [f'TEAM {x}' for x in range(13)]
    # scoring_settings = SettingsWindow.get()
    PP = get_player_pool()
    PP = calc_scores(PP, scoring_settings, roster_format)
    PP.loc[PP["is_keeper"] == True, 'is_drafted'] = True
    drafted_ids = PP.loc[PP["is_drafted"] == True, "sleeper_id"].tolist()

    adp_db = get_db_arr(PP, "adp", roster=roster_format, scoring=scoring_format)
    ecr_db = get_db_arr(PP, "ecr", roster=roster_format, scoring=scoring_format)
    db = get_db_arr(PP, "keepers", roster=roster_format, scoring=scoring_format)
    sleeper_live_draft = False
    yahoo_live_draft = False
    # This is for the DB array/view.  This should turn off when loading the ADP/ECR boards.
    # If both live_board and live_draft, refresh will update the live board
    live_board = True
    adp_board = False
    ecr_board = False
    """
    WHILE LOOP
    create and turn live_draft off
    """
    window = DraftboardWindow.get(settings, theme=None)
    while True:
        event, values = window.read(timeout=1000)
        # --- Break While Loop --- #
        if event in (sg.WIN_CLOSED, 'Exit'):
            settings["scoring_format"] = scoring_format
            settings["scoring_settings"] = scoring_settings
            settings["roster_format"] = roster_format
            with open(SETTINGS_PATH, "w") as file:
                json.dump(settings, file, indent=4)
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
            # Check the Live Draft status and update the label and drafted_ids
            if sleeper_live_draft:
                drafted_ids = PP.loc[PP["is_drafted"] == True, "sleeper_id"].tolist()
                window["-STATUS-"].update(value=f'Status: Connected to Sleeper Draft {id_text}')
            elif yahoo_live_draft:
                drafted_ids = PP.loc[PP["is_drafted"] == True, "yahoo_id"].tolist()
                window["-STATUS-"].update(value=f'Status: Connected to Yahoo Draft {id_text}')
            else:
                drafted_ids = PP.loc[PP["is_keeper"] == True, "sleeper_id"].tolist()
                window["-STATUS-"].update(value='Status: Offline')
            # Get the various variables needed from the window
            hide_d = window["-HIDE-DRAFTED-"].get()

            # ---- Update the Cheat Sheets and Bottom Tables ----- #
            for cheat_sheet_pos in ["QB", "WR", "TE", "RB"]:  # "ALL",
                cheatsheet_data = get_cheatsheet_data(PP, roster=roster_format, scoring=scoring_format,
                                                      table_pos=cheat_sheet_pos, hide_drafted=hide_d)
                window[f"-{cheat_sheet_pos}-TABLE-"].update(values=cheatsheet_data)
            # ----- Update the Bottom Table Data ----- #
            bottom_position = window['-BOTTOM-POS-DD-'].get()
            bottom_data = get_bottom_table(PP, pos=bottom_position.lower(), hide_drafted=hide_d, data_only=True)
            window['-BOTTOM-TABLE-'].update(values=bottom_data)
            # update_buttons(window, MAX_COLS, MAX_ROWS, BG_COLORS, db_arr=db)
            # ----- UPDATE BUTTONS - for loop to set the drafted players as "clicked" ---- #
            for col in range(MAX_COLS):
                for row in range(MAX_ROWS):
                    cur_id = window[(row, col)].metadata['sleeper_id']
                    y_id = window[(row, col)].metadata['yahoo_id']
                    if (cur_id in drafted_ids or y_id in drafted_ids) and hide_d:
                        window[(row, col)].metadata["is_clicked"] = True
                        window[(row, col)].update(button_color='white on gray')
                    else:
                        pass

            if sleeper_live_draft:
                try:
                    window["-STATUS-"].update(value='Status: Connected to Sleeper Draft')
                    PP["is_drafted"] = False
                    all_picks = draft.get_all_picks()
                    drafted_ids = [x['player_id'] for x in all_picks]
                    PP.loc[PP['sleeper_id'].isin(drafted_ids), "is_drafted"] = True
                    for pick in all_picks:
                        PP.loc[PP['sleeper_id'] == pick['player_id'], ["round", "draft_slot", "pick_no"]] = [
                            pick["round"], pick["draft_slot"], pick["pick_no"]]
                    db = get_db_arr(PP, "live", roster_format, scoring_format)
                    # ---- set the drafted_ids as True ---- #
                    # PP.loc[PP["sleeper_id"].isin(drafted_ids), "is_drafted"] = True
                    for col in range(MAX_COLS):
                        for row in range(MAX_ROWS):
                            cur_id = window[(row, col)].metadata["sleeper_id"]
                            if cur_id in drafted_ids:
                                window[(row, col)].metadata["is_clicked"] = True
                                window[(row, col)].update(button_color='white on gray')
                            else:
                                pass
                except TypeError:
                    sleeper_live_draft = False
                    sg.popup_quick_message("Connection to Draft Lost")
                finally:
                    if live_board:
                        window["-LOAD-DB-"].click()

            if yahoo_live_draft:
                window["-STATUS-"].update(value=f'Status: Connected to Yahoo Draft {id_text}')

                all_picks = yahoo_league.draft_results()

                drafted_ids = [x['player_id'] for x in all_picks]
                PP.loc[PP['yahoo_id'].isin(drafted_ids), "is_drafted"] = True
                for pick in all_picks:
                    r = pick['round']
                    c = pick['team_key']  # '414.l.1312973.t.2'   " '414.l.1312973.t.10'
                    c = c[-2:].replace(".", "")
                    p_no = pick['pick']
                    yahoo_id = str(pick['player_id'])  # .astype(str)  # 2449
                    PP.loc[PP["yahoo_id"] == yahoo_id, ['is_drafted', 'pick_no', 'draft_slot', 'round', ]] = [
                        True, p_no, c, r]

                db = get_db_arr(PP, "live", roster_format, scoring_format)
                # ---- set the drafted_ids as True ---- #
                PP.loc[PP["yahoo_id"].isin(drafted_ids), "is_drafted"] = True

            #update_buttons(window, MAX_COLS, MAX_ROWS, BG_COLORS, db_arr=db)
            update_all_tables(PP, window, roster_format, scoring_format)
                # finally:
                #     if live_board:
                #         window["-LOAD-DB-"].click()

        elif event == "Connect to Yahoo Draft":
            """
                        Get Draft ID
                        Validate Draft ID 
                        Create Draft Object
                        Remove is_drafted from PP
                        Update PP for is_drafted
                        
                        Remake Draftboard array
                        Place "is_drafted" players on empty DB 
                        Turn live_draft on 
                        drafted_ids = [x['player_id'] for x in all_picks]
                        """
            with open('data/draft_ids.json', "r") as file:
                id_list = json.load(file)
                yahoo_ids = id_list["yahoo_ids"]
                league_id_list = list(set(yahoo_ids))
                new_file = False
            if len(league_id_list) == 0:
                default_text = "Enter Yahoo ID"
            else:
                default_text = league_id_list[0]
            draft_id = PopUpDropDown("Enter Yahoo ID", "Enter the 7 Digit Yahoo League or Draft ID", league_id_list)
            # draft_id = sg.PopupGetText("Enter the Yahoo Draft ID or URL.", default_text=default_text)
            # print(draft_id)
            if not draft_id:
                sg.PopupQuick("No ID Entered")
                yahoo_live_draft = False
                pass
            else:
                league_id_list.append(draft_id)
                id_list["yahoo_ids"] = league_id_list
                yahoo_live_draft = True
                with open('data/draft_ids.json', "w") as file:
                    json.dump(id_list, file, indent=4)
                id_text = draft_id
                draft_id = "414.l." + draft_id[-7:]
                # draft_id = "414.l." + draft_id[-7:]
                # draft_id = 9881550
                # draft_id = "414.l." + "9882969"
                yahoo_league = yfa.league.League(OAUTH, draft_id)

                all_picks = yahoo_league.draft_results()
                print(f"First Call: Length of Yahoo all_picks = {len(all_picks)}")

                # Reset the PP dataframe
                PP["pick_no"] = None
                PP["adp_pick_no"] = None
                PP["ecr_pick_no"] = None
                PP["is_keeper"] = False
                PP["is_drafted"] = False
                # make empty db
                db = get_db_arr(PP, "live", roster_format, scoring_format)
                # Get new IDs
                drafted_ids = [str(x['player_id']) for x in all_picks]
                PP.loc[PP['yahoo_id'].isin(drafted_ids), "is_drafted"] = True
                for pick in all_picks:
                    r = pick['round']
                    c = pick['team_key']  # '414.l.1312973.t.2'   " '414.l.1312973.t.10'
                    c = c[-2:].replace(".", "")
                    p_no = pick['pick']
                    yahoo_id = str(pick['player_id'])  # .astype(str)  # 2449
                    PP.loc[PP["yahoo_id"] == yahoo_id, ['is_drafted', 'pick_no', 'draft_slot', 'round', ]] = [
                        True, p_no, c, r]
                db = get_db_arr(PP, "live", roster_format, scoring_format)
                # adp_db = get_db_arr(PP, "adp", roster=roster_format, scoring=scoring_format)  #  df_loc_col="is_drafted")
                # ecr_db = get_db_arr(PP, "ecr", roster=roster_format, scoring=scoring_format)   #  , df_loc_col="is_drafted")

                # except TypeError:
                #     sg.popup_quick_message("Error Connecting to Draft")
                #    yahoo_live_draft = False
                window["-LOAD-DB-"].click()
        elif event == "Connect to Sleeper Draft":
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
            # draft_id = sg.PopupGetText("Enter the Sleeper Draft ID or URL.")
            # print(draft_id)

            with open('data/draft_ids.json', "r") as file:
                id_list = json.load(file)
                sleeper_ids = id_list["sleeper_ids"]
                league_id_list = list(set(sleeper_ids))
                new_file = False
            if len(league_id_list) == 0:
                default_text = "Enter Sleeper ID"
                league_id_list.append(default_text)
            else:
                default_text = league_id_list[0]
            draft_id = PopUpDropDown("Enter Sleeper ID", "Enter the 18 Digit Sleeper Draft ID", league_id_list)
            draft_id = draft_id[-18:]
            if not draft_id:
                sg.PopupQuick("No ID Entered")
                sleeper_live_draft = False
                pass
            else:
                league_id_list.append(draft_id)
                id_list["sleeper_ids"] = [new_id for new_id in league_id_list if new_id != "Enter Sleeper ID"]
                sleeper_live_draft = True
                with open('data/draft_ids.json', "w") as file:
                    json.dump(id_list, file, indent=4)
                draft = Drafts(draft_id)  # create draft object
                id_text = draft_id

                all_picks = draft.get_all_picks()
                try:
                    # update the PP dataframe
                    PP["pick_no"] = None
                    PP["adp_pick_no"] = None
                    PP["ecr_pick_no"] = None
                    PP["is_keeper"] = False
                    PP["is_drafted"] = False
                    for pick in all_picks:
                        r = pick['round']
                        c = pick['draft_slot']
                        p_no = pick['pick_no']
                        sleeper_id = pick['player_id']  # 2449
                        PP.loc[PP["sleeper_id"] == sleeper_id, ['is_drafted', 'pick_no', 'draft_slot', 'round', ]] = [
                            True, p_no, c, r]
                    db = get_db_arr(PP, "live", scoring=scoring_format, roster=roster_format)
                    sleeper_live_draft = True  # turn live draft on
                except TypeError:
                    sg.popup_quick_message("Error Connecting to Draft")
                    sleeper_live_draft = False

        # ----- Select ADP Type ----- #
        elif event in ['2QB', 'PPR', 'Half-PPR', 'Non-PPR']:
            if event == "2QB":
                roster_format = "superflex"
            else:
                roster_format = "overall"
                scoring_format = event.lower().replace("-", "_")
            adp_db = get_db_arr(PP, "adp", roster=roster_format, scoring=scoring_format)
            ecr_db = get_db_arr(PP, "ecr", roster=roster_format, scoring=scoring_format)
            # TODO Map out the ecr_db to not sort by superflex
            #   Make calls for half-ppr and standard rankings as well.

            if adp_board:
                window["-LOAD-ADP-"].click()
            elif ecr_board:
                window["-LOAD-ECR-"].click()
            elif live_board:
                window["-LOAD-DB-"].click()
        elif event in ['-R1-', '-R2-', '-R3-', '-SUPERFLEX-']:
            # Get Roster type
            if window['-SUPERFLEX-'].get():
                roster_format = "superflex"
            else:
                roster_format = "overall"
            # Get Scoring type
            if window['-R1-'].get():
                scoring_format = 'ppr'
            elif window['-R2-'].get():
                scoring_format = 'half_ppr'
            elif window['-R3-'].get():
                scoring_format = 'non_ppr'
            # --- Get New Player Pool --- #
            # PP = get_player_pool()
            PP = calc_scores(PP, scoring_settings, roster_format)
            # -------Draftboard Arrays--------#
            adp_db = get_db_arr(PP, "adp", roster=roster_format, scoring=scoring_format)
            ecr_db = get_db_arr(PP, "ecr", roster=roster_format, scoring=scoring_format)
            if adp_board:
                window["-LOAD-ADP-"].click()
            elif ecr_board:
                window["-LOAD-ECR-"].click()
            elif live_board:
                window["-LOAD-DB-"].click()
            update_all_tables(PP, window, roster_format, scoring_format)
            # db = get_db_arr(PP, "keepers")
            """
            Reading the last used League ID to bring in league settings. 
            draft_order used to set the buttons for the board columns/teams.
            The league info should change if a new league is loaded. 
            """

            # -------Draftboard Arrays--------#
            # adp_db = get_db_arr(PP, "adp", roster_format=roster_format, scoring_format=scoring_format)
            # ecr_db = get_db_arr(PP, "ecr", roster_format=roster_format, scoring_format=scoring_format)
            # db = get_db_arr(PP, "keepers")
            # window["-LOAD-ADP-"].click()
            window["-Refresh-"].click()
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
            update_all_tables(PP, window, roster_format, scoring_format)
            # --- After updating the tables, if the draft is not live, then update those to gray as "hidden" --- #
            hide_d = window["-HIDE-DRAFTED-"].get()
            if sleeper_live_draft:
                drafted_ids = PP.loc[PP["is_drafted"] == True, "sleeper_id"].tolist()
            else:
                drafted_ids = PP.loc[PP["is_keeper"] == True, "sleeper_id"].tolist()
            for col in range(MAX_COLS):
                for row in range(MAX_ROWS):
                    cur_id = window[(row, col)].metadata['sleeper_id']
                    if cur_id in drafted_ids:
                        if hide_d:
                            window[(row, col)].metadata["is_clicked"] = True
                            window[(row, col)].update(button_color='white on gray')
                        else:
                            window[(row, col)].metadata["is_clicked"] = False
                            button_color = window[(row, col)].metadata["button_color"]
                            window[(row, col)].update(button_color=button_color)
        # Select position dropdown in bottom table
        elif event == '-BOTTOM-POS-DD-':
            update_all_tables(PP, window, roster_format, scoring_format)
        # click on button event
        elif event in [(r, c) for c in range(MAX_COLS) for r in range(MAX_ROWS)]:
            # CLICK ON BUTTON EVENT
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
            print(f"Button Meta: {window[(r, c)].metadata}")
            # --- Update the Cheatsheets and Bottom Table (Note: these will also update automatically on refresh) --- #
            update_all_tables(PP, window, roster_format, scoring_format)
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
        elif event == "-LOAD-ADP-":
            live_board = False
            adp_board = True
            ecr_board = False
            update_buttons(window, MAX_COLS, MAX_ROWS, BG_COLORS, db_arr=adp_db)
        elif event == "-LOAD-ECR-":
            live_board = False
            ecr_board = True
            adp_board = False
            update_buttons(window, MAX_COLS, MAX_ROWS, BG_COLORS, db_arr=ecr_db)
        elif event == "-LOAD-DB-":
            live_board = True
            ecr_board = False
            adp_board = False
            update_buttons(window, MAX_COLS, MAX_ROWS, BG_COLORS, db_arr=db)
            update_all_tables(PP, window, roster_format, scoring_format)
        elif event == "View Player Pool":
            ViewPlayerPool(PP)
        elif event == 'About...':
            sg.popup('Demo of table capabilities')
        elif event == 'Set Keepers':
            PP = KeeperPopUp(PP)
            # Refresh Arrays after Keeper Pop Up
            adp_db = get_db_arr(PP, "adp", roster_format, scoring_format)
            ecr_db = get_db_arr(PP, "ecr", roster_format, scoring_format)
            db = get_db_arr(PP, "keepers", roster_format, scoring_format)

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
        elif event == 'Disconnect':
            sleeper_live_draft = False
            yahoo_live_draft = False
        elif event == 'Change Theme':      # Theme button clicked, so get new theme and restart window
            event, values = sg.Window('Choose Theme', [[sg.Combo(sg.theme_list(), readonly=True, k='-THEME LIST-'), sg.OK(), sg.Cancel()]]).read(close=True)
            print(event, values)
            if event == 'OK':
                settings["scoring_format"] = scoring_format
                settings["scoring_settings"] = scoring_settings
                settings["roster_format"] = roster_format
                window.close()
                window = DraftboardWindow.get(settings, values['-THEME LIST-'])
        elif event.startswith(SEC1_KEY):
            window[SEC1_KEY].update(visible=not window[SEC1_KEY].visible)
            window[SEC1_KEY + '-BUTTON-'].update(
                window[SEC1_KEY].metadata[0] if window[SEC1_KEY].visible else window[SEC1_KEY].metadata[1])
        elif event.startswith(SEC2_KEY) or event == '-OPEN SEC2-CHECKBOX-':
            window[SEC2_KEY].update(visible=not window[SEC2_KEY].visible)
            window[SEC2_KEY + '-BUTTON-'].update(
                window[SEC2_KEY].metadata[0] if window[SEC2_KEY].visible else window[SEC2_KEY].metadata[1])
            window['-OPEN SEC2-CHECKBOX-'].update(not window[SEC2_KEY].visible)
        elif event == 'Scoring Settings':
            scoring_settings = SettingsWindow.create()
            PP = calc_scores(PP, scoring_settings, roster_format)
            PP = sort_reset_index(PP, sort_by=["vbd", "fpts"])

            update_all_tables(PP, window, roster_format, scoring_format)
    window.close()
