import pandas as pd
from scrape_ffcalc_adp import get_adp_df
from draftboard_brain import get_db_arr
import json
from pathlib import Path
import numpy as np
SETTINGS_PATH = Path('data/settings.json')


with open(SETTINGS_PATH, "r") as file:
    settings = json.load(file)
roster_format = settings["roster_format"]
scoring_format = settings["scoring_format"]
scoring_settings = settings["scoring_settings"]
# df = get_adp_df(12, 2021)
# adp_db = get_db_arr(df, key="adp", roster='ppr', scoring='ppr')

# print(adp_db)

arr = np.arange(16*12).reshape(16,12)
arr[1::2, :] = arr[1::2, ::-1]
df = pd.DataFrame(arr)
df.to_html('data/html_save.html')
print(df)
