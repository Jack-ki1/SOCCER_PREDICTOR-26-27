"""
2026/27 Premier League season constants.

Team ratings here are illustrative model inputs informed by real
end-of-2025/26 storylines (Arsenal champions, Man City's post-Guardiola
reset under Maresca, Man Utd's Carrick era, three promoted sides) — not
scraped provider data. Once data/soccerdata_integration.py +
scripts/fetch_historical_data.py are wired up, engine/probability_model.py
should fit these from real results instead of using the numbers below.
That's the single highest-leverage accuracy improvement available — see
the build plan §Phase 2.

Matchweek 1 fixtures ARE real (the confirmed 2026/27 opening round,
released 19 Jun 2026; season opens Fri 21 Aug 2026). Everything else is
generated — see data/calendar_2026.py.
"""
from datetime import datetime, timezone

SEASON = "2026-27"

# Friday 21 August 2026, 20:00 BST (19:00 UTC) — Arsenal vs Coventry City.
KICKOFF_UTC = datetime(2026, 8, 21, 19, 0, tzinfo=timezone.utc)

SEASON_ROUNDS = 38

# Order matters: it seeds the round-robin generator (data/calendar_2026.py)
# so Matchweek 1 reproduces the real confirmed opening fixtures.
SCHEDULE_ORDER = [
    "ars", "mci", "hul", "new", "bha", "bre", "ful", "nfo", "eve", "ips",
    "sun", "cry", "lee", "che", "tot", "avl", "liv", "mun", "bou", "cov",
]

