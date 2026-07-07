"""Enhanced prediction routes with calibration, optimization, and reports."""

from flask import Blueprint, render_template, jsonify, request, session, send_file
import io

from src.soccer_predictor.services.advanced_prediction_service import get_advanced_prediction_service
from src.soccer_predictor.services.fixture_service import get_fixture_service

bp = Blueprint("advanced_predictions", __name__)
advanced_service = get_advanced_prediction_service()
fixture_service = get_fixture_service()


@bp.route("/predict/<match_id>")
def advanced_match_prediction(match_id: str):
    """Get advanced prediction with calibration and context."""
    if request.headers.get("Accept") == "application/json":
        # Get optional parameters
        use_calibration = request.args.get('calibrate', 'true').lower() == 'true'
        
        # Collect context factors from query params
        context_factors = {}
        if request.args.get('weather'):
            context_factors['weather'] = request.args.get('weather')
        if request.args.get('is_derby'):
            context_factors['is_derby'] = request.args.get('is_derby').lower() == 'true'
        
        result = advanced_service.predict_match(
            match_id,
            use_calibration=use_calibration,
            context_factors=context_factors if context_factors else None
        )
        return jsonify(result)
    
    # HTML page - redirect to standard prediction page for now
    return render_template("predictions.html", error="Advanced view coming soon")


@bp.route("/calibrate/train", methods=["POST"])
def train_calibration():
    """Train probability calibration on historical data."""
    try:
        # In production, this would fetch from database
        # For now, return status
        result = {
            'status': 'info',
            'message': 'Calibration training requires historical data. Implement data collection first.'
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route("/optimize/weights", methods=["POST"])
def optimize_weights():
    """Optimize ensemble weights using Bayesian optimization."""
    try:
        days = request.json.get('days', 90) if request.json else 90
        
        result = advanced_service.optimize_weights(days=days)
        
        if result['status'] == 'success':
            # Update session weights
            session['ensemble_weights'] = result['optimized_weights']
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route("/report/<match_id>/<format>")
def download_report(match_id: str, format: str):
    """Download prediction report in specified format."""
    try:
        # Get prediction
        prediction = advanced_service.predict_match(match_id)
        
        if 'error' in prediction:
            return jsonify(prediction), 404
        
        # Generate report
        if format == 'html':
            report_content = advanced_service.generate_report(prediction, 'html')
            return send_file(
                io.BytesIO(report_content.encode()),
                mimetype='text/html',
                as_attachment=True,
                download_name=f'prediction_{match_id}.html'
            )
        elif format == 'pdf':
            pdf_bytes = advanced_service.generate_report(prediction, 'pdf')
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'prediction_{match_id}.pdf'
            )
        elif format == 'json':
            json_content = advanced_service.generate_report(prediction, 'json')
            return send_file(
                io.BytesIO(json_content.encode()),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'prediction_{match_id}.json'
            )
        elif format == 'csv':
            csv_content = advanced_service.generate_report(prediction, 'csv')
            return send_file(
                io.BytesIO(csv_content.encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'prediction_{match_id}.csv'
            )
        else:
            return jsonify({'error': f'Unsupported format: {format}'}), 400
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route("/accuracy/dashboard")
def accuracy_dashboard():
    """Get accuracy dashboard data."""
    try:
        days = request.args.get('days', 30, type=int)
        dashboard_data = advanced_service.get_accuracy_dashboard(days=days)
        return jsonify(dashboard_data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route("/accuracy/metrics")
def get_accuracy_metrics():
    """Get current accuracy metrics."""
    try:
        days = request.args.get('days', 30, type=int)
        metrics = advanced_service.accuracy_tracker.calculate_metrics(days=days)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route("/accuracy/history")
def get_accuracy_history():
    """Get historical accuracy metrics."""
    try:
        days = request.args.get('days', 90, type=int)
        history = advanced_service.accuracy_tracker.get_historical_metrics(days=days)
        return jsonify(history)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route("/reliability-diagram")
def get_reliability_diagram():
    """Get reliability diagram data for calibration visualization."""
    try:
        days = request.args.get('days', 90, type=int)
        data = advanced_service.accuracy_tracker.generate_reliability_diagram_data(days=days)
        return jsonify(data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
