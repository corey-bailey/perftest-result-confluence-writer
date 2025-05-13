import logging
from typing import Dict, Any
from tabulate import tabulate
from .BaseReporter import BaseReporter

logger = logging.getLogger(__name__)

class ConsoleReporter(BaseReporter):
    """Console report generator"""
    
    def __init__(self):
        """Initialize the console reporter"""
        super().__init__()
    
    def generate_report(self, data: Dict[str, Any], test_name: str, environment: str) -> str:
        """
        Generate console report from processed data
        
        Args:
            data: Dictionary containing processed test data
            test_name: Name of the test
            environment: Environment where test was run
            
        Returns:
            Console report as a string
        """
        try:
            # Format test timing information
            start_time = data['start_time']
            end_time = data['end_time']
            duration = data['test_duration']
            
            # Format duration into hours, minutes, seconds
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Format test times as a single field
            test_times = f"{start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Create summary table
            summary_data = [
                ['Test Name', test_name],
                ['Environment', environment],
                ['Test Times', test_times],
                ['Test Duration', duration_str],
                ['Total Requests', data['total_requests']],
                ['Total Errors', data['error_requests']],
                ['Error Rate', f"{data['error_rate']:.2f}%"],
                ['Throughput', f"{data.get('throughput', 0):.2f} req/sec"],
                ['Avg Response Time', f"{data['avg_response_time']:.2f} ms"],
                ['Max Response Time', f"{data['max_response_time']:.2f} ms"],
                ['P90 Response Time', f"{data['p90_response_time']:.2f} ms"],
                ['P95 Response Time', f"{data['p95_response_time']:.2f} ms"],
                ['P99 Response Time', f"{data['p99_response_time']:.2f} ms"],
                ['Max Concurrent Users', data['max_concurrent_users']],
                ['Avg Concurrent Users', f"{data['avg_concurrent_users']:.2f}"],
                ['Min Concurrent Users', data['min_concurrent_users']]
            ]
            
            summary_table = tabulate(summary_data, tablefmt='grid')
            
            # Add metrics table
            metrics_table = self.format_metrics(data['metrics'])
            
            # Combine tables
            report = f"\n{summary_table}\n\n{metrics_table}"
            
            logger.info("Console report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating console report: {str(e)}")
            raise
    
    def format_metrics(self, metrics: Dict[str, Any]) -> str:
        """
        Format metrics data for console output
        
        Args:
            metrics: Dictionary containing metrics data
            
        Returns:
            Formatted metrics as a string
        """
        try:
            # Prepare table data
            table_data = []
            headers = ['Transaction', 'Count', 'Errors', 'Error Rate', 'Throughput', 'Min (ms)', 'Max (ms)', 'Avg (ms)']
            
            for transaction in metrics['transactions']:
                table_data.append([
                    transaction['name'],
                    transaction['count'],
                    transaction['errors'],
                    f"{transaction['error_rate']:.2f}%",
                    f"{transaction['throughput']:.2f}",
                    f"{transaction['min_response_time']:.2f}",
                    f"{transaction['max_response_time']:.2f}",
                    f"{transaction['avg_response_time']:.2f}"
                ])
            
            # Generate table
            return tabulate(table_data, headers=headers, tablefmt='grid')
            
        except Exception as e:
            logger.error(f"Error formatting metrics for console: {str(e)}")
            raise 