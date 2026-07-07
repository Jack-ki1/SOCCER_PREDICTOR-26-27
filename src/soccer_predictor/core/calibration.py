"""Probability calibration using Platt Scaling and Temperature Scaling.

Implements methods to calibrate predicted probabilities to match real-world frequencies.
Inspired by F1 Predictor 2026's calibration system.
"""

import numpy as np
from scipy.optimize import minimize
from typing import List, Dict, Tuple, Optional
from sklearn.metrics import brier_score_loss, log_loss


class ProbabilityCalibrator:
    """
    Calibrates predicted probabilities using various methods.
    
    Methods:
    - Platt Scaling: Logistic regression on model outputs
    - Temperature Scaling: Single-parameter softmax scaling
    - Isotonic Regression: Non-parametric monotonic calibration
    """
    
    def __init__(self, method: str = 'platt'):
        """
        Initialize calibrator.
        
        Args:
            method: Calibration method ('platt', 'temperature', 'isotonic')
        """
        self.method = method
        self.params = {}
        self.is_trained = False
    
    def train_platt_scaling(self, predictions: List[float], 
                           outcomes: List[int]) -> Dict[str, float]:
        """
        Train Platt Scaling parameters.
        
        Platt Scaling fits a logistic regression model:
        P_calibrated = 1 / (1 + exp(A * f(x) + B))
        
        Args:
            predictions: Raw predicted probabilities
            outcomes: Actual outcomes (0 or 1)
        
        Returns:
            Dictionary with parameters A and B
        """
        def neg_log_likelihood(params):
            """Negative log-likelihood for optimization."""
            A, B = params
            p_calibrated = 1.0 / (1.0 + np.exp(A * np.array(predictions) + B))
            # Clip to avoid log(0)
            p_calibrated = np.clip(p_calibrated, 1e-10, 1 - 1e-10)
            
            # Negative log-likelihood
            nll = -np.mean(
                outcomes * np.log(p_calibrated) + 
                (1 - np.array(outcomes)) * np.log(1 - p_calibrated)
            )
            return nll
        
        # Initial parameters
        initial_params = [0.0, 0.0]
        
        # Optimize
        result = minimize(neg_log_likelihood, initial_params, method='L-BFGS-B')
        
        self.params = {
            'A': result.x[0],
            'B': result.x[1]
        }
        self.is_trained = True
        
        return self.params
    
    def train_temperature_scaling(self, logits: List[float], 
                                  outcomes: List[int]) -> Dict[str, float]:
        """
        Train Temperature Scaling parameter.
        
        Temperature Scaling divides logits by temperature T:
        P_calibrated = sigmoid(logit / T)
        
        Args:
            logits: Raw model logits (log-odds)
            outcomes: Actual outcomes (0 or 1)
        
        Returns:
            Dictionary with temperature parameter T
        """
        def nll_with_temperature(T):
            """Negative log-likelihood with temperature."""
            T = max(T[0], 0.01)  # Prevent division by zero
            calibrated_probs = 1.0 / (1.0 + np.exp(-np.array(logits) / T))
            calibrated_probs = np.clip(calibrated_probs, 1e-10, 1 - 1e-10)
            
            nll = -np.mean(
                outcomes * np.log(calibrated_probs) + 
                (1 - np.array(outcomes)) * np.log(1 - calibrated_probs)
            )
            return nll
        
        # Optimize temperature
        result = minimize(nll_with_temperature, [1.0], method='L-BFGS-B', 
                         bounds=[(0.01, 10.0)])
        
        self.params = {
            'temperature': result.x[0]
        }
        self.is_trained = True
        
        return self.params
    
    def calibrate_platt(self, raw_prob: float) -> float:
        """
        Apply Platt Scaling calibration to a single probability.
        
        Args:
            raw_prob: Raw predicted probability
        
        Returns:
            Calibrated probability
        """
        if not self.is_trained or self.method != 'platt':
            return raw_prob
        
        A = self.params['A']
        B = self.params['B']
        
        # Convert probability to logit
        raw_prob = np.clip(raw_prob, 1e-10, 1 - 1e-10)
        logit = np.log(raw_prob / (1 - raw_prob))
        
        # Apply Platt scaling
        calibrated_logit = A * logit + B
        calibrated_prob = 1.0 / (1.0 + np.exp(-calibrated_logit))
        
        return calibrated_prob
    
    def calibrate_temperature(self, raw_prob: float) -> float:
        """
        Apply Temperature Scaling calibration to a single probability.
        
        Args:
            raw_prob: Raw predicted probability
        
        Returns:
            Calibrated probability
        """
        if not self.is_trained or self.method != 'temperature':
            return raw_prob
        
        T = self.params['temperature']
        
        # Convert probability to logit
        raw_prob = np.clip(raw_prob, 1e-10, 1 - 1e-10)
        logit = np.log(raw_prob / (1 - raw_prob))
        
        # Apply temperature scaling
        calibrated_logit = logit / T
        calibrated_prob = 1.0 / (1.0 + np.exp(-calibrated_logit))
        
        return calibrated_prob
    
    def calibrate(self, raw_prob: float) -> float:
        """
        Calibrate a probability using the trained method.
        
        Args:
            raw_prob: Raw predicted probability
        
        Returns:
            Calibrated probability
        """
        if self.method == 'platt':
            return self.calibrate_platt(raw_prob)
        elif self.method == 'temperature':
            return self.calibrate_temperature(raw_prob)
        else:
            return raw_prob
    
    def calibrate_three_way(self, home_win: float, draw: float, 
                           away_win: float) -> Tuple[float, float, float]:
        """
        Calibrate three-way outcome probabilities and normalize.
        
        Args:
            home_win: Raw home win probability
            draw: Raw draw probability
            away_win: Raw away win probability
        
        Returns:
            Tuple of calibrated probabilities (normalized to sum to 1)
        """
        cal_home = self.calibrate(home_win)
        cal_draw = self.calibrate(draw)
        cal_away = self.calibrate(away_win)
        
        # Normalize to ensure they sum to 1
        total = cal_home + cal_draw + cal_away
        if total > 0:
            cal_home /= total
            cal_draw /= total
            cal_away /= total
        
        return cal_home, cal_draw, cal_away


