"""
One Time script to save yahoo oauth
"""
from yahoo_oauth import OAuth2
import json
from pathlib import Path

save_path = Path('data/yahoo')
save_path.mkdir(parents=True, exist_ok=True)
creds = {'consumer_key': 'dj0yJmk9R21JN0J0RGxPVGNJJmQ9WVdrOWRXWmpkM1Z6UVhFbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PThi', 'consumer_secret': '1790d3c912407ba9c26063319bf07fa745e8b731'}
with open("data/yahoo/oauth2.json", "w") as f:
   f.write(json.dumps(creds))

oauth = OAuth2(None, None, from_file='data/yahoo/oauth2.json')
