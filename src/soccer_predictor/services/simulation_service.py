"""League simulation service for Monte Carlo simulations."""

import uuid
import threading
from typing import Dict, List, Optional
from src.soccer_predictor.core.simulation import SimulationEngine  # ← FIXED class name


# In-memory job store
_jobs: Dict[str, Dict] = {}


class SimulationService:
    """Service for running league simulations."""
    
    def __init__(self):
        """Initialize simulation service."""
        self.engine = SimulationEngine()
    
    def start_simulation(
        self,
        league: str = "Premier League",
        n_simulations: int = 1000
    ) -> str:
        """Start a league simulation in the background.
        
        Args:
            league: League name
            n_simulations: Number of Monte Carlo simulations
            
        Returns:
            Job ID for tracking the simulation
        """
        job_id = str(uuid.uuid4())
        
        # Store job info
        _jobs[job_id] = {
            'status': 'running',
            'progress': 0,
            'results': None,
            'error': None,
            'league': league,
            'n_simulations': n_simulations
        }
        
        # Start simulation in a separate thread
        thread = threading.Thread(
            target=self._run_simulation_thread,
            args=(job_id, league, n_simulations)
        )
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def _run_simulation_thread(self, job_id: str, league: str, n_simulations: int):
        """Run simulation in background thread."""
        try:
            results = self.simulate_season(league, n_simulations)
            _jobs[job_id]['results'] = results
            _jobs[job_id]['status'] = 'completed'
        except Exception as e:
            _jobs[job_id]['error'] = str(e)
            _jobs[job_id]['status'] = 'failed'
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get status of a simulation job.
        
        Args:
            job_id: Job ID returned by start_simulation
            
        Returns:
            Status dictionary
        """
        job = _jobs.get(job_id)
        if not job:
            return {'status': 'not_found'}
        return job
    
    def simulate_season(
        self,
        league: str = "Premier League",
        n_simulations: int = 1000
    ) -> Dict:
        """Simulate a full season.
        
        Args:
            league: League name
            n_simulations: Number of Monte Carlo simulations
            
        Returns:
            Simulation results with standings and probabilities
        """
        try:
            results = self.engine.run_simulation(league, n_simulations)
            return results
        except Exception as e:
            return {
                'error': str(e),
                'league': league
            }
    
    def get_championship_probabilities(
        self,
        league: str = "Premier League"
    ) -> List[Dict]:
        """Get championship win probabilities for all teams.
        
        Args:
            league: League name
            
        Returns:
            List of teams with championship probabilities
        """
        # Run simulation if not already done
        results = self.simulate_season(league, n_simulations=1000)
        
        if 'error' in results:
            return []
        
        return results.get('championship_probs', [])


def get_simulation_service() -> SimulationService:
    """Get or create simulation service singleton.
    
    Returns:
        SimulationService instance
    """
    global _instance
    if _instance is None:
        _instance = SimulationService()
    return _instance


# Global instance
_instance: Optional['SimulationService'] = None