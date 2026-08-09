"""
Real file-download routes — makes the Reports page's buttons actually work
rather than being UI previews. Registered from dashboard/app.py alongside
the page and API blueprints.
"""
from __future__ import annotations

from flask import Blueprint, Response, request

from reports.csv_excel_report import fixtures_csv, predictions_csv, predictions_xlsx
from reports.pdf_generator import season_report_pdf

downloads_bp = Blueprint("downloads", __name__)


@downloads_bp.get("/download/fixtures.csv")
def download_fixtures_csv():
    return Response(
        fixtures_csv(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=epl-2026-27-fixtures.csv"},
    )


@downloads_bp.get("/download/predictions.csv")
def download_predictions_csv():
    matchweek = request.args.get("matchweek", 1, type=int)
    return Response(
        predictions_csv(matchweek), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=epl-matchweek-{matchweek}-predictions.csv"},
    )


@downloads_bp.get("/download/predictions.xlsx")
def download_predictions_xlsx():
    matchweek = request.args.get("matchweek", 1, type=int)
    return Response(
        predictions_xlsx(matchweek), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=epl-matchweek-{matchweek}-predictions.xlsx"},
    )


@downloads_bp.get("/download/season-report.pdf")
def download_season_report_pdf():
    n_sims = request.args.get("n_sims", 300, type=int)
    n_sims = max(50, min(1000, n_sims))
    return Response(
        season_report_pdf(n_sims), mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=epl-2026-27-season-report.pdf"},
    )
