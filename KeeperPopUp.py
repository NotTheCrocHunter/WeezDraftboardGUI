import PySimpleGUI as sg
from draftboard_brain import *
import pdb

MAX_ROWS = 17
MAX_COLS = 12


def KeeperPopUp(df):
    df['name'].fillna("NA", inplace=True)
    print(df["sleeper_id"].loc[df["name"] == "NA"])
    keeper_list = df.loc[df["is_keeper"] == True, 'name'].to_list()
    not_kept_list = df.loc[df["is_keeper"] != True, 'name'].to_list()
    # Create pick_list list for window["-KEEPER-PICK-"]
    pick_list = make_pick_list()

    # Create a list of the already established keeper picks and pop them from the pick_list
    kept_picks = df["pick_no"].loc[df["is_keeper"] == True].to_list()
    kept_picks.sort(reverse=True)
    print(kept_picks)

    for pick in kept_picks:
        pick_list.pop(pick - 1)

    filter_tooltip = "Find Player"

    col4 = [[sg.Input(size=(20, 1), focus=True, enable_events=True, key='-FILTER-', tooltip=filter_tooltip)],
            [sg.Listbox(not_kept_list, key='-DRAFT-POOL-', size=(20, 15), auto_size_text=True,
                        select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)]]
    col5 = [[sg.Text("Pick Player")],
            [sg.Button("Add", key='-ADD-KEEPER-', enable_events=True)],
            [sg.Button("Remove", key='-REMOVE-KEEPER-', enable_events=True)],
            [sg.Button("Set", key='-SET-KEEPER-', enable_events=True)],
            [sg.Button("Clear", key='-CLEAR-KEEPERS-', enable_events=True)],
            [sg.Button("Load Mock Keepers", key='-LOAD-MOCK-KEEPERS-', enable_events=True)],
            [sg.DropDown(pick_list, key='-KEEPER-PICK-', default_value=pick_list[0])],
            [sg.OK()]]
    col6 = [[sg.Listbox(keeper_list, key='-KEEPER-LIST-', size=(20, 15), auto_size_text=True)]]
    keeper_window = sg.Window("Set Keepers", [[sg.Column(col4)] + [sg.Column(col5)] + [sg.Column(col6)]])
    while True:
        event, values = keeper_window.read()
        if event in (sg.WINDOW_CLOSED, "OK"):
            save_keepers(df.loc[df["is_keeper"] == True].to_dict('records'))
            keeper_window.close()
            break
        elif event == "-FILTER-":

            new_list = [i for i in not_kept_list if values['-FILTER-'].lower() in i.lower()]
            keeper_window['-DRAFT-POOL-'].update(new_list)
        elif event == "-ADD-KEEPER-":
            rd, slot = values["-KEEPER-PICK-"].split('.')
            rd, slot = int(rd), int(slot)
            if rd % 2 == 0:
                pick_no = (rd - 1) * MAX_COLS + MAX_COLS - slot + 1
            else:
                pick_no = (rd - 1) * MAX_COLS + slot
            pick_list.remove(values["-KEEPER-PICK-"])

            # pdb.set_trace()
            k_cols = ["is_keeper", "is_drafted", "round", "draft_slot", "pick_no"]
            k_name = ''.join(values["-DRAFT-POOL-"])
            df.loc[df["name"] == k_name, k_cols] = [True, True, rd, slot, pick_no]

            # df["board_loc"] = df[[= k_name, "board_loc"] = df.loc[df["name"] == k_name
            # pdb.set_trace()
            keeper_list = df.loc[df["is_keeper"] == True, 'name'].to_list()
            not_kept_list = df.loc[df["is_keeper"] != True, 'name'].to_list()
            #

            # UPDATE ALL 3 Values
            keeper_window["-KEEPER-PICK-"].update(values=pick_list, set_to_index=0)
            keeper_window["-KEEPER-LIST-"].update(values=keeper_list)
            keeper_window["-DRAFT-POOL-"].update(values=not_kept_list)
            pass
        elif event == "-REMOVE-KEEPER-":
            k_cols = ["is_keeper", "is_drafted", "round", "draft_slot", "pick_no"]
            k_name = ''.join(values["-KEEPER-LIST-"])

            rd = df.loc[df["name"] == k_name, "round"].item()
            draft_slot = df.loc[df["name"] == k_name, "draft_slot"].item()
            pick_no = df.loc[df["name"] == k_name, "pick_no"].item()
            pick_no -= 1
            pick_list_text = f"{rd}.{draft_slot}"
            pick_list.insert(pick_no, pick_list_text)
            df.loc[df["name"] == k_name, k_cols] = [False, False, None, None, None]
            keeper_list = df.loc[df["is_keeper"] == True, 'name'].to_list()
            not_kept_list = df.loc[df["is_keeper"] != True, 'name'].to_list()

            keeper_window["-KEEPER-PICK-"].update(values=pick_list, set_to_index=0)
            keeper_window["-KEEPER-LIST-"].update(values=keeper_list)
            keeper_window["-DRAFT-POOL-"].update(values=not_kept_list)
            pass
        elif event == "-SET-KEEPER-":
            # split the keeper-pick value for round, slot and calc for pick_no
            rd, slot = ''.join(values["-KEEPER-PICK-"]).split('.')
            rd, slot = int(rd), int(slot)
            if rd % 2 == 0:
                pick_no = (rd - 1) * MAX_COLS + MAX_COLS - slot + 1
            else:
                pick_no = (rd - 1) * MAX_COLS + slot

            # Assign the keeper values to the dataframe
            k_cols = ["is_keeper", "is_drafted", "round", "draft_slot", "pick_no"]
            k_name = ''.join(values["-KEEPER-"])
            df.loc[df["name"] == k_name, k_cols] = [True, True, rd, slot, pick_no]
            # pdb.set_trace()

            # make the keeper list from the dataframe and then save to the JSON
            keeper_list = df.loc[df["is_keeper"] == True].to_dict('records')
            # pdb.set_trace()
            with open('../sleeper-api-wrapper/data/keepers/keepers.json', 'w') as file:
                json.dump(keeper_list, file, indent=4)

            # get new keeper list text for text box
            keeper_list_text = open_keepers(get="text")
            keeper_window["-KEEPER-LIST-"].update(values=keeper_list_text)
            # pdb.set_trace()
            """
            'round': 15, 'roster_id': None, 'player_id': '7606', 'picked_by': '339134645083856896', 'pick_no': 171, 'is_keeper': None, 'draft_slot': 3
            """
        elif event == "-CLEAR-KEEPERS-":
            df = reset_keepers(df)  # resets the keeper values in the json and the dataframe
            keeper_list_text = open_keepers(get="text")  # This opens empty list
            keeper_window["-KEEPER-LIST-"].update(values=keeper_list_text)
        elif event == "-LOAD-MOCK-KEEPERS-":
            # df Switch the keeper values on/off
            df = reset_keepers(df)  # resets the keeper values in the json and the dataframe
            # get the mock keeper list
            mock_id = sg.PopupGetText("Get Mock Keepers")
            if not mock_id:
                break
            mock_keepers = get_mock_keepers(mock_id)
            # fix the column names
            for k in mock_keepers:
                k['sleeper_id'] = k['player_id']
                k['is_keeper'] = True
                k['is_drafted'] = False
            # save the mock keepers to the json file
            save_keepers(mock_keepers)
            keeper_list, keeper_list_text = open_keepers()
            # iterate over the keeper list to grab the dict values and assign to the main player_pool dataframe
            k_cols = ['is_keeper', 'pick_no', 'draft_slot', 'round']
            for p in keeper_list:
                id = p['sleeper_id']
                is_keeper = p['is_keeper']
                # is_drafted = p["is_drafted"]
                pick_no = p['pick_no']
                slot = p['draft_slot']
                rd = p['round']
                df.loc[df['sleeper_id'] == id, k_cols] = [is_keeper, pick_no, slot, rd]  # is_drafted

            keeper_window["-KEEPER-LIST-"].update(values=keeper_list_text)
            # print(mock_keepers)
        print(event)
        print(values)
        print(keeper_list)
    return df
    keeper_window.close()
    