# id, name, short code, hex colour (approximate club identity, decorative
# only), attack/defense/home-advantage rating (0-100 illustrative scale),
# discipline (flavour stat, lightly used), last-5 form (None = promoted /
# no top-flight form yet), and a one-line tag.
TEAMS = [
    {"id": "ars", "name": "Arsenal", "short": "ARS", "color": "#EF0107",
     "attack": 90, "defense": 91, "home_adv": 68, "discipline": 74,
     "form": ["W", "W", "D", "W", "W"], "tag": "Defending champions — first title in 22 years"},
    {"id": "mci", "name": "Manchester City", "short": "MCI", "color": "#6CABDD",
     "attack": 87, "defense": 79, "home_adv": 66, "discipline": 70,
     "form": ["W", "D", "W", "L", "W"], "tag": "New era: Enzo Maresca succeeds Guardiola"},
    {"id": "hul", "name": "Hull City", "short": "HUL", "color": "#F18A00",
     "attack": 50, "defense": 49, "home_adv": 47, "discipline": 63,
     "form": None, "tag": "Promoted from the Championship"},
    {"id": "new", "name": "Newcastle United", "short": "NEW", "color": "#241F20",
     "attack": 78, "defense": 76, "home_adv": 62, "discipline": 71,
     "form": ["W", "D", "W", "W", "L"], "tag": "Back in Europe"},
    {"id": "bha", "name": "Brighton & Hove Albion", "short": "BHA", "color": "#0057B8",
     "attack": 72, "defense": 66, "home_adv": 55, "discipline": 72,
     "form": ["W", "D", "L", "W", "D"], "tag": "Model recruitment engine"},
    {"id": "bre", "name": "Brentford", "short": "BRE", "color": "#E30613",
     "attack": 68, "defense": 64, "home_adv": 53, "discipline": 67,
     "form": ["L", "W", "D", "W", "L"], "tag": "Set-piece specialists"},
    {"id": "ful", "name": "Fulham", "short": "FUL", "color": "#1A1A1A",
     "attack": 65, "defense": 66, "home_adv": 52, "discipline": 71,
     "form": ["D", "L", "W", "D", "W"], "tag": "Steady mid-table"},
    {"id": "nfo", "name": "Nottingham Forest", "short": "NFO", "color": "#DD0000",
     "attack": 67, "defense": 63, "home_adv": 54, "discipline": 62,
     "form": ["W", "L", "D", "W", "D"], "tag": "City Ground fortress"},
    {"id": "eve", "name": "Everton", "short": "EVE", "color": "#003399",
     "attack": 60, "defense": 68, "home_adv": 57, "discipline": 75,
     "form": ["L", "D", "D", "W", "L"], "tag": "New stadium era"},
    {"id": "ips", "name": "Ipswich Town", "short": "IPS", "color": "#0044A9",
     "attack": 54, "defense": 52, "home_adv": 49, "discipline": 66,
     "form": None, "tag": "Promoted from the Championship"},
    {"id": "sun", "name": "Sunderland", "short": "SUN", "color": "#EB172B",
     "attack": 58, "defense": 56, "home_adv": 50, "discipline": 64,
     "form": ["L", "D", "W", "L", "D"], "tag": "Second season back in the top flight"},
    {"id": "cry", "name": "Crystal Palace", "short": "CRY", "color": "#1B458F",
     "attack": 66, "defense": 70, "home_adv": 56, "discipline": 73,
     "form": ["D", "D", "W", "L", "D"], "tag": "Cup pedigree, league consistency"},
    {"id": "lee", "name": "Leeds United", "short": "LEE", "color": "#1D428A",
     "attack": 61, "defense": 58, "home_adv": 52, "discipline": 61,
     "form": ["D", "L", "L", "W", "D"], "tag": "Elland Road roars back"},
    {"id": "che", "name": "Chelsea", "short": "CHE", "color": "#034694",
     "attack": 79, "defense": 72, "home_adv": 60, "discipline": 66,
     "form": ["D", "W", "W", "L", "W"], "tag": "Young squad, new manager"},
    {"id": "tot", "name": "Tottenham Hotspur", "short": "TOT", "color": "#132257",
     "attack": 77, "defense": 67, "home_adv": 58, "discipline": 60,
     "form": ["W", "L", "W", "D", "W"], "tag": "European pedigree"},
    {"id": "avl", "name": "Aston Villa", "short": "AVL", "color": "#670E36",
     "attack": 74, "defense": 73, "home_adv": 60, "discipline": 69,
     "form": ["D", "W", "W", "L", "D"], "tag": "Europa League champions"},
    {"id": "liv", "name": "Liverpool", "short": "LIV", "color": "#C8102E",
     "attack": 85, "defense": 78, "home_adv": 64, "discipline": 68,
     "form": ["W", "W", "L", "W", "D"], "tag": "Arne Slot, year three"},
    {"id": "mun", "name": "Manchester United", "short": "MUN", "color": "#DA291C",
     "attack": 76, "defense": 70, "home_adv": 62, "discipline": 65,
     "form": ["L", "W", "D", "W", "W"], "tag": "Michael Carrick era begins"},
    {"id": "bou", "name": "AFC Bournemouth", "short": "BOU", "color": "#DA020E",
     "attack": 70, "defense": 65, "home_adv": 54, "discipline": 68,
     "form": ["W", "W", "D", "L", "W"], "tag": "Iraola's counter-press"},
    {"id": "cov", "name": "Coventry City", "short": "COV", "color": "#78C6E8",
     "attack": 52, "defense": 50, "home_adv": 48, "discipline": 65,
     "form": None, "tag": "Promoted — first top flight game in 25 years"},
]

TEAMS_BY_ID = {t["id"]: t for t in TEAMS}

# The real confirmed Matchweek 1 fixtures (home, away) — everything else in
# the season is generated by data/calendar_2026.py's round-robin.
REAL_MATCHWEEK_1 = [
    ("ars", "cov"), ("mci", "bou"), ("hul", "mun"), ("new", "liv"),
    ("bha", "avl"), ("bre", "tot"), ("ful", "che"), ("nfo", "lee"),
    ("eve", "cry"), ("ips", "sun"),
]

# Clubs playing in Europe this season (9 total per the confirmed
# competition draw: 5 Champions League, 3 Europa League, 1 Conference
# League) — feeds engine/fatigue_model.py. Specific competition per club
# isn't confirmed here; treat this set as "has additional midweek fixtures."
EUROPEAN_CLUB_IDS: set[str] = set()  # populate once the specific 9 clubs are confirmed/verified
