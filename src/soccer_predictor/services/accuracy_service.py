"""Accuracy tracking and evaluation service.

Tracks prediction accuracy over time, calculates metrics like Brier Score,
Log Loss, and Expected Calibration Error. Generates reliability diagrams.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sklearn.metrics import brier_score_loss, log_loss

from src.soccer_predictor.data.models import (
    Prediction, MatchResult, AccuracyMetric, get_session
)
from src.soccer_predictor.core.calibration import CalibrationEvaluator


class AccuracyTracker:
    """
    Tracks and evaluates prediction accuracy over time.
    
    Calculates comprehensive metrics including:
    - Outcome accuracy (% correct predictions)
    - Brier Score (probability calibration quality)
    - Log Loss (confidence-weighted accuracy)
    - Expected Calibration Error (ECE)
    - Goal prediction errors
    """
    
    def __init__(self):
        """Initialize accuracy tracker."""
        self.evaluator = CalibrationEvaluator()
    
    def record_prediction(self, prediction_data: Dict) -> int:
        """
        Record a new prediction in the database.
        
        Args:
            prediction_data: Dictionary with prediction details
        
        Returns:
            Prediction ID
        """
        session = get_session()
        try:
            prediction = Prediction(
                match_id=prediction_data['match_id'],
                home_team=prediction_data['home_team'],
                away_team=prediction_data['away_team'],
                league=prediction_data.get('league', 'Unknown'),
                match_date=prediction_data.get('match_date', datetime.utcnow()),
                raw_home_win=prediction_data.get('home_win', 0.45),
                raw_draw=prediction_data.get('draw', 0.28),
                raw_away_win=prediction_data.get('away_win', 0.27),
                calibrated_home_win=prediction_data.get('calibrated_home_win'),
                calibrated_draw=prediction_data.get('calibrated_draw'),
                calibrated_away_win=prediction_data.get('calibrated_away_win'),
                is_calibrated=prediction_data.get('is_calibrated', False),
                home_xg=prediction_data.get('home_xg'),
                away_xg=prediction_data.get('away_xg'),
                btts_prob=prediction_data.get('btts'),
                over_25_prob=prediction_data.get('over_25'),
                model_weights=prediction_data.get('model_weights'),
                model_version=prediction_data.get('model_version', '1.0'),
                simulation_count=prediction_data.get('simulation_count', 50000)
            )
            
            session.add(prediction)
            session.commit()
            
            return prediction.id
        
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def record_result(self, result_data: Dict) -> int:
        """
        Record actual match result.
        
        Args:
            result_data: Dictionary with match result
        
        Returns:
            Result ID
        """
        session = get_session()
        try:
            result = MatchResult(
                match_id=result_data['match_id'],
                home_goals=result_data['home_goals'],
                away_goals=result_data['away_goals'],
                match_date=result_data.get('match_date', datetime.utcnow())
            )
            
            # Calculate outcomes
            result.calculate_outcomes()
            
            # Link to prediction if exists
            prediction = session.query(Prediction).filter_by(
                match_id=result_data['match_id']
            ).first()
            
            if prediction:
                result.prediction_id = prediction.id
            
            session.add(result)
            session.commit()
            
            return result.id
        
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def calculate_metrics(self, days: int = 30) -> Dict:
        """
        Calculate accuracy metrics for recent predictions.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dictionary with accuracy metrics
        """
        session = get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get predictions with results
            predictions_with_results = session.query(Prediction).join(
                MatchResult
            ).filter(
                Prediction.predicted_at >= cutoff_date
            ).all()
            
            if not predictions_with_results:
                return self._empty_metrics()
            
            # Calculate metrics
            metrics = self._compute_metrics(predictions_with_results)
            
            # Save to database
            metric_record = AccuracyMetric(
                metric_date=datetime.utcnow(),
                period_type='daily',
                **metrics
            )
            session.add(metric_record)
            session.commit()
            
            return metrics
        
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _compute_metrics(self, predictions: List[Prediction]) -> Dict:
        """
        Compute comprehensive accuracy metrics.
        
        Args:
            predictions: List of Prediction objects with results
        
        Returns:
            Dictionary with all metrics
        """
        total = len(predictions)
        matched = sum(1 for p in predictions if p.result is not None)
        
        if matched == 0:
            return self._empty_metrics()
        
        # Prepare data for calculations
        pred_probs = []
        outcomes = []
        home_pred_errors = []
        away_pred_errors = []
        score_correct = 0
        btts_correct = 0
        over_25_correct = 0
        
        for pred in predictions:
            if pred.result is None:
                continue
            
            # Determine predicted outcome (highest probability)
            if pred.is_calibrated:
                pred_home = pred.calibrated_home_win
                pred_draw = pred.calibrated_draw
                pred_away = pred.calibrated_away_win
            else:
                pred_home = pred.raw_home_win
                pred_draw = pred.raw_draw
                pred_away = pred.raw_away_win
            
            # Actual outcome
            result = pred.result
            if result.home_win:
                actual_outcome = 0  # Index for home win
                outcome_vec = [1, 0, 0]
            elif result.draw:
                actual_outcome = 1  # Index for draw
                outcome_vec = [0, 1, 0]
            else:
                actual_outcome = 2  # Index for away win
                outcome_vec = [0, 0, 1]
            
            pred_probs.append([pred_home, pred_draw, pred_away])
            outcomes.append(outcome_vec)
            
            # Goal prediction errors
            if pred.home_xg and pred.away_xg:
                home_error = abs(pred.home_xg - result.home_goals)
                away_error = abs(pred.away_xg - result.away_goals)
                home_pred_errors.append(home_error)
                away_pred_errors.append(away_error)
                
                # Exact score accuracy
                pred_home_goals = round(pred.home_xg)
                pred_away_goals = round(pred.away_xg)
                if pred_home_goals == result.home_goals and pred_away_goals == result.away_goals:
                    score_correct += 1
            
            # BTTS accuracy
            if pred.btts_prob is not None:
                actual_btts = 1 if (result.home_goals > 0 and result.away_goals > 0) else 0
                pred_btts = 1 if pred.btts_prob > 0.5 else 0
                if pred_btts == actual_btts:
                    btts_correct += 1
            
            # Over 2.5 accuracy
            if pred.over_25_prob is not None:
                actual_over_25 = 1 if (result.home_goals + result.away_goals) > 2.5 else 0
                pred_over_25 = 1 if pred.over_25_prob > 0.5 else 0
                if pred_over_25 == actual_over_25:
                    over_25_correct += 1
        
        # Calculate outcome accuracy
        correct_predictions = 0
        for i, probs in enumerate(pred_probs):
            predicted_idx = np.argmax(probs)
            actual_idx = np.argmax(outcomes[i])
            if predicted_idx == actual_idx:
                correct_predictions += 1
        
        outcome_accuracy = correct_predictions / matched if matched > 0 else 0
        exact_score_accuracy = score_correct / matched if matched > 0 else 0
        
        # Calculate Brier Score (multi-class)
        brier_scores = []
        for probs, outcome in zip(pred_probs, outcomes):
            bs = sum((p - o)**2 for p, o in zip(probs, outcome))
            brier_scores.append(bs)
        brier_score = np.mean(brier_scores)
        
        # Calculate Log Loss (for home win only as binary)
        home_probs = [p[0] for p in pred_probs]
        home_outcomes = [o[0] for o in outcomes]
        log_loss_value = self.evaluator.calculate_log_loss(home_probs, home_outcomes)
        
        # Calculate ECE
        ece = self.evaluator.calculate_ece(home_probs, home_outcomes)
        
        # Average goal errors
        avg_home_error = np.mean(home_pred_errors) if home_pred_errors else 0
        avg_away_error = np.mean(away_pred_errors) if away_pred_errors else 0
        
        # Market accuracies
        btts_accuracy = btts_correct / matched if matched > 0 else 0
        over_25_accuracy = over_25_correct / matched if matched > 0 else 0
        
        return {
            'total_predictions': total,
            'matched_predictions': matched,
            'outcome_accuracy': outcome_accuracy,
            'exact_score_accuracy': exact_score_accuracy,
            'brier_score': brier_score,
            'log_loss': log_loss_value,
            'expected_calibration_error': ece,
            'avg_home_goal_error': avg_home_error,
            'avg_away_goal_error': avg_away_error,
            'avg_total_goal_error': (avg_home_error + avg_away_error) / 2,
            'btts_accuracy': btts_accuracy,
            'over_25_accuracy': over_25_accuracy,
            'value_bet_count': 0,  # TODO: Implement value bet tracking
            'value_bet_wins': 0,
            'value_bet_roi': 0.0,
            'trend_indicator': self._determine_trend(brier_score)
        }
    
    def _determine_trend(self, current_brier: float) -> str:
        """
        Determine performance trend based on recent Brier Scores.
        
        Args:
            current_brier: Current Brier Score
        
        Returns:
            Trend indicator string
        """
        session = get_session()
        try:
            # Get last 7 days of metrics
            recent_metrics = session.query(AccuracyMetric).filter_by(
                period_type='daily'
            ).order_by(
                AccuracyMetric.metric_date.desc()
            ).limit(7).all()
            
            if len(recent_metrics) < 3:
                return 'stable'
            
            # Compare recent average to older average
            recent_avg = np.mean([m.brier_score for m in recent_metrics[:3]])
            older_avg = np.mean([m.brier_score for m in recent_metrics[3:]])
            
            if recent_avg < older_avg - 0.01:  # Lower Brier is better
                return 'improving'
            elif recent_avg > older_avg + 0.01:
                return 'declining'
            else:
                return 'stable'
        
        finally:
            session.close()
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics dictionary."""
        return {
            'total_predictions': 0,
            'matched_predictions': 0,
            'outcome_accuracy': 0.0,
            'exact_score_accuracy': 0.0,
            'brier_score': 0.0,
            'log_loss': 0.0,
            'expected_calibration_error': 0.0,
            'avg_home_goal_error': 0.0,
            'avg_away_goal_error': 0.0,
            'avg_total_goal_error': 0.0,
            'btts_accuracy': 0.0,
            'over_25_accuracy': 0.0,
            'value_bet_count': 0,
            'value_bet_wins': 0,
            'value_bet_roi': 0.0,
            'trend_indicator': 'stable'
        }
    
    def get_historical_metrics(self, days: int = 90) -> List[Dict]:
        """
        Get historical accuracy metrics.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of metric dictionaries
        """
        session = get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            metrics = session.query(AccuracyMetric).filter(
                AccuracyMetric.metric_date >= cutoff_date
            ).order_by(
                AccuracyMetric.metric_date.asc()
            ).all()
            
            return [
                {
                    'metric_date': m.metric_date.isoformat(),
                    'outcome_accuracy': m.outcome_accuracy,
                    'brier_score': m.brier_score,
                    'log_loss': m.log_loss,
                    'expected_calibration_error': m.expected_calibration_error,
                    'matched_predictions': m.matched_predictions,
                    'trend_indicator': m.trend_indicator
                }
                for m in metrics
            ]
        
        finally:
            session.close()
    
    def generate_reliability_diagram_data(self, days: int = 90) -> Dict:
        """
        Generate data for reliability diagram visualization.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dictionary with reliability diagram data
        """
        session = get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            predictions = session.query(Prediction).join(
                MatchResult
            ).filter(
                Prediction.predicted_at >= cutoff_date
            ).all()
            
            if not predictions:
                return {'bin_centers': [], 'predicted_probs': [], 'actual_freqs': []}
            
            # Collect probabilities and outcomes
            probs = []
            outcomes = []
            
            for pred in predictions:
                if pred.result is None:
                    continue
                
                # Use home win probability
                prob = pred.calibrated_home_win if pred.is_calibrated else pred.raw_home_win
                outcome = 1 if pred.result.home_win else 0
                
                probs.append(prob)
                outcomes.append(outcome)
            
            # Generate reliability data
            return self.evaluator.generate_reliability_data(probs, outcomes)
        
        finally:
            session.close()
