import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from jinja2 import Template
from tabulate import tabulate
from .base_processor import BaseProcessor
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class JMeterProcessor(BaseProcessor):
    """Processor for JMeter JTL files"""
    
    def __init__(self, jtl_file):
        """Initialize the JMeter processor"""
        super().__init__(jtl_file)
        self.test_name = None
        self.environment = None
        
    def read_data(self) -> None:
        """Read and parse the JMeter JTL file"""
        try:
            # Read the JTL file
            self.df = pd.read_csv(self.input_file, sep=',', header=0)
            
            # Convert timestamp to datetime
            self.df['timeStamp'] = pd.to_datetime(self.df['timeStamp'], unit='ms')
            
            # Calculate duration
            self.duration = (self.df['timeStamp'].max() - self.df['timeStamp'].min()).total_seconds()
            
            logger.info(f"Successfully read JMeter data from {self.input_file}")
            logger.info(f"Found {len(self.df)} samples over {self.duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error reading JMeter file {self.input_file}: {str(e)}")
            raise
            
    def calculate_overall_stats(self) -> Dict[str, Any]:
        """Calculate overall statistics from JMeter data"""
        try:
            # Calculate basic statistics
            total_requests = int(len(self.df))
            error_requests = int(len(self.df[self.df['success'] == False]))
            error_rate = float(error_requests / total_requests if total_requests > 0 else 0)
            throughput = float(total_requests / self.duration if self.duration > 0 else 0)
            
            # Calculate response time statistics
            response_times = self.df['elapsed'].astype(float)
            min_response = float(response_times.min())
            max_response = float(response_times.max())
            avg_response = float(response_times.mean())
            
            # Calculate percentiles
            p50_response = float(response_times.quantile(0.50))
            p90_response = float(response_times.quantile(0.90))
            p95_response = float(response_times.quantile(0.95))
            p99_response = float(response_times.quantile(0.99))
            
            # Calculate statistics per label
            label_stats = {}
            for label in self.df['label'].unique():
                label_data = self.df[self.df['label'] == label]
                label_times = label_data['elapsed'].astype(float)
                
                label_stats[label] = {
                    'count': int(len(label_data)),
                    'error_count': int(len(label_data[label_data['success'] == False])),
                    'error_rate': float(len(label_data[label_data['success'] == False]) / len(label_data) if len(label_data) > 0 else 0),
                    'min': float(label_times.min()),
                    'max': float(label_times.max()),
                    'mean': float(label_times.mean()),
                    'p50': float(label_times.quantile(0.50)),
                    'p90': float(label_times.quantile(0.90)),
                    'p95': float(label_times.quantile(0.95)),
                    'p99': float(label_times.quantile(0.99))
                }
            
            return {
                'total_requests': total_requests,
                'error_requests': error_requests,
                'error_rate': error_rate,
                'throughput': throughput,
                'min_response_time': min_response,
                'max_response_time': max_response,
                'avg_response_time': avg_response,
                'p50_response_time': p50_response,
                'p90_response_time': p90_response,
                'p95_response_time': p95_response,
                'p99_response_time': p99_response,
                'label_stats': label_stats
            }
            
        except Exception as e:
            logger.error(f"Error calculating JMeter statistics: {str(e)}")
            raise
        
    def generate_metrics_table(self) -> str:
        """Generate HTML table with JMeter metrics"""
        try:
            # Create table header with Confluence styling
            html = [
                '<table class="confluenceTable" style="width: 100%; border-collapse: collapse; margin: 10px 0;">',
                '<tbody>',
                '<tr style="background-color: #f0f0f0; font-weight: bold;">',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">Transaction</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">Count</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">Errors</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">Error Rate (%)</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">Throughput (req/sec)</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">Min (ms)</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">Max (ms)</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">Avg (ms)</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">P90 (ms)</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">P95 (ms)</th>',
                '<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">P99 (ms)</th>',
                '</tr>'
            ]
            
            # Add rows for each label
            for label, stats in self.overall_stats['label_stats'].items():
                # Calculate throughput for this label
                throughput = stats['count'] / self.duration if self.duration > 0 else 0
                
                html.extend([
                    '<tr>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{label}</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{stats["count"]}</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{stats["error_count"]}</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{stats["error_rate"]:.2f}%</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{throughput:.2f}</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{stats["min"]:.2f}</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{stats["max"]:.2f}</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{stats["mean"]:.2f}</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{stats["p90"]:.2f}</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{stats["p95"]:.2f}</td>',
                    f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{stats["p99"]:.2f}</td>',
                    '</tr>'
                ])
            
            # Add summary row for all transactions
            overall_throughput = self.overall_stats['total_requests'] / self.duration if self.duration > 0 else 0
            html.extend([
                '<tr style="font-weight: bold;">',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">ALL TRANSACTIONS</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{self.overall_stats["total_requests"]}</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{self.overall_stats["error_requests"]}</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{self.overall_stats["error_rate"]:.2f}%</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{overall_throughput:.2f}</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{self.overall_stats["min_response_time"]:.2f}</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{self.overall_stats["max_response_time"]:.2f}</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{self.overall_stats["avg_response_time"]:.2f}</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{self.overall_stats["p90_response_time"]:.2f}</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{self.overall_stats["p95_response_time"]:.2f}</td>',
                f'<td class="confluenceTd" style="padding: 8px; border: 1px solid #ddd;">{self.overall_stats["p99_response_time"]:.2f}</td>',
                '</tr>'
            ])
            
            # Close table
            html.extend(['</tbody>', '</table>'])
            
            return '\n'.join(html)
            
        except Exception as e:
            logger.error(f"Error generating JMeter metrics table: {str(e)}")
            raise
        
    def generate_response_time_graph(self) -> str:
        """Generate response time over time graph"""
        try:
            # Create figure and axis with narrower width
            plt.figure(figsize=(8, 4))
            
            # Plot response time for each label
            for label in self.df['label'].unique():
                label_data = self.df[self.df['label'] == label]
                plt.plot(label_data['timeStamp'], label_data['elapsed'], label=label, alpha=0.7)
            
            # Customize the plot
            plt.title('Response Time Over Time')
            plt.xlabel('Time')
            plt.ylabel('Response Time (ms)')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            # Save plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f'<img src="data:image/png;base64,{image_base64}" alt="Response Time Over Time">'
            
        except Exception as e:
            logger.error(f"Error generating response time graph: {str(e)}")
            return ""

    def generate_throughput_graph(self) -> str:
        """Generate throughput over time graph"""
        try:
            # Create figure and axis with narrower width
            plt.figure(figsize=(8, 4))
            
            # Calculate throughput for each label
            for label in self.df['label'].unique():
                label_data = self.df[self.df['label'] == label]
                # Resample to 1-minute intervals and count requests
                throughput = label_data.resample('1min', on='timeStamp').size()
                plt.plot(throughput.index, throughput.values, label=label, alpha=0.7)
            
            # Customize the plot
            plt.title('Throughput Over Time')
            plt.xlabel('Time')
            plt.ylabel('Requests per Minute')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            # Save plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f'<img src="data:image/png;base64,{image_base64}" alt="Throughput Over Time">'
            
        except Exception as e:
            logger.error(f"Error generating throughput graph: {str(e)}")
            return ""

    def generate_html_report(self, test_name: str, environment: str) -> str:
        """
        Generate HTML report
        
        Args:
            test_name: Name of the test
            environment: Environment where the test was run
            
        Returns:
            HTML report as string
        """
        try:
            logger.info("Attempting to load template...")
            template = self.template_env.get_template('report_template.html')
            logger.info("Template loaded successfully")
            
            # Generate graphs
            response_time_graph = self.generate_response_time_graph()
            throughput_graph = self.generate_throughput_graph()
            
            logger.info("Rendering template...")
            html = template.render(
                test_name=test_name,
                environment=environment,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                total_requests=self.overall_stats['total_requests'],
                total_errors=self.overall_stats['error_requests'],
                error_rate=f"{self.overall_stats['error_rate']:.2%}",
                throughput=f"{self.overall_stats.get('throughput', 0):.2f}",
                min_response=f"{self.overall_stats['min_response_time']:.2f}",
                max_response=f"{self.overall_stats['max_response_time']:.2f}",
                avg_response=f"{self.overall_stats['avg_response_time']:.2f}",
                p50_response=f"{self.overall_stats.get('p50_response_time', 0):.2f}",
                p90_response=f"{self.overall_stats.get('p90_response_time', 0):.2f}",
                p95_response=f"{self.overall_stats.get('p95_response_time', 0):.2f}",
                p99_response=f"{self.overall_stats.get('p99_response_time', 0):.2f}",
                metrics_table=self.generate_metrics_table(),
                response_time_graph=response_time_graph,
                throughput_graph=throughput_graph
            )
            logger.info("Template rendered successfully")
            return html
            
        except Exception as e:
            logger.error(f"Error in generate_html_report: {str(e)}")
            raise Exception(f"Error reading template: {str(e)}")
        
    def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON report from JMeter data"""
        try:
            # Calculate overall statistics
            stats = self.calculate_overall_stats()
            
            # Convert NumPy types to Python native types
            report = {
                'test_name': self.test_name,
                'environment': self.environment,
                'timestamp': datetime.now().isoformat(),
                'duration': float(self.duration),
                'overall_stats': {
                    'total_requests': int(stats['total_requests']),
                    'error_requests': int(stats['error_requests']),
                    'error_rate': float(stats['error_rate']),
                    'throughput': float(stats['throughput']),
                    'min_response_time': float(stats['min_response_time']),
                    'max_response_time': float(stats['max_response_time']),
                    'avg_response_time': float(stats['avg_response_time']),
                    'p50_response_time': float(stats['p50_response_time']),
                    'p90_response_time': float(stats['p90_response_time']),
                    'p95_response_time': float(stats['p95_response_time']),
                    'p99_response_time': float(stats['p99_response_time'])
                },
                'label_stats': {
                    label: {
                        'count': int(data['count']),
                        'error_count': int(data['error_count']),
                        'error_rate': float(data['error_rate']),
                        'min': float(data['min']),
                        'max': float(data['max']),
                        'mean': float(data['mean']),
                        'p50': float(data['p50']),
                        'p90': float(data['p90']),
                        'p95': float(data['p95']),
                        'p99': float(data['p99'])
                    }
                    for label, data in stats['label_stats'].items()
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            raise
        
    def generate_console_table(self) -> str:
        """Generate console-friendly table for JMeter results"""
        try:
            # Create table header
            lines = [
                f"\nTest: {self.test_name}",
                f"Environment: {self.environment}",
                f"Duration: {self.duration:.2f} seconds",
                "\nOverall Statistics:",
                f"Total Requests: {self.overall_stats['total_requests']}",
                f"Error Requests: {self.overall_stats['error_requests']}",
                f"Error Rate: {self.overall_stats['error_rate']:.2%}",
                f"Throughput: {self.overall_stats['throughput']:.2f} transactions/sec",
                f"Min Response Time: {self.overall_stats['min_response_time']:.2f} ms",
                f"Max Response Time: {self.overall_stats['max_response_time']:.2f} ms",
                f"Average Response Time: {self.overall_stats['avg_response_time']:.2f} ms",
                f"P50 Response Time: {self.overall_stats['p50_response_time']:.2f} ms",
                f"P90 Response Time: {self.overall_stats['p90_response_time']:.2f} ms",
                f"P95 Response Time: {self.overall_stats['p95_response_time']:.2f} ms",
                f"P99 Response Time: {self.overall_stats['p99_response_time']:.2f} ms",
                "\nPer-Label Statistics:"
            ]
            
            # Add rows for each label
            for label, stats in self.overall_stats['label_stats'].items():
                lines.extend([
                    f"\n{label}:",
                    f"  Count: {stats['count']}",
                    f"  Error Count: {stats['error_count']}",
                    f"  Error Rate: {stats['error_rate']:.2%}",
                    f"  Min: {stats['min']:.2f} ms",
                    f"  Max: {stats['max']:.2f} ms",
                    f"  Mean: {stats['mean']:.2f} ms",
                    f"  P50: {stats['p50']:.2f} ms",
                    f"  P90: {stats['p90']:.2f} ms",
                    f"  P95: {stats['p95']:.2f} ms",
                    f"  P99: {stats['p99']:.2f} ms"
                ])
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error generating JMeter console table: {str(e)}")
            raise
        
    def process(self, test_name, environment):
        """Process test results"""
        self.test_name = test_name
        self.environment = environment
        
        self.read_data()
        self.overall_stats = self.calculate_overall_stats()
        
        return {
            'html_report': self.generate_html_report(test_name, environment),
            'json_report': self.generate_json_report(),
            'console_table': self.generate_console_table(),
            'overall_stats': self.overall_stats
        } 