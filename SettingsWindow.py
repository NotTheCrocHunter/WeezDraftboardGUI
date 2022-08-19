from draftboard_brain import *
import PySimpleGUI as sg
from pathlib import Path
import json
from sleeper_wrapper import League


def SettingsWindow():

    settings_path = Path('data/settings')
    settings_json = Path('data/settings/settings.json')
    try:
        with open(settings_json, "r") as file:
            league_id_list = json.load(file)
            league_id_list = list(set(league_id_list))
            new_file = False
    except FileNotFoundError:
        new_file = True  # This will clear out the "Enter League ID text" when saving the first time
        settings_path.mkdir(parents=True, exist_ok=True)
        settings = {
            "roster_settings":{'2QB', 'Half-PPR', 'PPR', 'Non-PPR'},
            "scoring_settings": {
                "pass_yd": 0.04,
                "pass_td": 4.0,
                "rush_yd": 0.1,
                "rush_td": 6.0,
                "rec": 1.0,
                "rec_yd": 0.1,
                "rec_td": 6.0,
                "bonus_rec_te": 0.5,
                "fum": -2.0,
                "pass_int": -2.0,
            }
        }
    except json.decoder.JSONDecodeError:
        new_file = True  # This will clear out the "Enter League ID text" when saving the first time
        settings_path.mkdir(parents=True, exist_ok=True)
        league_id_list = ["Enter League ID"]
    tab1_layout = [[sg.T("SuperFlex (2QB)")],
                   [sg.T("PPR")],
                   [sg.T("Half-PPR")],
                   [sg.T("Non-PPR")]]
    tab2_layout = [[sg.T("Passing Yards Per Point")],
                   [sg.T("Passing TDs")],
                   [sg.T("Rushing Yards Per Point")],
                   [sg.T("Rushing TDs")],
                   [sg.T("Receptions")],
                   [sg.T("Receiving Yards Per Point")],
                   [sg.T("Receiving TDs")],
                   [sg.T("TE Rec Bonus")],
                   [sg.T("Fumbles Lost")],
                   [sg.T("Interceptions")]
                   ]
    tab1 = sg.Tab("ADP Settings", layout=tab1_layout)
    tab2 = sg.Tab("Scoring Settings", layout=tab2_layout)
    tab_group = sg.TabGroup([[tab1, tab2]], tab_location="lefttop")
    # col1 = sg.Column(col1_layout)
    """

    """
    # col = sg.Column(col1_layout, col2_layout)
    # col2_layout = [[sg.Text("League Info")], ] # [sg.Table(values=[], key="-LEAGUE-TABLE-")]]
    # col2 = sg.Column(col2_layout, key="-COL2-",)
    # layout = [tab_group]
    window = sg.Window("Settings", layout=[[tab_group]], size=(800, 600))
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            # save_keepers(df.loc[df["is_keeper"] == True].to_dict('records'))
            break
        elif event == "-SAVE-":
            pass
        elif event == "-CANCEL-":
            pass
        elif event == "LOAD":
            pass

    window.close()

SettingsWindow()