def make_pick_list():
    """
    This func reorders  the picks to be in snake-draft format.
    """
    pl = [f"{r + 1}.{c + 1}" for r in range(MAX_ROWS) for c in range(MAX_COLS)]
    pl = np.array(pl)
    pl = np.reshape(pl, (MAX_ROWS, MAX_COLS))
    pl[1::2, :] = pl[1::2, ::-1]
    pl = pl.flatten()

    return pl.tolist()


def sort_keepers(df):
    # Add in None values for Keeper columns
    k_cols = ['is_keeper', 'is_drafted', 'pick_no', 'draft_slot', 'round']

    for k in k_cols:
        df[k] = None

    # Open keeper list of dicts so that we can set the keeper value to True
    keeper_list = open_keepers(get="list")

    # iterate over the keeper list to grab the dict values and assign to the main player_pool dataframe
    for player_dict in keeper_list:
        p = player_dict
        if 'player_id' in p.keys():
            p['sleeper_id'] = p['player_id']
        id = p['sleeper_id']
        is_keeper = p['is_keeper']
        # initializing the keeper/drafted value as them same.  The values will update while drafting
        is_drafted = False  # p['is_keeper']
        pick_no = p['pick_no']
        slot = p['draft_slot']
        rd = p['round']

        df.loc[df['sleeper_id'] == id, k_cols] = [is_keeper, is_drafted, pick_no, slot, rd]

    return df



