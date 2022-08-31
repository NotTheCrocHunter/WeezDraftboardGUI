import json
from pathlib import Path

settings_dict = {
    "roster_format": "overall",
    "scoring_format": "ppr",
    "scoring_settings": {
         "pass_yd": 0.04,
         "pass_td": 4.0,
         "pass_int": -2.0,
         "rec": 1.0,
         "rec_yd": 0.1,
         "rec_td": 6.0,
         "rush_yd": 0.1,
         "rush_td": 6.0,
         "fum": -2.0,
         "bonus_rec_te": 0.5,
         "bonus_rec_rb": 0.0,
         "bonus_rec_wr": 0.0
    }
}


# settings_path = Path('data/settings.json')
"""
with open(settings_path, "w") as file:
    json.dump(settings_dict, file, indent=4)
"""
# settings_path = Path('data/settings.json')
id_path = Path('data/draft_ids.json')

id_dict = {"sleeper_ids": [],
           "yahoo_ids": []}

with open(id_path, "w") as file:
    json.dump(id_dict, file, indent=4)