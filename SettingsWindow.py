import PySimpleGUI as sg
from pathlib import Path
import json


def SettingsWindow(silent_mode=False):
    """
    Settings window to capture scoring settings.  
    Reads/writes to local json file for storage. 
    Returns scoring dict.
    """
    
    default_settings = {"pass_yd": 0.04,
                        "pass_td": 4,
                        "pass_int": -2,                                              
                        "rec": 1,
                        "rec_yd": 0.1,
                        "rec_td": 6,
                        "rush_yd": 0.1,
                        "rush_td": 6,  
                        "fum": -2,
                        "bonus_rec_te": 0,
                        "bonus_rec_rb": 0,
                        "bonus_rec_wr": 0,
                        }            

    settings_path = Path('data/settings')
    settings_json = Path('data/settings/scoring_settings.json')
    try:
        with open(settings_json, "r") as file:
            scoring_settings = json.load(file)
    except FileNotFoundError:
        settings_path.mkdir(parents=True, exist_ok=True)
        scoring_settings = default_settings
        with open(settings_json, "w") as file:
            json.dump(scoring_settings, file, indent=4)

    if silent_mode:
        return scoring_settings
    else:
        s = scoring_settings

    col1_layout = [[sg.T("Passing Yards Per Point")],
                   [sg.T("Passing TDs")],
                   [sg.T("Interceptions")],
                   [sg.T("Receptions")],
                   [sg.T("Receiving Yards Per Point")],
                   [sg.T("Receiving TDs")],
                   [sg.T("Rushing Yards Per Point")],
                   [sg.T("Rushing TDs")],
                   [sg.T("Fumbles Lost")],
                   [sg.T("TE Rec Bonus")],
                   [sg.T("RB Rec Bonus")],
                   [sg.T("WR Rec Bonus")],
                   ]

    col2_layout = [[sg.Input(default_text=int(1/s["pass_yd"]), size=5, key="pass_yd")],
                   [sg.Input(default_text=int(s["pass_td"]), size=5, key="pass_td")],
                   [sg.Input(default_text=int(s["pass_int"]), size=5, key="pass_int")],
                   [sg.Input(default_text=int(s["rec"]), size=5, key="rec")],
                   [sg.Input(default_text=int(1/s["rec_yd"]/1), size=5, key="rec_yd")],
                   [sg.Input(default_text=int(s["rec_td"]), size=5, key="rec_td")],
                   [sg.Input(default_text=int(1/s["rush_yd"]/1), size=5, key="rush_yd")],
                   [sg.Input(default_text=int(s["rush_td"]), size=5, key="rush_td")],
                   [sg.Input(default_text=int(s["fum"]), size=5, key="fum")],
                   [sg.Input(default_text=float(s["bonus_rec_te"]), size=5, key="bonus_rec_te")],
                   [sg.Input(default_text=int(s["bonus_rec_rb"]), size=5, key="bonus_rec_rb")],
                   [sg.Input(default_text=int(s["bonus_rec_wr"]), size=5, key="bonus_rec_wr")],
                   ]
    
    col1 = sg.Column(col1_layout)
    col2 = sg.Column(col2_layout)
    save_button = sg.Button("Save", key="-SAVE-", enable_events=True)
    cancel_button = sg.Button("Cancel", key="-CANCEL-", enable_events=True)
    window = sg.Window("Settings", layout=[[col1, col2], [save_button, cancel_button]], size=(300, 300))

    while True:
        event, values = window.read()

        if event in [sg.WINDOW_CLOSED, '-CANCEL-']:
            sg.popup("Scoring settings not saved.", title="Settings")
            break

        elif event == "-SAVE-":
            scoring_settings = {"pass_yd": 1/int(window["pass_yd"].get()),
                                "pass_td": float(window["pass_td"].get()),
                                "pass_int": float(window["pass_int"].get()),
                                "rec": float(window["rec"].get()),
                                "rec_yd": float(1/int(window["rec_yd"].get())),
                                "rec_td": float(window["rec_td"].get()),
                                "rush_yd": 1/int(window["rush_yd"].get()),
                                "rush_td": float(window["rush_td"].get()),
                                "fum": float(window["fum"].get()),
                                "bonus_rec_te": float(window["bonus_rec_te"].get()),
                                "bonus_rec_rb": float(window["bonus_rec_rb"].get()),
                                "bonus_rec_wr": float(window["bonus_rec_wr"].get()),
                                }
            with open(settings_json, "w") as file:
                json.dump(scoring_settings, file, indent=4)
            sg.popup("Scoring settings saved.", title="Settings")
            break
    return scoring_settings
    window.close()
"""
sw=SettingsWindow()
print(sw)
print("hi")"""