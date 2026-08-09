"""
CSV / Excel report generation. Used by dashboard/download_routes.py to make
the Reports page's export buttons real (not just a UI preview).
"""
from __future__ import annotations

import csv
import io

import openpyxl

from data.calendar_2026 import get_fixtures
from engine.predictor import get_prediction


def fixtures_csv() -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Matchweek", "Home", "Away", "Confirmed"])
    for f in get_fixtures():
        writer.writerow([f["round"], f["home_name"], f["away_name"], "Yes" if f["is_confirmed"] else "No"])
    return buf.getvalue()


def predictions_csv(matchweek: int, weights: dict | None = None) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Matchweek", "Home", "Away", "P(Home)", "P(Draw)", "P(Away)", "xG Home", "xG Away", "Top Scoreline"])
    for f in get_fixtures(matchweek):
        p = get_prediction(f["home_id"], f["away_id"], weights)
        writer.writerow([
            matchweek, f["home_name"], f["away_name"],
            f"{p.market.p_home*100:.1f}%", f"{p.market.p_draw*100:.1f}%", f"{p.market.p_away*100:.1f}%",
            f"{p.lambda_home:.2f}", f"{p.lambda_away:.2f}", p.market.top_scorelines[0][0],
        ])
    return buf.getvalue()


def predictions_xlsx(matchweek: int, weights: dict | None = None) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Matchweek {matchweek}"
    ws.append(["Home", "Away", "P(Home)", "P(Draw)", "P(Away)", "xG Home", "xG Away"])
    for f in get_fixtures(matchweek):
        p = get_prediction(f["home_id"], f["away_id"], weights)
        ws.append([
            f["home_name"], f["away_name"],
            round(p.market.p_home, 3), round(p.market.p_draw, 3), round(p.market.p_away, 3),
            round(p.lambda_home, 2), round(p.lambda_away, 2),
        ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
