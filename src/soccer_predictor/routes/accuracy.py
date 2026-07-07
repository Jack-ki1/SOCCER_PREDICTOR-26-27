"""Accuracy tracking and performance monitoring routes.

Provides endpoints for viewing prediction accuracy, trends, and model performance.
"""

from flask import Blueprint, jsonify, render_template
from src.soccer_predictor.services.database import get_database

bp = Blueprint('accuracy', __name__, url_prefix='/accuracy')


@bp.route('/')
def accuracy_dashboard():
    """Main accuracy dashboard page."""
    db = get_database()
    
    # Get metrics for different periods
    metrics_7d = db.calculate_accuracy_metrics(days=7)
    metrics_30d = db.calculate_accuracy_metrics(days=30)
    metrics_90d = db.calculate_accuracy_metrics(days=90)
    
    # Get historical trend
    history = db.get_accuracy_history(days=90)
    
    return render_template('accuracy/dashboard.html',
                          metrics_7d=metrics_7d,
                          metrics_30d=metrics_30d,
                          metrics_90d=metrics_90d,
                          history=history)


@bp.route('/api/metrics')
def api_get_metrics():
    """API endpoint for accuracy metrics."""
    days = int(request.args.get('days', 30))
    db = get_database()
    
    metrics = db.calculate_accuracy_metrics(days=days)
    return jsonify(metrics)


@bp.route('/api/history')
def api_get_history():
    """API endpoint for historical accuracy data."""
    days = int(request.args.get('days', 90))
    db = get_database()
    
    history = db.get_accuracy_history(days=days)
    return jsonify(history)


@bp.route('/api/report')
def api_generate_report():
    """Generate comprehensive performance report."""
    days = int(request.args.get('days', 30))
    db = get_database()
    
    report = db.generate_performance_report(days=days)
    return jsonify(report)


@bp.route('/export/csv')
def export_predictions_csv():
    """Export predictions to CSV."""
    from flask import send_file
    
    days = int(request.args.get('days', 30))
    db = get_database()
    
    filepath = f"data/exports/predictions_{days}d.csv"
    db.export_predictions_to_csv(filepath, days=days)
    
    return send_file(filepath, as_attachment=True)


# Import request at module level
from flask import request
