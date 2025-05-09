from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseReporter(ABC):
    """Base class for all reporters"""
    
    def __init__(self):
        """Initialize the reporter"""
        pass
    
    @abstractmethod
    def generate_report(self, data: Dict[str, Any], test_name: str, environment: str) -> str:
        """
        Generate a report from the processed data
        
        Args:
            data: Dictionary containing processed test data
            test_name: Name of the test
            environment: Environment where test was run
            
        Returns:
            Formatted report as a string
        """
        pass
    
    @abstractmethod
    def format_metrics(self, metrics: Dict[str, Any]) -> str:
        """
        Format metrics data for the specific report type
        
        Args:
            metrics: Dictionary containing metrics data
            
        Returns:
            Formatted metrics as a string
        """
        pass 