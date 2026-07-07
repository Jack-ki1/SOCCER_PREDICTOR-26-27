"""Data export routes."""

from flask import Blueprint, request, send_file, jsonify, render_template  # ← FIXED: Added render_template
import io

from src.soccer_predictor.services.export_service import get_export_service
from src.soccer_predictor.services.prediction_service import get_prediction_service

bp = Blueprint("export", __name__)
export_service = get_export_service()
prediction_service = get_prediction_service()


@bp.route("/")
def export_page():
    """Export interface."""
    return render_template("export.html")


@bp.route("/predictions", methods=["POST"])
def export_predictions():
    """Export predictions in requested format."""
    data = request.get_json() or {}
    match_ids = data.get("match_ids", [])
    format_type = data.get("format", "csv")

    if not match_ids:
        return jsonify({"error": "No match_ids provided"}), 400

    predictions = prediction_service.predict_batch(match_ids)

    if format_type == "csv":
        content = export_service.export_predictions_csv(predictions)
        return send_file(
            io.BytesIO(content),
            mimetype="text/csv",
            as_attachment=True,
            download_name="predictions_2026-2027.csv",
        )
    elif format_type == "json":
        content = export_service.export_predictions_json(predictions)
        return send_file(
            io.BytesIO(content.encode()),
            mimetype="application/json",
            as_attachment=True,
            download_name="predictions_2026-2027.json",
        )
    elif format_type == "excel":
        content = export_service.export_predictions_excel(predictions)
        return send_file(
            io.BytesIO(content),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="predictions_2026-2027.xlsx",
        )

    return jsonify({"error": "Unsupported format"}), 400