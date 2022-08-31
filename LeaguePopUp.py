from draftboard_brain import *
import PySimpleGUI as sg
from pathlib import Path
import json
from sleeper_wrapper import League


"""
Select the League
Display League Info
Calculate Custom Score 
"""

def PopUpDropDown(title, text, values):
    pop_drop_window = sg.Window(title,
        [[sg.Text(text)],
        [sg.DropDown(values, key='-DROP-', default_value=values[0])],
        [sg.OK(), sg.Cancel()]
    ])
    event, values = pop_drop_window.read()
    return None if event != 'OK' else values['-DROP-']

def LeaguePopUp():
    id_json = Path('data/league_ids.json')
    try:
        with open(id_json, "r") as file:
            id_list = json.load(file)
            sleeper_ids = id_list["sleeper_ids"]
            league_id_list = list(set(sleeper_ids))
            new_file = False
    except FileNotFoundError:
        new_file = True  # This will clear out the "Enter League ID text" when saving the first time
        # id_path.mkdir(parents=True, exist_ok=True)
        league_id_list = ["Enter League ID"]
    except json.decoder.JSONDecodeError:
        new_file = True  # This will clear out the "Enter League ID text" when saving the first time
        # id_path.mkdir(parents=True, exist_ok=True)
        league_id_list = ["Enter League ID"]

    col1_layout = [[sg.DropDown(values=league_id_list,
                                default_value=league_id_list[0],
                                size=(20, 1),
                                key='-LEAGUE-ID-DROPDOWN-')],
              [sg.Button("Load", enable_events=True, key="-LOAD-LEAGUE-")],
              [sg.Text("League Info")]]
    col1 = sg.Column(col1_layout)
    # col2_layout = [[sg.Text("League Info")], ] # [sg.Table(values=[], key="-LEAGUE-TABLE-")]]
    # col2 = sg.Column(col2_layout, key="-COL2-",)
    layout = [[col1]]
    window = sg.Window("League", layout=layout, size=(800, 600))
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            # save_keepers(df.loc[df["is_keeper"] == True].to_dict('records'))
            break
        elif event == "-LOAD-LEAGUE-":
            # pdb.set_trace()
            try:
                l_id = int(window["-LEAGUE-ID-DROPDOWN-"].get())
                league = League(league_id=l_id)
                league_id_list.append(window["-LEAGUE-ID-DROPDOWN-"].get())
                if new_file:
                    league_id_list.pop(0)
                with open(id_json, "w") as file:
                    json.dump(league_id_list, file, indent=4)
                window["-LEAGUE-ID-DROPDOWN-"].update(values=list(set(league_id_list)))
                league_info = league.get_league()

                sg.Popup(f"League {league_info['name']} loaded.\n")
                with open(f'data/league_ids/{l_id}.json', "w") as file:
                    json.dump(league_info, file, indent=4)
                return league
            except TypeError:
                sg.popup_quick_message("Sorry, that is not a valid league ID")
            except ValueError:
                sg.popup_quick_message("Sorry, that is not a valid league ID")

    window.close()


# LeaguePopUp()
