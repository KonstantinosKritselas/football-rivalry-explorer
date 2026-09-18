"""
Head-to-Head Explorer - Group Assignment, From Data to App
Data: TheSportsDB free API (https://www.thesportsdb.com/api.php)
Run it with:   streamlit run app.py
"""
import time
from datetime import date

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3/"
SEARCH_EVENTS_URL = BASE_URL + "searchevents.php"
SEARCH_TEAMS_URL = BASE_URL + "searchteams.php"
N_SEASONS = 10
REQUEST_DELAY = 0.25  # be polite to the free tier - it 429s on a tight burst ) 

# Curated list for the team pickers - avoids hitting TheSportsDB just to list
# teams, and its free tier has no "all teams" endpoint anyway. after that you have to pay or 
# hope that the team name you typed is in their database. sorted for convenience.
TEAMS = sorted([
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Liverpool",
    "Manchester City", "Manchester United", "Newcastle United",
    "Nottingham Forest", "Tottenham Hotspur", "West Ham United",
    "Wolverhampton Wanderers",
    "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla",
    "Real Sociedad", "Real Betis", "Valencia", "Villarreal", "Athletic Bilbao",
    "Juventus", "Inter Milan", "AC Milan", "Napoli", "AS Roma", "Lazio",
    "Atalanta", "Fiorentina",
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen",
    "Borussia Monchengladbach", "Eintracht Frankfurt", "VfB Stuttgart",
    "Werder Bremen",
    "Paris Saint-Germain", "Marseille", "Lyon", "Monaco", "Lille", "Nice",
    "Rennes",
    "Ajax", "PSV Eindhoven", "Feyenoord", "Porto", "Benfica", "Sporting CP",
    "Celtic", "Rangers",
])


#  pure helpers used by test_app.py 
def season_list(n=N_SEASONS, today=None):
    """Last n football seasons, oldest first, ending with the season in progress
    today (season runs roughly Jul-Jun)."""
    today = today or date.today()
    start_year = today.year if today.month >= 7 else today.year - 1
    return [f"{y}-{y + 1}" for y in range(start_year - n + 1, start_year + 1)]


def match_row(event, team_a, team_b):
    """Turn one raw TheSportsDB event into a clean row, or None if it can't be
    used (no final score, or a friendly)."""
    league = event.get("strLeague") or ""
    if "friendly" in league.lower():
        return None
    home, away = event.get("strHomeTeam"), event.get("strAwayTeam")
    try:
        home_score = int(event["intHomeScore"])
        away_score = int(event["intAwayScore"])
    except (TypeError, ValueError, KeyError):
        return None  # not played yet or no score on record

    if home == team_a:
        a_goals, b_goals = home_score, away_score
    elif home == team_b:
        a_goals, b_goals = away_score, home_score
    else:
        return None  # safety - it should not happen  

    winner = "Draw" if a_goals == b_goals else (team_a if a_goals > b_goals else team_b)
    return {
        "idEvent": event.get("idEvent"),
        "date": event.get("dateEvent"),
        "season": event.get("strSeason"),
        "competition": league,
        "home_team": home,
        "away_team": away,
        f"{team_a}_goals": a_goals,
        f"{team_b}_goals": b_goals,
        "total_goals": a_goals + b_goals,
        "winner": winner,
    }


#  API calls
def _get(url, params, retries=3):
    """GET with light pacing + backoff retries on a 429 (the free tier rate-limits bursts)."""
    for attempt in range(retries):
        time.sleep(REQUEST_DELAY)
        try:
            r = requests.get(url, params=params, timeout=8)
        except requests.exceptions.RequestException:
            return None
        if r.status_code == 429:
            time.sleep(2 * (attempt + 1))
            continue
        try:
            r.raise_for_status()
        except requests.exceptions.RequestException:
            return None
        return r.json()
    return None


@st.cache_data(show_spinner=False)
def resolve_team(name):
    """Look up a team's canonical TheSportsDB name + short name. Returns None
    if it isn't a known football team."""
    data = _get(SEARCH_TEAMS_URL, {"t": name})
    if data is None:
        return "error"
    teams = [t for t in (data.get("teams") or []) if t.get("strSport") == "Soccer"]
    if not teams:
        return None
    t = teams[0]
    return {"strTeam": t["strTeam"], "strTeamShort": t.get("strTeamShort")}


def _search_events(name_a, name_b, seasons, _progress=None):
    events = {}
    failures = 0
    attempts = 0
    for i, season in enumerate(seasons):
        if _progress is not None:
            _progress.progress(i / len(seasons), text=f"Checking {season}... ({i}/{len(seasons)} seasons)")
        for e_name in (f"{name_a} vs {name_b}", f"{name_b} vs {name_a}"):
            attempts += 1
            data = _get(SEARCH_EVENTS_URL, {"e": e_name, "s": season})
            if data is None:
                failures += 1
                continue
            for ev in (data.get("event") or []):
                events[ev["idEvent"]] = ev
    if _progress is not None:
        _progress.progress(1.0, text="Done.")
    return events, failures, attempts


def _pick_name_variant(team_a, team_b, team_a_short, team_b_short, probe_season):
    """TheSportsDB stores some fixtures under each club's short name (e.g. 'Man
    City') instead of the full name. Probe one season to see which variant this
    pair uses, instead of querying every season twice as often."""
    events, _, _ = _search_events(team_a, team_b, [probe_season])
    if events:
        return team_a, team_b
    has_short = team_a_short and team_b_short and (team_a_short, team_b_short) != (team_a, team_b)
    if has_short:
        events, _, _ = _search_events(team_a_short, team_b_short, [probe_season])
        if events:
            return team_a_short, team_b_short
    return team_a, team_b


