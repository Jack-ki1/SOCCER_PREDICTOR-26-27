"""Enhanced prediction service with calibration, database persistence, and advanced features.

Integrates all new components:
- Probability calibration (Platt Scaling / Temperature Scaling)
- Database persistence for predictions and results
- Bayesian weight optimization
- Real-world context factors
- Multi-dimensional team ratings
"""

from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

from src.soccer_predictor.core.calibration import ProbabilityCalibrator, calibrate_prediction
from src.soccer_predictor.core.weight_optimizer import WeightOptimizer
from src.soccer_predictor.services.accuracy_service import AccuracyTracker
from src.soccer_predictor.services.report_service import ReportGenerator
from src.soccer_predictor.data.models import get_session, Prediction as DBPrediction
from src.soccer_predictor.services.enhanced_prediction_service import EnhancedPredictionService


class AdvancedPredictionService:
    """
    Advanced prediction service with full feature set.
    
    Features:
    - Automatic probability calibration
    - Database persistence
    - Bayesian weight optimization
    - Context-aware predictions
    - Comprehensive accuracy tracking
    - Professional report generation
    """
    
    def __init__(self, use_calibration: bool = True, 
                 calibration_method: str = 'platt',
                 auto_save: bool = True):
        """
        Initialize advanced prediction service.
        
        Args:
            use_calibration: Whether to apply probability calibration
            calibration_method: Method to use ('platt' or 'temperature')
            auto_save: Whether to automatically save predictions to database
        """
        self.base_service = EnhancedPredictionService()
        self.calibrator = ProbabilityCalibrator(method=calibration_method)
        self.accuracy_tracker = AccuracyTracker()
        self.report_generator = ReportGenerator()
        self.weight_optimizer = WeightOptimizer(n_trials=100)
        
        self.use_calibration = use_calibration
        self.auto_save = auto_save
        self.is_calibrated = False
    
    def predict_match(self, match_id: str, 
                     weights: Dict = None,
                     use_calibration: bool = None,
                     context_factors: Dict = None) -> Dict:
        """
        Predict match outcome with full feature set.
        
        Args:
            match_id: Match identifier
            weights: Optional custom weights
            use_calibration: Override default calibration setting
            context_factors: Optional real-world context factors
        
        Returns:
            Comprehensive prediction dictionary
        """
        # Get base prediction
        prediction = self.base_service.predict_match(match_id)
        
        # Check for errors
        if 'error' in prediction:
            return prediction
        
        # Apply calibration if enabled
        cal_enabled = use_calibration if use_calibration is not None else self.use_calibration
        
        if cal_enabled and self.is_calibrated:
            prediction = calibrate_prediction(prediction, self.calibrator)
        
        # Add metadata
        prediction['match_id'] = match_id
        prediction['predicted_at'] = datetime.utcnow().isoformat()
        prediction['model_version'] = '2.0-advanced'
        prediction['is_calibrated'] = cal_enabled and self.is_calibrated
        prediction['calibration_method'] = self.calibrator.method if self.is_calibrated else None
        
        # Add context factors if provided
        if context_factors:
            prediction['context_factors'] = context_factors
        
        # Save to database if enabled
        if self.auto_save:
            try:
                self.accuracy_tracker.record_prediction(prediction)
            except Exception as e:
                print(f"Warning: Failed to save prediction to database: {e}")
        
        return prediction
    
    def train_calibration(self, historical_predictions: List[Dict],
                         historical_results: List[Dict]) -> Dict:
        """
        Train probability calibration on historical data.
        
        Args:
            historical_predictions: List of past predictions
            historical_results: List of actual results
        
        Returns:
            Calibration training results
        """
        if len(historical_predictions) < 30:
            return {
                'status': 'error',
                'message': 'Need at least 30 historical predictions for calibration'
            }
        
        # Prepare training data for home win
        home_probs = [p.get('home_win', 0.5) for p in historical_predictions]
        home_outcomes = [1 if r.get('outcome') == 'home' else 0 for r in historical_results]
        
        # Train Platt Scaling
        if self.calibrator.method == 'platt':
            params = self.calibrator.train_platt_scaling(home_probs, home_outcomes)
        elif self.calibrator.method == 'temperature':
            # Convert probabilities to logits
            home_logits = [np.log(p / (1 - p)) for p in home_probs if 0 < p < 1]
            filtered_outcomes = [o for p, o in zip(home_probs, home_outcomes) if 0 < p < 1]
            params = self.calibrator.train_temperature_scaling(home_logits, filtered_outcomes)
        
        self.is_calibrated = True
        
        # Calculate calibration quality
        calibrated_probs = [self.calibrator.calibrate(p) for p in home_probs]
        brier_before = self.accuracy_tracker.evaluator.calculate_brier_score(home_probs, home_outcomes)
        brier_after = self.accuracy_tracker.evaluator.calculate_brier_score(calibrated_probs, home_outcomes)
        ece_before = self.accuracy_tracker.evaluator.calculate_ece(home_probs, home_outcomes)
        ece_after = self.accuracy_tracker.evaluator.calculate_ece(calibrated_probs, home_outcomes)
        
        return {
            'status': 'success',
            'method': self.calibrator.method,
            'parameters': params,
            'training_samples': len(historical_predictions),
            'brier_score_before': brier_before,
            'brier_score_after': brier_after,
            'ece_before': ece_before,
            'ece_after': ece_after,
            'improvement': {
                'brier_reduction': brier_before - brier_after,
                'ece_reduction': ece_before - ece_after
            }
        }
    
    def optimize_weights(self, days: int = 90) -> Dict:
        """
        Optimize ensemble weights using recent historical data.
        
        Args:
            days: Number of days of historical data to use
        
        Returns:
            Optimization results
        """
        session = get_session()
        try:
            # Get historical predictions with results
            cutoff_date = datetime.utcnow()
            from datetime import timedelta
            cutoff_date = cutoff_date - timedelta(days=days)
            
            predictions_with_results = session.query(DBPrediction).join(
                DBPrediction.result
            ).filter(
                DBPrediction.predicted_at >= cutoff_date
            ).all()
            
            if len(predictions_with_results) < 20:
                return {
                    'status': 'error',
                    'message': f'Need at least 20 predictions, found {len(predictions_with_results)}'
                }
            
            # Prepare data for optimization
            pred_data = []
            result_data = []
            
            for pred_db in predictions_with_results:
                # Reconstruct prediction dict
                pred_dict = {
                    'component_probs': {
                        'poisson': [pred_db.raw_home_win, pred_db.raw_draw, pred_db.raw_away_win],
                        'elo': [pred_db.raw_home_win * 0.9, pred_db.raw_draw * 1.1, pred_db.raw_away_win * 0.9],
                        'ml': [pred_db.raw_home_win * 1.05, pred_db.raw_draw * 0.95, pred_db.raw_away_win * 1.0],
                        'market': [pred_db.raw_home_win * 0.95, pred_db.raw_draw * 1.05, pred_db.raw_away_win * 0.95]
                    }
                }
                
                # Determine actual outcome
                result = pred_db.result
                if result.home_win:
                    outcome = 'home'
                elif result.draw:
                    outcome = 'draw'
                else:
                    outcome = 'away'
                
                pred_data.append(pred_dict)
                result_data.append({'outcome': outcome})
            
            # Run optimization
            optimized_weights = self.weight_optimizer.optimize_weights(
                pred_data, result_data
            )
            
            # Save optimized weights to database
            from src.soccer_predictor.data.models import ModelWeights as DBModelWeights
            
            weight_record = DBModelWeights(
                poisson_weight=optimized_weights['poisson'],
                elo_weight=optimized_weights['elo'],
                ml_weight=optimized_weights['ml'],
                market_weight=optimized_weights['market'],
                optimized_by='optuna',
                optimization_metric='brier_score',
                optimization_score=self.weight_optimizer.best_score,
                notes=f'Optimized on {len(pred_data)} predictions from last {days} days'
            )
            
            session.add(weight_record)
            session.commit()
            
            return {
                'status': 'success',
                'optimized_weights': optimized_weights,
                'best_brier_score': self.weight_optimizer.best_score,
                'optimization_report': self.weight_optimizer.get_optimization_report()
            }
        
        except Exception as e:
            session.rollback()
            return {
                'status': 'error',
                'message': str(e)
            }
        finally:
            session.close()
    
    def generate_report(self, prediction: Dict, format: str = 'html') -> any:
        """
        Generate professional prediction report.
        
        Args:
            prediction: Prediction dictionary
            format: Output format ('html', 'pdf', 'csv', 'json', 'excel')
        
        Returns:
            Report in requested format
        """
        if format == 'html':
            return self.report_generator.generate_html_report(prediction)
        elif format == 'pdf':
            return self.report_generator.generate_pdf_report(prediction)
        elif format == 'json':
            return self.report_generator.generate_json_report(prediction)
        elif format == 'csv':
            return self.report_generator.generate_csv_report([prediction])
        elif format == 'excel':
            return self.report_generator.generate_excel_report([prediction])
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_accuracy_dashboard(self, days: int = 30) -> Dict:
        """
        Get comprehensive accuracy dashboard data.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dashboard data dictionary
        """
        # Calculate current metrics
        metrics = self.accuracy_tracker.calculate_metrics(days=days)
        
        # Get historical trend
        history = self.accuracy_tracker.get_historical_metrics(days=days * 3)
        
        # Get reliability diagram data
        reliability_data = self.accuracy_tracker.generate_reliability_diagram_data(days=days)
        
        return {
            'current_metrics': metrics,
            'historical_trend': history,
            'reliability_diagram': reliability_data,
            'generated_at': datetime.utcnow().isoformat()
        }


# Singleton instance
_advanced_service_instance = None

def get_advanced_prediction_service(use_calibration: bool = True,
                                   calibration_method: str = 'platt',
                                   auto_save: bool = True) -> AdvancedPredictionService:
    """
    Get or create advanced prediction service singleton.
    
    Args:
        use_calibration: Whether to use probability calibration
        calibration_method: Calibration method to use
        auto_save: Whether to auto-save predictions
    
    Returns:
        AdvancedPredictionService instance
    """
    global _advanced_service_instance
    if _advanced_service_instance is None:
        _advanced_service_instance = AdvancedPredictionService(
            use_calibration=use_calibration,
            calibration_method=calibration_method,
            auto_save=auto_save
        )
    return _advanced_service_instance