def reorder_keepers(key, p_pool):
    p_pool.sort_values(by=[key], ascending=True, inplace=True)
    return


def open_keepers(get=None):
    keeper_json_path = Path('data/keepers/keepers.json')
    try:
        with open(keeper_json_path, "r") as data:
            keeper_list = json.load(data)
            print(f"Total Keepers Found: {len(keeper_list)}")
            keeper_list_text = [f"{k['round']}.{k['draft_slot']}" for k in keeper_list]
            # keeper_list_text = [f"{k['name']} {k['round']}.{k['draft_slot']}" for k in keeper_list]
    except KeyError:
        with open(keeper_json_path, "r") as data:
            keeper_list = json.load(data)
            print(f"Opened Keeper List: {keeper_list}")
            keeper_list_text = [f"{k['round']}.{k['draft_slot']}" for k in keeper_list]
            # keeper_list_text = [f"{k['name']} {k['round']}.{k['draft_slot']}" for k in keeper_list]
    except FileNotFoundError:
        keeper_list = []
        keeper_list_text = []

    if not get:
        return keeper_list, keeper_list_text
    elif get == "list":
        return keeper_list
    elif get == "text":
        return keeper_list_text
    else:
        print("Can only accept 'list' or 'text'")
        return None


def clear_all_keepers():
    keeper_list = []
    Path('data/keepers').mkdir(exist_ok=True, parents=True)
    with open('data/keepers/keepers.json', 'w') as file:
        json.dump(keeper_list, file, indent=4)
    print("keepers.json overwritten, set as []")


def get_mock_keepers(mock_id):
    try:
        mock_draft = Drafts(mock_id)
        return mock_draft.get_all_picks()
    except:
        sg.popup_quick_message("Error getting mock keepers")


def reset_keepers(df):
    clear_all_keepers()  # this clears the keeper_list as [] and overwrites the keepers.json with empty list
    # this resets the columns in the PP DataFrame
    k_cols = ['is_keeper', 'is_drafted', 'pick_no', 'draft_slot', 'round']
    for k in k_cols:
        df[k] = None
    return df


def save_keepers(keeper_list):
    cols = ["name", "sleeper_id", 'is_keeper', 'pick_no', 'draft_slot', 'round', 'button_text']
    keeper_list = [{k: v for k, v in keeper.items() if k in cols} for keeper in keeper_list]
    # keeper_path = Path('../sleeper-api-wrapper/data/keepers/keepers.json')
    keeper_path = Path('data/keepers/keepers.json')
    print(f"Saving {len(keeper_list)} keepers to {keeper_path}")

    with open(keeper_path, 'w') as file:
        json.dump(keeper_list, file, indent=4)
    pass

