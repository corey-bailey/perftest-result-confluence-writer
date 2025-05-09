import os
import logging
from datetime import datetime
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from .BaseReporter import BaseReporter

logger = logging.getLogger(__name__)

class HTMLReporter(BaseReporter):
    """HTML report generator"""
    
    def __init__(self):
        """Initialize the HTML reporter"""
        super().__init__()
        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'templates')
        self.template_env = Environment(loader=FileSystemLoader(template_dir))
    
    def generate_report(self, data: Dict[str, Any], test_name: str, environment: str) -> str:
        """
        Generate HTML report from processed data
        
        Args:
            data: Dictionary containing processed test data
            test_name: Name of the test
            environment: Environment where test was run
            
        Returns:
            HTML report as a string
        """
        try:
            logger.info("Loading HTML template...")
            template = self.template_env.get_template('report_template.html')
            logger.info("Template loaded successfully")
            
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
            
            # Render template with data
            html = template.render(
                test_name=test_name,
                environment=environment,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                test_times=test_times,
                test_duration=duration_str,
                total_requests=data['total_requests'],
                total_errors=data['error_requests'],
                error_rate=f"{data['error_rate']:.2%}",
                throughput=f"{data.get('throughput', 0):.2f}",
                min_response=f"{data['min_response_time']:.2f}",
                max_response=f"{data['max_response_time']:.2f}",
                avg_response=f"{data['avg_response_time']:.2f}",
                p50_response=f"{data.get('p50_response_time', 0):.2f}",
                p90_response=f"{data['p90_response_time']:.2f}",
                p95_response=f"{data['p95_response_time']:.2f}",
                p99_response=f"{data['p99_response_time']:.2f}",
                max_concurrent_users=data['max_concurrent_users'],
                avg_concurrent_users=data['avg_concurrent_users'],
                min_concurrent_users=data['min_concurrent_users'],
                metrics_table=data['metrics_table'],
                response_time_graph=data['response_time_graph'],
                throughput_graph=data['throughput_graph']
            )
            
            logger.info("HTML report generated successfully")
            return html
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            raise
    
    def format_metrics(self, metrics: Dict[str, Any]) -> str:
        """
        Format metrics data for HTML report
        
        Args:
            metrics: Dictionary containing metrics data
            
        Returns:
            Formatted metrics as HTML string
        """
        try:
            # Generate HTML table with improved styling
            html_table = '''
            <table class="confluenceTable" style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                <tbody>
                    <tr style="background-color: #f0f0f0; font-weight: bold;">
            '''
            
            # Add headers
            for col in metrics['columns']:
                html_table += f'<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">{col}</th>'
            html_table += '</tr>'
            
            # Add rows
            for row in metrics['rows']:
                html_table += '<tr>'
                for value in row:
                    html_table += f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{value}</td>'
                html_table += '</tr>'
            
            html_table += '''
                </tbody>
            </table>
            '''
            
            return html_table
            
        except Exception as e:
            logger.error(f"Error formatting metrics for HTML: {str(e)}")
            raise 