import logging
from typing import Dict, Any
from ..utils.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class HTMLReporter:
    """HTML report generator for performance test results"""
    
    def __init__(self):
        """Initialize the HTML reporter"""
        self.ollama_client = OllamaClient()
    
    def generate_report(self, data: Dict[str, Any], test_name: str, environment: str) -> str:
        """Generate HTML report with LLM analysis
        
        Args:
            data: Dictionary containing test results and metrics
            test_name: Name of the test
            environment: Environment where test was run
            
        Returns:
            str: HTML report content
        """
        try:
            # Get LLM analysis
            llm_analysis = self.ollama_client.analyze_performance_results(data)
            
            # Generate HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Performance Test Report - {test_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                    .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                    .metrics-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    .metrics-table th, .metrics-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    .metrics-table th {{ background-color: #f5f5f5; }}
                    .error {{ color: red; }}
                    .success {{ color: green; }}
                    .llm-analysis {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #0052cc; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Performance Test Report</h1>
                        <h2>{test_name}</h2>
                        <p>Environment: {environment}</p>
                    </div>
                    
                    <div class="section">
                        <h3>LLM Analysis</h3>
                        <div class="llm-analysis">
                            {llm_analysis}
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>Overall Statistics</h3>
                        <table class="metrics-table">
                            <tr>
                                <th>Metric</th>
                                <th>Value</th>
                            </tr>
                            <tr>
                                <td>Test Duration</td>
                                <td>{data['test_duration']:.2f} seconds</td>
                            </tr>
                            <tr>
                                <td>Total Requests</td>
                                <td>{data['total_requests']}</td>
                            </tr>
                            <tr>
                                <td>Error Rate</td>
                                <td class="{'error' if data['error_rate'] > 0 else 'success'}">{data['error_rate']:.2f}%</td>
                            </tr>
                            <tr>
                                <td>Average Response Time</td>
                                <td>{data['avg_response_time']:.2f} ms</td>
                            </tr>
                            <tr>
                                <td>P95 Response Time</td>
                                <td>{data['p95_response_time']:.2f} ms</td>
                            </tr>
                            <tr>
                                <td>Throughput</td>
                                <td>{data['throughput']:.2f} req/sec</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="section">
                        <h3>Detailed Metrics</h3>
                        {data['metrics_table']}
                    </div>
                    
                    <div class="section">
                        <h3>Concurrent Users Over Time</h3>
                        {data['response_time_graph']}
                    </div>
                    
                    <div class="section">
                        <h3>Throughput Analysis</h3>
                        {data['throughput_graph']}
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            raise 