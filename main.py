import WeezDraftboard
import pdb
from draftboard_brain import *
from KeeperPopUp import KeeperPopUp
from LeaguePopUp import LeaguePopUp
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

    MAX_ROWS = 17
    MAX_COLS = 12
    BOARD_LENGTH = MAX_ROWS * MAX_COLS
    CONSUMER_KEY = os.getenv('YAHOO_CONSUMER_KEY')
    CONSUMER_SECRET = os.getenv('YAHOO_CONSUMER_SECRET')
    OAUTH = OAuth2(None, None, from_file='data/yahoo/oauth2.json')
    roster = "superflex"
    scoring = "ppr"

    """
    Reading the last used League ID to bring in league settings. 
    draft_order used to set the buttons for the board columns/teams.
    The league info should change if a new league is loaded. 
    """
    scoring_settings, draft_order, league_found = load_saved_league()
    # draft_order = [f'TEAM {x}' for x in range(13)]
    # scoring_settings = SettingsWindow.get()
    PP = get_player_pool()
    PP = calc_scores(PP, scoring_settings, roster)
    drafted_ids = PP.loc[PP["is_drafted"] == True, "sleeper_id"].tolist()

    adp_db = get_db_arr(PP, "adp", roster=roster, scoring=scoring)
    ecr_db = get_db_arr(PP, "ecr", roster=roster, scoring=scoring)
    db = get_db_arr(PP, "keepers")
    sleeper_live_draft = False
    yahoo_live_draft = False
    # This is for the DB array/view.  This should turn off when loading the ADP/ECR boards.
    # If both live_board and live_draft, refresh will update the live board
    live_board = True
    """
        WHILE LOOP
        create and turn live_draft off
        """


    window = WeezDraftboard.get()
    while True:
        event, values = window.read(timeout=1000)
        # --- Break While Loop --- #
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        elif event == 'Scoring Settings':
            scoring_settings = SettingsWindow.create()
            PP = calc_scores(PP, scoring_settings, roster)
            PP = sort_reset_index(PP, sort_by=["vbd", "fpts"])
            # update_all_tables(PP, window, roster, scoring)
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
                window["-STATUS-"].update(value=f"Viewing: {scoring.upper()} scoring.  Status: Connected")
            elif yahoo_live_draft:
                drafted_ids = PP.loc[PP["is_drafted"] == True, "sleeper_id"].tolist()
                window["-STATUS-"].update(value=f"Viewing: {scoring.upper()} scoring.  Status: Connected")
            else:
                drafted_ids = PP.loc[PP["is_keeper"] == True, "sleeper_id"].tolist()
                window["-STATUS-"].update(value=f"Viewing: {scoring.upper()} scoring.  Status: Offline")

            # Get the various variables needed from the window
            hide_d = window["-HIDE-DRAFTED-"].get()
            # roster_type = window["--"].get()
            # scoring_type = window['--'].get()

            # ---- Update the Cheat Sheets and Bottom Tables ----- #
            # update_all_tables(PP, window, roster, scoring)
            for cheat_sheet_pos in ["QB", "WR", "TE", "RB"]:  # "ALL",
                cheatsheet_data = get_cheatsheet_data(PP, roster=roster, scoring=scoring,
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
                    if cur_id in drafted_ids:
                        window[(row, col)].metadata["is_clicked"] = True
                        window[(row, col)].update(button_color='white on gray')
                    else:
                        pass
            if sleeper_live_draft:
                try:
                    window["-STATUS-"].update(value='Status: Connected to Sleeper Draft')
                    all_picks = draft.get_all_picks()
                    drafted_ids = [x['player_id'] for x in all_picks]
                    PP.loc[PP['sleeper_id'].isin(drafted_ids), "is_drafted"] = True
                    for pick in all_picks:
                        PP.loc[PP['sleeper_id'] == pick['player_id'], ["round", "draft_slot", "pick_no"]] = [
                            pick["round"], pick["draft_slot"], pick["pick_no"]]
                    db = get_db_arr(PP, "live")
                    # ---- set the drafted_ids as True ---- #
                    PP.loc[PP["sleeper_id"].isin(drafted_ids), "is_drafted"] = True
                except TypeError:
                    sleeper_live_draft = False
                    sg.popup_quick_message("Connection to Draft Lost")
                finally:
                    if live_board:
                        window["-LOAD-DB-"].click()
            if yahoo_live_draft:
                # try:
                window["-STATUS-"].update(value='Status: Connected to Yahoo Draft')
                all_picks = yahoo_league.draft_results()
                drafted_ids = [str(x['player_id']) for x in all_picks]
                PP.loc[PP['player_yahoo_id'].isin(drafted_ids), "is_drafted"] = True
                for pick in all_picks:
                    r = pick['round']
                    c = pick['team_key']  # '414.l.1312973.t.2'   " '414.l.1312973.t.10'
                    c = c[-2:].replace(".", "")
                    p_no = pick['pick']
                    yahoo_id = pick['player_id']  # 2449
                    PP.loc[PP["player_yahoo_id"] == yahoo_id, ['is_drafted', 'pick_no', 'draft_slot', 'round', ]] = \
                        [True, p_no, c, r]

                db = get_db_arr(PP, "live")
                # ---- set the drafted_ids as True ---- #
                PP.loc[PP["player_yahoo_id"].isin(drafted_ids), "is_drafted"] = True
                """
                except TypeError:
                    yahoo_live_draft = False
                    sg.popup_quick_message("Connection to Draft Lost")
                finally:
                    if live_board:
                        window["-LOAD-DB-"].click()
                """
        elif event == "Connect to Yahoo Draft":
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
            draft_id = sg.PopupGetText("Enter the Yahoo Draft ID or URL.")
            # print(draft_id)
            if not draft_id:
                sg.PopupQuick("No ID Entered")
                sleeper_live_draft = False
                pass
            else:
                draft_id = "414.l." + draft_id[-7:]
                yahoo_league = yfa.league.League(OAUTH, draft_id)
                try:
                    all_picks = yahoo_league.draft_results()
                except:
                    print("Error Getting Draft")
                    continue
                drafted_ids = [str(x['player_id']) for x in all_picks]
                PP.loc[PP['player_yahoo_id'].isin(drafted_ids), "is_drafted"] = True
                # try:
                # update the PP dataframe
                PP["pick_no"] = None
                PP["adp_pick_no"] = None
                PP["ecr_pick_no"] = None
                PP["is_keeper"] = False
                PP["is_drafted"] = False
                for pick in all_picks:
                    r = pick['round']
                    c = pick['team_key']  # '414.l.1312973.t.2'   " '414.l.1312973.t.10'
                    c = c[-2:].replace(".", "")
                    p_no = pick['pick']
                    yahoo_id = str(pick['player_id'])  # .astype(str)  # 2449
                    PP.loc[PP["player_yahoo_id"] == yahoo_id, ['is_drafted', 'pick_no', 'draft_slot', 'round', ]] = [
                        True, p_no, c, r]
                db = get_db_arr(PP, "live")
                adp_db = get_db_arr(PP, "adp", roster=roster, scoring=scoring, df_loc_col="is_drafted")
                ecr_db = get_db_arr(PP, "ecr", roster=roster, scoring=scoring, df_loc_col="is_drafted")
                yahoo_live_draft = True  # turn live draft on
                # except TypeError:
                #     sg.popup_quick_message("Error Connecting to Draft")
                #    yahoo_live_draft = False
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
            # TODO: Figure out how to avoid HTTPError when the sleeper draft ID is not filled out.
            draft_id = sg.PopupGetText("Enter the Sleeper Draft ID or URL.")
            print(draft_id)
            draft_id = draft_id[-18:]
            if not draft_id:
                sg.PopupQuick("No ID Entered")
                sleeper_live_draft = False
                pass
            else:
                draft = Drafts(draft_id)  # create draft object
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
                    db = get_db_arr(PP, "live")
                    adp_db = get_db_arr(PP, "adp", df_loc_col="is_drafted")
                    ecr_db = get_db_arr(PP, "ecr", df_loc_col="is_drafted")
                    sleeper_live_draft = True  # turn live draft on
                except TypeError:
                    sg.popup_quick_message("Error Connecting to Draft")
                    sleeper_live_draft = False
        # ----- Select ADP Type ----- #
        elif event in ['2QB', 'PPR', 'Half-PPR', 'Non-PPR']:
            # PP, draft_order, league_found = get_player_pool(scoring_type=event.lower())
            # PP = get_player_pool(PP, roster=event,
            # PP = get_player_pool(roster=event)
            adp_db = get_db_arr(PP, "adp")
            ecr_db = get_db_arr(PP, "ecr")
            # TODO Map out the ecr_db to not sort by superflex
            #   Make calls for half-ppr and standard rankings as well.
            window["-LOAD-ADP-"].click()
        elif event in ['-R1-', '-R2-', '-R3-', '-SUPERFLEX-']:
            # Get Roster type
            if window['-SUPERFLEX-'].get():
                roster = "superflex"
            else:
                roster = "overall"
            # Get Scoring type
            if window['-R1-'].get():
                scoring = 'PPR'
            elif window['-R2-'].get():
                scoring = 'Half-PPR'
            elif window['-R3-'].get():
                scoring = 'Non-PPR'
            # --- Get New Player Pool --- #
            # PP = get_player_pool()
            PP = calc_scores(PP, SettingsWindow.get(), roster)
            # -------Draftboard Arrays--------#
            adp_db = get_db_arr(PP, "adp", roster=roster, scoring=scoring)
            ecr_db = get_db_arr(PP, "ecr", roster=roster, scoring=scoring)

            # update_all_tables(PP, window, roster, scoring)
            # db = get_db_arr(PP, "keepers")
            """
            Reading the last used League ID to bring in league settings. 
            draft_order used to set the buttons for the board columns/teams.
            The league info should change if a new league is loaded. 
            """

            # -------Draftboard Arrays--------#
            # adp_db = get_db_arr(PP, "adp", roster=roster, scoring=scoring)
            # ecr_db = get_db_arr(PP, "ecr", roster=roster, scoring=scoring)
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
            # update_all_tables(PP, window, roster, scoring)
            # --- After updating the tables, if the draft is not live, then update those to gray as "hidden" --- #
            if sleeper_live_draft:
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
            # update_all_tables(PP, window, roster, scoring)
            pass
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
            # --- Update the Cheatsheets and Bottom Table (Note: these will also update automatically on refresh) --- #
            # update_all_tables(PP, window, roster, scoring)
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
        elif event == 'Disconnect':
            sleeper_live_draft = False
            yahoo_live_draft = False

    window.close()
