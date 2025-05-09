import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from jinja2 import Template
from tabulate import tabulate
from .base_processor import BaseProcessor

class K6Processor(BaseProcessor):
    """Processor for k6 JSON files"""
    
    def __init__(self, json_file):
        """Initialize the k6 processor"""
        super().__init__(json_file)
        self.test_name = None
        self.environment = None
        
    def read_data(self):
        """Read and process k6 JSON data"""
        try:
            # Read the JSON file
            with open(self.input_file, 'r') as f:
                data = json.load(f)
                
            # Extract metrics
            metrics = []
            for metric in data['metrics']:
                if metric['type'] == 'Point' and metric['metric'] == 'http_req_duration':
                    metrics.append({
                        'timestamp': datetime.fromisoformat(metric['data']['time'].replace('Z', '+00:00')),
                        'value': metric['data']['value'],
                        'name': metric['data']['tags']['name'],
                        'method': metric['data']['tags']['method'],
                        'status': metric['data']['tags']['status'],
                        'url': metric['data']['tags']['url']
                    })
                        
            # Convert to DataFrame
            self.data = pd.DataFrame(metrics)
            
            # Calculate test duration in seconds
            self.test_duration = (self.data['timestamp'].max() - self.data['timestamp'].min()).total_seconds()
            
            return self.data
        except Exception as e:
            logging.error(f"Error reading k6 JSON file: {str(e)}")
            raise
            
    def calculate_overall_stats(self):
        """Calculate overall statistics"""
        try:
            total_requests = len(self.data)
            error_requests = len(self.data[self.data['status'].isin(['500', '404'])])
            error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0
            
            stats = {
                'total_requests': total_requests,
                'error_requests': error_requests,
                'error_rate': error_rate,
                'avg_response_time': self.data['value'].mean(),
                'min_response_time': self.data['value'].min(),
                'max_response_time': self.data['value'].max(),
                'test_duration': self.test_duration
            }
            
            return stats
        except Exception as e:
            logging.error(f"Error calculating overall statistics: {str(e)}")
            raise
        
    def generate_metrics_table(self):
        """Generate metrics table"""
        try:
            metrics = []
            for name in self.data['name'].unique():
                transaction_data = self.data[self.data['name'] == name]
                total = len(transaction_data)
                errors = len(transaction_data[transaction_data['status'].isin(['500', '404'])])
                error_rate = (errors / total) * 100 if total > 0 else 0
                
                metrics.append({
                    'Transaction': name,
                    'Count': total,
                    'Errors': errors,
                    'Error Rate (%)': f"{error_rate:.2f}%",
                    'Min (ms)': f"{transaction_data['value'].min():.2f}",
                    'Max (ms)': f"{transaction_data['value'].max():.2f}",
                    'Avg (ms)': f"{transaction_data['value'].mean():.2f}"
                })
            
            metrics_df = pd.DataFrame(metrics)
            return metrics_df.to_html(index=False, classes='table table-striped')
        except Exception as e:
            logging.error(f"Error generating metrics table: {str(e)}")
            raise
        
    def generate_html_report(self, test_name, environment):
        """Generate HTML report"""
        try:
            template = self.read_template()
            overall_stats = self.calculate_overall_stats()
            metrics_table = self.generate_metrics_table()
            
            report = template.render(
                test_name=test_name,
                environment=environment,
                overall_stats=overall_stats,
                metrics_table=metrics_table
            )
            
            return report
        except Exception as e:
            logging.error(f"Error generating HTML report: {str(e)}")
            raise
        
    def generate_json_report(self, test_name, environment):
        """Generate JSON report"""
        try:
            overall_stats = self.calculate_overall_stats()
            metrics = []
            
            for name in self.data['name'].unique():
                transaction_data = self.data[self.data['name'] == name]
                total = len(transaction_data)
                errors = len(transaction_data[transaction_data['status'].isin(['500', '404'])])
                error_rate = (errors / total) * 100 if total > 0 else 0
                
                metrics.append({
                    'transaction': name,
                    'count': total,
                    'errors': errors,
                    'error_rate': error_rate,
                    'min_response_time': transaction_data['value'].min(),
                    'max_response_time': transaction_data['value'].max(),
                    'avg_response_time': transaction_data['value'].mean()
                })
            
            report = {
                'test_name': test_name,
                'environment': environment,
                'overall_stats': overall_stats,
                'metrics': metrics
            }
            
            return report
        except Exception as e:
            logging.error(f"Error generating JSON report: {str(e)}")
            raise
        
    def generate_console_table(self):
        """Generate console table"""
        try:
            metrics = []
            for name in self.data['name'].unique():
                transaction_data = self.data[self.data['name'] == name]
                total = len(transaction_data)
                errors = len(transaction_data[transaction_data['status'].isin(['500', '404'])])
                error_rate = (errors / total) * 100 if total > 0 else 0
                
                metrics.append([
                    name,
                    total,
                    errors,
                    f"{error_rate:.2f}%",
                    f"{transaction_data['value'].min():.2f}",
                    f"{transaction_data['value'].max():.2f}",
                    f"{transaction_data['value'].mean():.2f}"
                ])
            
            headers = ['Transaction', 'Count', 'Errors', 'Error Rate', 'Min (ms)', 'Max (ms)', 'Avg (ms)']
            return tabulate(metrics, headers=headers, tablefmt='grid')
        except Exception as e:
            logging.error(f"Error generating console table: {str(e)}")
            raise
        
    def process(self, test_name, environment):
        """Process test results"""
        try:
            self.test_name = test_name
            self.environment = environment
            
            self.read_data()
            
            return {
                'html_report': self.generate_html_report(test_name, environment),
                'json_report': self.generate_json_report(test_name, environment),
                'console_table': self.generate_console_table()
            }
        except Exception as e:
            logging.error(f"Error processing test results: {str(e)}")
            raise 