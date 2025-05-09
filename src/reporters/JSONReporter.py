import logging
from datetime import datetime
from typing import Dict, Any
from .BaseReporter import BaseReporter

logger = logging.getLogger(__name__)

class JSONReporter(BaseReporter):
    """JSON report generator"""
    
    def __init__(self):
        """Initialize the JSON reporter"""
        super().__init__()
    
    def generate_report(self, data: Dict[str, Any], test_name: str, environment: str) -> Dict[str, Any]:
        """
        Generate JSON report from processed data
        
        Args:
            data: Dictionary containing processed test data
            test_name: Name of the test
            environment: Environment where test was run
            
        Returns:
            JSON report as a dictionary
        """
        try:
            # Create base report
            report = {
                'test_name': test_name,
                'environment': environment,
                'timestamp': datetime.now().isoformat(),
                'duration': float(data['test_duration']),
                'overall_stats': {
                    'total_requests': int(data['total_requests']),
                    'error_requests': int(data['error_requests']),
                    'error_rate': float(data['error_rate']),
                    'avg_response_time': float(data['avg_response_time']),
                    'min_response_time': float(data['min_response_time']),
                    'max_response_time': float(data['max_response_time']),
                    'p90_response_time': float(data['p90_response_time']),
                    'p95_response_time': float(data['p95_response_time']),
                    'p99_response_time': float(data['p99_response_time']),
                    'max_concurrent_users': int(data['max_concurrent_users']),
                    'avg_concurrent_users': float(data['avg_concurrent_users']),
                    'min_concurrent_users': int(data['min_concurrent_users'])
                }
            }
            
            # Add concurrent users over time if available
            if 'concurrent_users_over_time' in data:
                concurrent_users_over_time = {
                    ts.isoformat(): count 
                    for ts, count in data['concurrent_users_over_time'].items()
                }
                report['overall_stats']['concurrent_users_over_time'] = concurrent_users_over_time
            
            # Add transaction metrics
            if 'metrics' in data and 'transactions' in data['metrics']:
                report['transactions'] = []
                for transaction in data['metrics']['transactions']:
                    report['transactions'].append({
                        'name': transaction['name'],
                        'count': int(transaction['count']),
                        'errors': int(transaction['errors']),
                        'error_rate': float(transaction['error_rate']),
                        'throughput': float(transaction['throughput']),
                        'min_response_time': float(transaction['min_response_time']),
                        'max_response_time': float(transaction['max_response_time']),
                        'avg_response_time': float(transaction['avg_response_time']),
                        'p90_response_time': float(transaction['p90_response_time']),
                        'p95_response_time': float(transaction['p95_response_time']),
                        'p99_response_time': float(transaction['p99_response_time'])
                    })
            
            logger.info("JSON report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            raise
    
    def format_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format metrics data for JSON report
        
        Args:
            metrics: Dictionary containing metrics data
            
        Returns:
            Formatted metrics as a dictionary
        """
        try:
            formatted_metrics = {
                'transactions': []
            }
            
            for transaction in metrics['transactions']:
                formatted_metrics['transactions'].append({
                    'name': transaction['name'],
                    'count': int(transaction['count']),
                    'errors': int(transaction['errors']),
                    'error_rate': float(transaction['error_rate']),
                    'throughput': float(transaction['throughput']),
                    'min_response_time': float(transaction['min_response_time']),
                    'max_response_time': float(transaction['max_response_time']),
                    'avg_response_time': float(transaction['avg_response_time']),
                    'p90_response_time': float(transaction['p90_response_time']),
                    'p95_response_time': float(transaction['p95_response_time']),
                    'p99_response_time': float(transaction['p99_response_time'])
                })
            
            return formatted_metrics
            
        except Exception as e:
            logger.error(f"Error formatting metrics for JSON: {str(e)}")
            raise 
            raise 