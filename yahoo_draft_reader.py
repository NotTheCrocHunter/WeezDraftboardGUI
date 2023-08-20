from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

oauth = OAuth2(None, None, from_file='data/yahoo/oauth2.json')

game = yfa.game.Game(oauth, "nfl")
# print(game.league_ids())
league_url = "https://football.fantasysports.yahoo.com/f1/1312973"
league_id = "414.l." + league_url[-7:]
league_id = "414.l.9891243"
lg = yfa.league.League(oauth, league_id)

draft_results = lg.draft_results()
# print(lg.current_week())
print(draft_results)


"""
Draft results format:
{'pick': 1,
 'round': 1,
 'cost': '4',
 'team_key': '388.l.27081.t.4',
 'player_id': 9490}
"""

