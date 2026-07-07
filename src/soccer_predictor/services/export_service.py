"""Export service for prediction results."""

from typing import Dict, List, Optional
import json
import csv
import io
from datetime import datetime


# Singleton instance
_instance: Optional['ExportService'] = None


class ExportService:
    """Service for exporting prediction data."""
    
    def __init__(self):
        """Initialize export service."""
        pass
    
    def export_to_json(self, data: Dict) -> str:
        """Export data to JSON format.
        
        Args:
            data: Data to export
            
        Returns:
            JSON string
        """
        return json.dumps(data, indent=2, default=str)
    
    def export_to_csv(self, data: List[Dict]) -> str:
        """Export data to CSV format.
        
        Args:
            data: List of dictionaries to export
            
        Returns:
            CSV string
        """
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    def export_predictions(
        self,
        predictions: List[Dict],
        format: str = "json"
    ) -> str:
        """Export predictions in specified format.
        
        Args:
            predictions: List of prediction results
            format: Export format ('json' or 'csv')
            
        Returns:
            Formatted export string
        """
        if format == "json":
            return self.export_to_json({
                'predictions': predictions,
                'exported_at': datetime.now().isoformat(),
                'count': len(predictions)
            })
        elif format == "csv":
            return self.export_to_csv(predictions)
        else:
            raise ValueError(f"Unsupported format: {format}")


def get_export_service() -> ExportService:
    """Get or create export service singleton.
    
    Returns:
        ExportService instance
    """
    global _instance
    if _instance is None:
        _instance = ExportService()
    return _instance
