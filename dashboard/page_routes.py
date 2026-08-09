"""
Server-rendered page routes. Kept deliberately simple (Jinja2 + a little
vanilla JS calling the /api/v1 blueprint for live numbers) — this is not a
reimplementation of the React prototype, it's a working, dependency-light
web UI that ships with this project out of the box. See
EPL_PREDICTOR_2026_BUILD_PLAN.md §8 for why the React dashboard is kept as
a separate, optional frontend rather than rewritten here.
"""
from __future__ import annotations

from flask import Blueprint, render_template

from data.calendar_2026 import get_fixtures, total_matchweeks
from data.team_data import get_all_teams, promoted_teams
from config.constants import KICKOFF_UTC, SEASON

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def homepage():
    return render_template(
        "homepage.html",
        season=SEASON, kickoff=KICKOFF_UTC.isoformat(), team_count=len(get_all_teams()),
        promoted=promoted_teams(), fixture_count=total_matchweeks() * 10,
    )


@pages_bp.get("/dashboard")
def dashboard():
    mw1 = get_fixtures(1)
    return render_template("dashboard.html", mw1=mw1, teams=get_all_teams(), kickoff=KICKOFF_UTC.isoformat())


@pages_bp.get("/table")
def table():
    return render_template("table.html", teams=get_all_teams())


@pages_bp.get("/fixtures")
def fixtures():
    from config.constants import SEASON_ROUNDS
    return render_template("fixtures.html", total_matchweeks=SEASON_ROUNDS)


@pages_bp.get("/h2h")
def h2h():
    return render_template("h2h.html", teams=get_all_teams())


@pages_bp.get("/fpl-lab")
def fpl_lab():
    return render_template("fpl_lab.html", total_matchweeks=total_matchweeks())


@pages_bp.get("/analytics")
def analytics():
    return render_template("analytics.html", teams=get_all_teams())


@pages_bp.get("/settings")
def settings_page():
    from config.feature_weights import DEFAULT_WEIGHTS
    return render_template("settings.html", weights=DEFAULT_WEIGHTS)


@pages_bp.get("/reports")
def reports():
    return render_template("reports.html")


@pages_bp.get("/download")
def download():
    return render_template("download.html")