class CalibrationEvaluator:
    """Evaluate calibration quality using various metrics."""
    
    @staticmethod
    def calculate_brier_score(predictions: List[float], 
                             outcomes: List[int]) -> float:
        """
        Calculate Brier Score (mean squared error of probabilities).
        
        Lower is better. Perfect score = 0.
        
        Args:
            predictions: Predicted probabilities
            outcomes: Actual outcomes (0 or 1)
        
        Returns:
            Brier Score
        """
        return brier_score_loss(outcomes, predictions)
    
    @staticmethod
    def calculate_log_loss(predictions: List[float], 
                          outcomes: List[int]) -> float:
        """
        Calculate Log Loss (cross-entropy loss).
        
        Lower is better. Penalizes confident wrong predictions heavily.
        
        Args:
            predictions: Predicted probabilities
            outcomes: Actual outcomes (0 or 1)
        
        Returns:
            Log Loss
        """
        # Clip predictions to avoid log(0)
        predictions = np.clip(predictions, 1e-15, 1 - 1e-15)
        return log_loss(outcomes, predictions)
    
    @staticmethod
    def calculate_ece(predictions: List[float], outcomes: List[int], 
                     n_bins: int = 10) -> float:
        """
        Calculate Expected Calibration Error (ECE).
        
        ECE measures the average difference between predicted and actual
        probabilities across bins.
        
        Args:
            predictions: Predicted probabilities
            outcomes: Actual outcomes (0 or 1)
            n_bins: Number of bins for calibration curve
        
        Returns:
            Expected Calibration Error
        """
        bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        total_samples = len(predictions)
        
        for i in range(n_bins):
            # Get samples in this bin
            mask = ((np.array(predictions) >= bin_boundaries[i]) & 
                   (np.array(predictions) < bin_boundaries[i + 1]))
            
            if np.sum(mask) == 0:
                continue
            
            # Average predicted probability in bin
            avg_pred = np.mean(np.array(predictions)[mask])
            
            # Actual frequency in bin
            actual_freq = np.mean(np.array(outcomes)[mask])
            
            # Weighted absolute difference
            bin_weight = np.sum(mask) / total_samples
            ece += bin_weight * abs(avg_pred - actual_freq)
        
        return ece
    
    @staticmethod
    def generate_reliability_data(predictions: List[float], 
                                 outcomes: List[int], 
                                 n_bins: int = 10) -> Dict:
        """
        Generate data for reliability diagram.
        
        Args:
            predictions: Predicted probabilities
            outcomes: Actual outcomes (0 or 1)
            n_bins: Number of bins
        
        Returns:
            Dictionary with bin centers, predicted probs, and actual freqs
        """
        bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
        bin_centers = []
        predicted_probs = []
        actual_freqs = []
        bin_counts = []
        
        for i in range(n_bins):
            mask = ((np.array(predictions) >= bin_boundaries[i]) & 
                   (np.array(predictions) < bin_boundaries[i + 1]))
            
            if np.sum(mask) > 0:
                bin_center = (bin_boundaries[i] + bin_boundaries[i + 1]) / 2
                bin_centers.append(bin_center)
                predicted_probs.append(np.mean(np.array(predictions)[mask]))
                actual_freqs.append(np.mean(np.array(outcomes)[mask]))
                bin_counts.append(int(np.sum(mask)))
        
        return {
            'bin_centers': bin_centers,
            'predicted_probs': predicted_probs,
            'actual_freqs': actual_freqs,
            'bin_counts': bin_counts
        }


def calibrate_prediction(prediction: Dict, calibrator: ProbabilityCalibrator) -> Dict:
    """
    Calibrate a prediction dictionary.
    
    Args:
        prediction: Prediction dictionary with home_win, draw, away_win
        calibrator: Trained ProbabilityCalibrator instance
    
    Returns:
        Updated prediction dictionary with calibrated probabilities
    """
    raw_home = prediction.get('home_win', 0.45)
    raw_draw = prediction.get('draw', 0.28)
    raw_away = prediction.get('away_win', 0.27)
    
    cal_home, cal_draw, cal_away = calibrator.calibrate_three_way(
        raw_home, raw_draw, raw_away
    )
    
    prediction['calibrated_home_win'] = cal_home
    prediction['calibrated_draw'] = cal_draw
    prediction['calibrated_away_win'] = cal_away
    prediction['is_calibrated'] = True
    
    return prediction
