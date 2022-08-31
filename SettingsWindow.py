import PySimpleGUI as sg
from pathlib import Path
import json


def get():
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

    settings_path = Path('data/settings.json')

    with open(settings_path, "r") as file:
        settings = json.load(file)

    return settings


def create(silent_mode=False):
    """
    Settings window to capture scoring_format settings.
    Reads/writes to local json file for storage. 
    Returns scoring_format dict.
    """
    settings_path = Path('data/settings.json')
    # settings_json = Path('data/settings/scoring_settings.json')
    
    settings = get()
    scoring_settings = settings["scoring_settings"]

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
                   [sg.Input(default_text=s["rec"], size=5, key="rec")],
                   [sg.Input(default_text=int(1/s["rec_yd"]/1), size=5, key="rec_yd")],
                   [sg.Input(default_text=int(s["rec_td"]), size=5, key="rec_td")],
                   [sg.Input(default_text=int(1/s["rush_yd"]/1), size=5, key="rush_yd")],
                   [sg.Input(default_text=int(s["rush_td"]), size=5, key="rush_td")],
                   [sg.Input(default_text=int(s["fum"]), size=5, key="fum")],
                   [sg.Input(default_text=s["bonus_rec_te"], size=5, key="bonus_rec_te")],
                   [sg.Input(default_text=s["bonus_rec_rb"], size=5, key="bonus_rec_rb")],
                   [sg.Input(default_text=s["bonus_rec_wr"], size=5, key="bonus_rec_wr")],
                   ]
    
    col1 = sg.Column(col1_layout)
    col2 = sg.Column(col2_layout)
    save_button = sg.Button("Save", key="-SAVE-", enable_events=True)
    cancel_button = sg.Button("Cancel", key="-CANCEL-", enable_events=True)
    layout = [[col1, col2], [save_button, cancel_button]]
    settings_window = sg.Window("Settings", layout=layout, modal=True)

    while True:
        event, values = settings_window.read()

        if event in [sg.WINDOW_CLOSED, '-CANCEL-']:
            # sg.popup("Scoring settings not saved.", title="Settings")
            settings_window.close()
            break

        elif event == "-SAVE-":
            scoring_settings = {"pass_yd": 1/int(settings_window["pass_yd"].get()),
                                "pass_td": float(settings_window["pass_td"].get()),
                                "pass_int": float(settings_window["pass_int"].get()),
                                "rec": float(settings_window["rec"].get()),
                                "rec_yd": float(1/int(settings_window["rec_yd"].get())),
                                "rec_td": float(settings_window["rec_td"].get()),
                                "rush_yd": 1/int(settings_window["rush_yd"].get()),
                                "rush_td": float(settings_window["rush_td"].get()),
                                "fum": float(settings_window["fum"].get()),
                                "bonus_rec_te": float(settings_window["bonus_rec_te"].get()),
                                "bonus_rec_rb": float(settings_window["bonus_rec_rb"].get()),
                                "bonus_rec_wr": float(settings_window["bonus_rec_wr"].get()),
                                }
            settings["scoring_settings"] = scoring_settings
            with open(settings_path, "w") as file:
                json.dump(settings, file, indent=4)
            # sg.popup("Scoring settings saved.", title="Settings")
            settings_window.close()
            break
    return scoring_settings
    settings_window.close()
"""
sw=SettingsWindow()
print(sw)
print("hi")"""