@st.cache_data(show_spinner="Fetching matches from TheSportsDB...")
def fetch_matches(team_a, team_b, team_a_short, team_b_short, seasons, _progress=None):
    if not seasons:
        return [], False
    name_a, name_b = _pick_name_variant(team_a, team_b, team_a_short, team_b_short, seasons[-1])
    events, failures, attempts = _search_events(name_a, name_b, seasons, _progress)
    api_down = attempts > 0 and failures == attempts
    return list(events.values()), api_down


# --- UI -----------------------------------------------------------------
def main():
    st.set_page_config(page_title="Football Rivalry Explorer", layout="wide")
    st.title("Football Rivalry Explorer")
    st.caption("Has the rivalry really shifted?")
    st.caption("Compare goals, wins and match intensity across the last decade.")

    seasons = season_list()

    with st.sidebar:
        st.header("Controls")
        team_a_input = st.selectbox("Team A", options=TEAMS, index=TEAMS.index("Arsenal"))
        team_b_input = st.selectbox("Team B", options=TEAMS, index=TEAMS.index("Chelsea"))
        start_season, end_season = st.select_slider(
            "Season range",
            options=seasons,
            value=(seasons[0], seasons[-1]),
        )

    if team_a_input == team_b_input:
        st.info("Pick two different teams in the sidebar.")
        st.stop()

    team_a_info = resolve_team(team_a_input.strip())
    team_b_info = resolve_team(team_b_input.strip())

    if team_a_info == "error" or team_b_info == "error":
        st.error("Could not reach TheSportsDB right now. Please try again in a moment.")
        st.stop()
    if team_a_info is None:
        st.error(f"Could not find a football team named '{team_a_input}' on TheSportsDB.")
        st.stop()
    if team_b_info is None:
        st.error(f"Could not find a football team named '{team_b_input}' on TheSportsDB.")
        st.stop()

    team_a = team_a_info["strTeam"]
    team_b = team_b_info["strTeam"]
    selected_seasons = tuple(s for s in seasons if start_season <= s <= end_season)

    progress = st.progress(0, text="Starting...")
    t0 = time.time()
    raw_events, api_down = fetch_matches(
        team_a, team_b, team_a_info["strTeamShort"], team_b_info["strTeamShort"], selected_seasons,
        _progress=progress,
    )
    fetch_seconds = time.time() - t0
    progress.empty()

    if api_down:
        st.error("TheSportsDB appears to be unavailable right now. Please try again shortly.")
        st.stop()

    rows = [r for r in (match_row(ev, team_a, team_b) for ev in raw_events) if r is not None]
    df = pd.DataFrame(rows).drop_duplicates(subset="idEvent").sort_values("date") if rows else pd.DataFrame()

    if df.empty:
        st.warning(
            f"No completed, non-friendly matches found between {team_a} and {team_b} "
            f"for seasons {start_season}-{end_season}."
        )
        st.stop()

    # METRICS
    st.caption(
        "Card statistics aren't available on TheSportsDB's free tier, so this analysis "
        "covers goals and results only (average goals per match stands in for intensity)."
    )

    wins_a = int((df["winner"] == team_a).sum())
    wins_b = int((df["winner"] == team_b).sum())
    draws = int((df["winner"] == "Draw").sum())
    goals_a = int(df[f"{team_a}_goals"].sum())
    goals_b = int(df[f"{team_b}_goals"].sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Matches analysed", len(df))
    c2.metric("Avg. goals / match", f"{df['total_goals'].mean():.2f}")
    c3.metric("Draws", draws)
    c4.metric(f"{team_a} wins", wins_a, delta=f"{goals_a} goals scored", delta_color="off")
    c5.metric(f"{team_b} wins", wins_b, delta=f"{goals_b} goals scored", delta_color="off")
    st.caption(f"Data fetched from TheSportsDB in {fetch_seconds:.1f}s (instant on repeat visits - cached).")

    # visualisation: goals per season. shows the intensity
    season_agg = (
        df.groupby("season")
        .agg(
            **{
                f"{team_a}": (f"{team_a}_goals", "sum"),
                f"{team_b}": (f"{team_b}_goals", "sum"),
                "matches": ("idEvent", "count"),
            }
        )
        .reset_index()
    )
    season_agg["avg_goals_per_match"] = (season_agg[team_a] + season_agg[team_b]) / season_agg["matches"]

    long = season_agg.melt(
        id_vars=["season", "matches", "avg_goals_per_match"],
        value_vars=[team_a, team_b],
        var_name="team",
        value_name="goals",
    )

    fig = px.bar(
        long,
        x="season",
        y="goals",
        color="team",
        barmode="group",
        text_auto=True,
        category_orders={"season": [s for s in seasons if s in season_agg["season"].values]},
        hover_data={"matches": True, "avg_goals_per_match": ":.2f", "team": False},
        labels={"goals": "Goals scored", "season": "Season"},
    )
    fig.update_layout(height=440, margin=dict(t=10, b=0), legend_title_text="")
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig)
    st.caption(
        "Goals scored by season (bars, labelled - a 0 means that team was shut out that "
        "season, not missing data). Hover a bar to see matches played and average goals "
        "per match that season - our proxy for how open/intense the fixture was."
    )

    st.caption(
        "Limitations: friendly matches are excluded; coverage depends on what TheSportsDB "
        "has recorded, so older or lower-profile fixtures may be missing."
    )

    st.download_button(
        "Download match data (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{team_a}_vs_{team_b}.csv".replace(" ", "_"),
        mime="text/csv",
    )


if __name__ == "__main__":
    main()