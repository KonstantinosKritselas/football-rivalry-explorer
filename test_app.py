"""A SMALL test for app.py's pure logic. We run it with python test_app.py"""
from datetime import date

from app import match_row, season_list

# Season_list: 10 seasons, chronological, ends with season in progress
seasons = season_list(n=10, today=date(2026, 9, 18))
assert seasons == [f"{y}-{y + 1}" for y in range(2017, 2027)], seasons
assert len(seasons) == 10

# Before July ->
# Still in the previous season
seasons_spring = season_list(n=3, today=date(2026, 3, 1))
assert seasons_spring[-1] == "2025-2026", seasons_spring

# Match_row: home win, assigned to the right team regardless of who's home
row = match_row(
    {"strLeague": "English Premier League", "strHomeTeam": "Arsenal",
     "strAwayTeam": "Chelsea", "intHomeScore": "2", "intAwayScore": "1",
     "idEvent": "1", "dateEvent": "2020-01-01", "strSeason": "2019-2020"},
    "Arsenal", "Chelsea",
)
assert row["winner"] == "Arsenal"
assert row["Arsenal_goals"] == 2 and row["Chelsea_goals"] == 1

# No friendly matches 
assert match_row(
    {"strLeague": "Club Friendly", "strHomeTeam": "Arsenal", "strAwayTeam": "Chelsea",
     "intHomeScore": "1", "intAwayScore": "1", "idEvent": "2"},
    "Arsenal", "Chelsea",
) is None

# Unplayed matches or (no score) are dropped
assert match_row(
    {"strLeague": "English Premier League", "strHomeTeam": "Arsenal",
     "strAwayTeam": "Chelsea", "intHomeScore": None, "intAwayScore": None, "idEvent": "3"},
    "Arsenal", "Chelsea",
) is None

print("all good")