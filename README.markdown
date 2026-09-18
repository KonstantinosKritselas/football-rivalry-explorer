# Football Rivalry Explorer
  Compares the head to head record of two football teams over the last 10 seasons:
  goals, wins, draws, and how the rivalry's goal output has shifted season by season.

Data: [TheSportsDB](https://www.thesportsdb.com/) free API, via the
[Free Sports API on FreePublicAPIs](https://www.freepublicapis.com/free-sports-api).

## HOW - Run it locally
  1.python -m venv .venv
  2..venv\Scripts\Activate.ps1 # Windows
  3.pip install -r requirements.txt
  4.streamlit run app.py
______________________________

## Target audience
   Our target audience is football fans and people interested in sports data. Instead of looking only at the latest result, our app lets users compare 2 teams across the last decade and see how their rivalry has evolved.

## Known limitations
- **Card statistics aren't available.** Wanted to display cards to give an indicator about
   a fiercest or a more fanatical competition between teams. TheSportsDB's free tier didn't let us.
   Card data required a paid plan.
- **Event search matches by exact name.** TheSportsDB's `searchevents.php` looks
  up the literal stored match title, which sometimes uses a club's short name
  (e.g. "Man City" rather than "Manchester City"). The app probes both forms
  automatically, but an abstract name spelling by mistake may still return nothing.
- **Coverage depends on TheSportsDB's own records** not so important matches for the api or
  older seasons may be missing even when they were played.
- **Free tier rate limit.** The API 429s under a heavy burst of requests, the app
  paces its calls and retries automatically.But a fresh query still takes a few
  seconds.
  If TheSportsDB's shared free quota is temporarily exhausted, the
  app will show a clear "unavailable" message rather than fail silently.
  Tried to make a dynamic api teams list. We could, but the app wpould upload the data slower for the user or the user would top-up the permitted requests quickly than with a static list.



## 4TH PART OF ASSIGNMENT _ Briefly state which AI/tools you used and what you used them for
  We used AI claude code and chat for:
  1. help to fix errors during the creation of the coding
  2. Asked questions about api's endpoints to understand better their usefulness
  3. Find ways of displaying more information (e.g. cards or dynamic list - slower UI)
  4. Asked questions about the speed and the api's limit had and also about the UI work inside the streamlit.
  5. Asked questions about how to display the graph better (e.g. 0 goals = no bar chart for the team that didnt score. Tried to fix it by using visual labels)
  6. Asked it to make the static team list to avoid misspelling 
  7. Find help about the timeout, for making UI better, by reducing the upload speed
  8. Helped by dividing the code in 4 steps and make it more readable for us if we need to change something instead of searching (curated list, api, ui, visualisation)
  9. Did a quick testing before deciding which idea we would work on. To see if our apis display enough and accurate information or we had to pay for more data.


