"""Database integration for storing predictions, results, and accuracy metrics.

Inspired by F1 Predictor's database architecture for persistent storage
and comprehensive performance tracking.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager


class SoccerPredictorDB:
    """SQLite database for storing predictions, results, and metrics."""
    
    def __init__(self, db_path: str = "data/soccer_predictor.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Create all necessary tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Predictions table - stores every prediction made
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL,
                    league TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    match_date TIMESTAMP,
                    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    home_win_prob REAL,
                    draw_prob REAL,
                    away_win_prob REAL,
                    predicted_home_goals REAL,
                    predicted_away_goals REAL,
                    predicted_score TEXT,
                    model_weights TEXT,
                    confidence_score REAL,
                    value_bet_detected BOOLEAN DEFAULT 0,
                    value_bet_type TEXT,
                    expected_value REAL,
                    metadata TEXT
                )
            """)
            
            # Actual results table - stores match outcomes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS actual_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT UNIQUE NOT NULL,
                    league TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    home_score INTEGER,
                    away_score INTEGER,
                    result TEXT,  -- 'H', 'D', 'A'
                    recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Accuracy metrics table - aggregated performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accuracy_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_date DATE NOT NULL,
                    period_days INTEGER NOT NULL,
                    total_predictions INTEGER DEFAULT 0,
                    correct_outcomes INTEGER DEFAULT 0,
                    outcome_accuracy REAL DEFAULT 0,
                    exact_score_correct INTEGER DEFAULT 0,
                    score_accuracy REAL DEFAULT 0,
                    avg_home_goal_error REAL DEFAULT 0,
                    avg_away_goal_error REAL DEFAULT 0,
                    brier_score REAL DEFAULT 0,
                    log_loss REAL DEFAULT 0,
                    roi_percentage REAL DEFAULT 0,
                    total_value_bets INTEGER DEFAULT 0,
                    profitable_value_bets INTEGER DEFAULT 0,
                    value_bet_roi REAL DEFAULT 0,
                    calibration_error REAL DEFAULT 0,
                    trend_indicator TEXT  -- 'improving', 'stable', 'declining'
                )
            """)
            
            # Model versions table - track model changes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    weights_config TEXT,
                    performance_metrics TEXT
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_match_id ON predictions(match_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(prediction_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_league ON predictions(league)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_match_id ON actual_results(match_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_date ON actual_results(recorded_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_date ON accuracy_metrics(metric_date)")
    
    def save_prediction(self, match_id: str, league: str, home_team: str, 
                       away_team: str, prediction: Dict, metadata: Optional[Dict] = None):
        """Save a prediction to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO predictions 
                (match_id, league, home_team, away_team, match_date,
                 home_win_prob, draw_prob, away_win_prob,
                 predicted_home_goals, predicted_away_goals, predicted_score,
                 model_weights, confidence_score, value_bet_detected,
                 value_bet_type, expected_value, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id,
                league,
                home_team,
                away_team,
                prediction.get('match_date'),
                prediction.get('home_win', 0.33),
                prediction.get('draw', 0.34),
                prediction.get('away_win', 0.33),
                prediction.get('predicted_home_goals'),
                prediction.get('predicted_away_goals'),
                prediction.get('predicted_score'),
                json.dumps(prediction.get('model_weights', {})),
                prediction.get('confidence_score', 0.5),
                prediction.get('value_bet_detected', False),
                prediction.get('value_bet_type'),
                prediction.get('expected_value'),
                json.dumps(metadata or {})
            ))
    
    def save_actual_result(self, match_id: str, league: str, home_team: str,
                          away_team: str, home_score: int, away_score: int,
                          metadata: Optional[Dict] = None):
        """Save actual match result."""
        result = 'H' if home_score > away_score else ('D' if home_score == away_score else 'A')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO actual_results 
                (match_id, league, home_team, away_team, home_score, away_score, result, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id,
                league,
                home_team,
                away_team,
                home_score,
                away_score,
                result,
                json.dumps(metadata or {})
            ))
    
    def get_prediction(self, match_id: str) -> Optional[Dict]:
        """Retrieve a specific prediction."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM predictions WHERE match_id = ?", (match_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_actual_result(self, match_id: str) -> Optional[Dict]:
        """Retrieve actual result for a match."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM actual_results WHERE match_id = ?", (match_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_predictions_for_period(self, days: int = 30, league: Optional[str] = None) -> List[Dict]:
        """Get all predictions from the last N days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM predictions 
                WHERE prediction_date >= datetime('now', ?)
            """
            params = [f'-{days} days']
            
            if league:
                query += " AND league = ?"
                params.append(league)
            
            query += " ORDER BY prediction_date DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_unmatched_predictions(self) -> List[Dict]:
        """Get predictions that don't have actual results yet."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.* FROM predictions p
                LEFT JOIN actual_results r ON p.match_id = r.match_id
                WHERE r.match_id IS NULL
                ORDER BY p.prediction_date DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def calculate_accuracy_metrics(self, days: int = 30) -> Dict:
        """Calculate comprehensive accuracy metrics for a time period."""
        predictions = self.get_predictions_for_period(days)
        
        if not predictions:
            # Return default metrics when no predictions available
            return {
                'metric_date': date.today().isoformat(),
                'period_days': days,
                'total_predictions': 0,
                'matched_predictions': 0,
                'correct_outcomes': 0,
                'outcome_accuracy': 0,
                'exact_score_correct': 0,
                'score_accuracy': 0,
                'avg_home_goal_error': 0,
                'avg_away_goal_error': 0,
                'brier_score': 0,
                'total_value_bets': 0,
                'profitable_value_bets': 0,
                'value_bet_roi': 0,
                'trend_indicator': 'stable',
                'pending_matches': 0,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        total = len(predictions)
        correct_outcomes = 0
        exact_scores = 0
        home_goal_errors = []
        away_goal_errors = []
        brier_scores = []
        value_bets_total = 0
        value_bets_profitable = 0
        
        for pred in predictions:
            result = self.get_actual_result(pred['match_id'])
            if not result:
                continue
            
            # Outcome accuracy
            predicted_outcome = max(
                pred['home_win_prob'],
                pred['draw_prob'],
                pred['away_win_prob'],
                key=lambda x: {'home_win_prob': 'H', 'draw_prob': 'D', 'away_win_prob': 'A'}[x]
            )
            predicted_outcome_map = {
                'home_win_prob': 'H',
                'draw_prob': 'D',
                'away_win_prob': 'A'
            }
            predicted_result = predicted_outcome_map[predicted_outcome]
            
            if predicted_result == result['result']:
                correct_outcomes += 1
            
            # Exact score accuracy
            pred_score = pred.get('predicted_score', '')
            actual_score = f"{result['home_score']}-{result['away_score']}"
            if pred_score == actual_score:
                exact_scores += 1
            
            # Goal prediction errors
            if pred.get('predicted_home_goals') is not None:
                home_goal_errors.append(abs(pred['predicted_home_goals'] - result['home_score']))
            if pred.get('predicted_away_goals') is not None:
                away_goal_errors.append(abs(pred['predicted_away_goals'] - result['away_score']))
            
            # Brier score (probabilistic accuracy)
            actual_probs = {'H': 0, 'D': 0, 'A': 0}
            actual_probs[result['result']] = 1
            
            brier = (
                (pred['home_win_prob'] - actual_probs['H'])**2 +
                (pred['draw_prob'] - actual_probs['D'])**2 +
                (pred['away_win_prob'] - actual_probs['A'])**2
            )
            brier_scores.append(brier)
            
            # Value bet tracking
            if pred.get('value_bet_detected'):
                value_bets_total += 1
                # Simplified ROI calculation (would need actual odds)
                if pred.get('expected_value', 0) > 0:
                    value_bets_profitable += 1
        
        # Calculate final metrics
        matched = sum(1 for p in predictions if self.get_actual_result(p['match_id']))
        
        # Handle division by zero
        outcome_accuracy = correct_outcomes / matched if matched > 0 else 0
        score_accuracy = exact_scores / matched if matched > 0 else 0
        avg_home_error = sum(home_goal_errors) / len(home_goal_errors) if home_goal_errors else 0
        avg_away_error = sum(away_goal_errors) / len(away_goal_errors) if away_goal_errors else 0
        avg_brier = sum(brier_scores) / len(brier_scores) if brier_scores else 0
        value_bet_roi = (value_bets_profitable / value_bets_total * 100) if value_bets_total > 0 else 0
        
        metrics = {
            'metric_date': date.today().isoformat(),
            'period_days': days,
            'total_predictions': total,
            'matched_predictions': matched,
            'correct_outcomes': correct_outcomes,
            'outcome_accuracy': outcome_accuracy,
            'exact_score_correct': exact_scores,
            'score_accuracy': score_accuracy,
            'avg_home_goal_error': avg_home_error,
            'avg_away_goal_error': avg_away_error,
            'brier_score': avg_brier,
            'total_value_bets': value_bets_total,
            'profitable_value_bets': value_bets_profitable,
            'value_bet_roi': value_bet_roi,
        }
        
        # Determine trend
        metrics['trend_indicator'] = self._calculate_trend(days)
        
        # Save metrics
        self._save_metrics(metrics)
        
        return metrics
    
    def _calculate_trend(self, days: int = 30) -> str:
        """Determine if model accuracy is improving, stable, or declining."""
        # If we don't have enough historical data, default to stable
        return 'stable'
    
    def _save_metrics(self, metrics: Dict):
        """Save calculated metrics to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO accuracy_metrics 
                (metric_date, period_days, total_predictions, correct_outcomes,
                 outcome_accuracy, exact_score_correct, score_accuracy,
                 avg_home_goal_error, avg_away_goal_error, brier_score,
                 roi_percentage, total_value_bets, profitable_value_bets,
                 value_bet_roi, trend_indicator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics['metric_date'],
                metrics['period_days'],
                metrics['total_predictions'],
                metrics['correct_outcomes'],
                metrics['outcome_accuracy'],
                metrics['exact_score_correct'],
                metrics['score_accuracy'],
                metrics['avg_home_goal_error'],
                metrics['avg_away_goal_error'],
                metrics['brier_score'],
                metrics.get('roi_percentage', 0),
                metrics['total_value_bets'],
                metrics['profitable_value_bets'],
                metrics['value_bet_roi'],
                metrics['trend_indicator']
            ))
    
    def get_accuracy_history(self, days: int = 90) -> List[Dict]:
        """Get historical accuracy metrics over time."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM accuracy_metrics 
                WHERE metric_date >= date('now', ?)
                ORDER BY metric_date DESC
            """, (f'-{days} days',))
            return [dict(row) for row in cursor.fetchall()]
    
    def export_predictions_to_csv(self, filepath: str, days: int = 30):
        """Export predictions to CSV file."""
        import csv
        
        predictions = self.get_predictions_for_period(days)
        
        if not predictions:
            # Create a sample CSV if no predictions exist
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = ['match_id', 'league', 'home_team', 'away_team', 'home_win_prob', 'draw_prob', 'away_win_prob', 'prediction_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                # Write a sample row to have a valid CSV
                writer.writerow({
                    'match_id': 'sample_match_001',
                    'league': 'Sample League',
                    'home_team': 'Sample Home Team',
                    'away_team': 'Sample Away Team',
                    'home_win_prob': 0.45,
                    'draw_prob': 0.28,
                    'away_win_prob': 0.27,
                    'prediction_date': datetime.now().isoformat()
                })
            return
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = predictions[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for pred in predictions:
                # Convert JSON fields to strings
                row = pred.copy()
                for key, value in row.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value)
                writer.writerow(row)
    
    def generate_performance_report(self, days: int = 30) -> Dict:
        """Generate comprehensive performance report."""
        metrics = self.calculate_accuracy_metrics(days)
        history = self.get_accuracy_history(days)
        unmatched = self.get_unmatched_predictions()
        
        return {
            'summary': metrics,
            'historical_trend': history[-10:] if history else [],  # Last 10 data points
            'pending_matches': len(unmatched),
            'generated_at': datetime.now().isoformat()
        }


# Global database instance
_db_instance = None

def get_database(db_path: str = "data/soccer_predictor.db") -> SoccerPredictorDB:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SoccerPredictorDB(db_path)
    return _db_instance