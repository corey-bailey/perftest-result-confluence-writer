#!/usr/bin/env python3

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from .base_processor import BaseProcessor
import matplotlib.pyplot as plt
import io
import base64
import pytz
from jinja2 import Template
from tabulate import tabulate
from src.utils.ollama_client import OllamaClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NeoLoadProcessor(BaseProcessor):
    """Processor for NeoLoad test results"""
    
    def __init__(self, input_file: str):
        """Initialize the NeoLoad processor"""
        super().__init__(input_file)
        self.df = None
        self.test_duration = 0
        self.eastern_tz = pytz.timezone('US/Eastern')
        self.ollama_client = OllamaClient()
        self.logger.info(f"Initialized NeoLoad processor with input file: {input_file}")
    
    def read_data(self) -> None:
        """Read and parse the NeoLoad CSV file"""
        try:
            # Read the CSV file
            self.df = pd.read_csv(self.input_file, sep=';')
            
            # Convert timestamp to datetime and convert to Eastern time
            self.df['Time'] = pd.to_datetime(self.df['Time'])
            if self.df['Time'].dt.tz is None:
                self.df['Time'] = self.df['Time'].dt.tz_localize('UTC')
            self.df['Time'] = self.df['Time'].dt.tz_convert('US/Eastern')
            
            # Calculate actual start time by subtracting elapsed time from first record
            first_record_time = self.df['Time'].min()
            first_record_elapsed = self.df.loc[self.df['Time'] == first_record_time, 'Elapsed'].iloc[0]
            self.actual_start_time = first_record_time - pd.Timedelta(milliseconds=first_record_elapsed)
            
            # Calculate actual end time by adding response time to last record
            last_record_time = self.df['Time'].max()
            last_record_response = self.df.loc[self.df['Time'] == last_record_time, 'Response time'].iloc[0]
            self.actual_end_time = last_record_time + pd.Timedelta(milliseconds=last_record_response)
            
            # Calculate test duration in seconds
            self.test_duration = (self.actual_end_time - self.actual_start_time).total_seconds()
            
            self.logger.info(f"Successfully read NeoLoad data from {self.input_file}")
            self.logger.info(f"Found {len(self.df)} samples over {self.test_duration:.2f} seconds")
            self.logger.info(f"Actual test start time: {self.actual_start_time}")
            self.logger.info(f"Actual test end time: {self.actual_end_time}")
            
        except Exception as e:
            self.logger.error(f"Error reading NeoLoad CSV file: {str(e)}")
            raise
    
    def calculate_overall_stats(self) -> Dict[str, Any]:
        """Calculate overall statistics from NeoLoad data"""
        try:
            # Calculate basic statistics
            total_requests = len(self.df)
            error_requests = len(self.df[self.df['Success'].str.lower() != 'yes'])
            error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0
            
            # Calculate test duration and throughput using actual start and end times
            test_duration = (self.actual_end_time - self.actual_start_time).total_seconds()
            throughput = total_requests / test_duration if test_duration > 0 else 0
            
            # Calculate response time statistics
            response_times = self.df['Response time'].astype(float)
            min_response = response_times.min()
            max_response = response_times.max()
            avg_response = response_times.mean()
            
            # Calculate percentiles
            p90_response = response_times.quantile(0.90)
            p95_response = response_times.quantile(0.95)
            p99_response = response_times.quantile(0.99)
            p50_response = response_times.quantile(0.50)
            
            # Calculate concurrent users statistics if the column exists
            if 'Concurrent users' in self.df.columns:
                concurrent_users = self.df['Concurrent users'].astype(int)
                max_concurrent = concurrent_users.max()
                avg_concurrent = concurrent_users.mean()
                min_concurrent = concurrent_users.min()
                concurrent_users_over_time = self.df.groupby('Time')['Concurrent users'].mean()
            else:
                # Use Virtual User ID as a fallback for concurrent users
                concurrent_users = self.df.groupby('Time')['Virtual User ID'].nunique()
                max_concurrent = concurrent_users.max()
                avg_concurrent = concurrent_users.mean()
                min_concurrent = concurrent_users.min()
                concurrent_users_over_time = concurrent_users
            
            # Calculate statistics per label (Element)
            label_stats = {}
            for element in self.df['Element'].unique():
                element_data = self.df[self.df['Element'] == element]
                element_times = element_data['Response time'].astype(float)
                
                label_stats[element] = {
                    'count': int(len(element_data)),
                    'error_count': int(len(element_data[element_data['Success'].str.lower() != 'yes'])),
                    'error_rate': float(len(element_data[element_data['Success'].str.lower() != 'yes']) / len(element_data) if len(element_data) > 0 else 0),
                    'min': float(element_times.min()),
                    'max': float(element_times.max()),
                    'mean': float(element_times.mean()),
                    'p50': float(element_times.quantile(0.50)),
                    'p90': float(element_times.quantile(0.90)),
                    'p95': float(element_times.quantile(0.95)),
                    'p99': float(element_times.quantile(0.99))
                }
            
            return {
                'test_duration': test_duration,
                'total_requests': total_requests,
                'error_requests': error_requests,
                'error_rate': error_rate,
                'throughput': throughput,
                'avg_response_time': avg_response,
                'min_response_time': min_response,
                'max_response_time': max_response,
                'p90_response_time': p90_response,
                'p95_response_time': p95_response,
                'p99_response_time': p99_response,
                'p50_response_time': p50_response,
                'max_concurrent_users': max_concurrent,
                'avg_concurrent_users': avg_concurrent,
                'min_concurrent_users': min_concurrent,
                'concurrent_users_over_time': concurrent_users_over_time,
                'label_stats': label_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating NeoLoad statistics: {str(e)}")
            raise
    
    def generate_metrics_table(self) -> str:
        """Generate metrics table in HTML format for Confluence"""
        try:
            metrics = []
            
            # First collect all transaction metrics except ALL TRANSACTIONS
            for element in self.df['Element'].unique():
                transaction_data = self.df[self.df['Element'] == element]
                total = len(transaction_data)
                errors = len(transaction_data[transaction_data['Success'].str.lower() != 'yes'])
                error_rate = (errors / total) * 100 if total > 0 else 0
                response_times = transaction_data['Response time'].astype(float)
                
                # Calculate throughput using actual test duration
                throughput = total / self.test_duration if self.test_duration > 0 else 0
                
                metrics.append({
                    'Transaction': element,
                    'Count': total,
                    'Errors': errors,
                    'Error Rate (%)': f"{error_rate:.2f}%",
                    'Throughput (req/sec)': f"{throughput:.2f}",
                    'Min (ms)': f"{response_times.min():.2f}",
                    'Max (ms)': f"{response_times.max():.2f}",
                    'Avg (ms)': f"{response_times.mean():.2f}",
                    'P90 (ms)': f"{response_times.quantile(0.90):.2f}",
                    'P95 (ms)': f"{response_times.quantile(0.95):.2f}",
                    'P99 (ms)': f"{response_times.quantile(0.99):.2f}"
                })
            
            # Sort metrics by Transaction name
            metrics.sort(key=lambda x: x['Transaction'])
            
            # Add summary row with overall metrics at the beginning
            total_requests = len(self.df)
            total_errors = len(self.df[self.df['Success'].str.lower() != 'yes'])
            overall_error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
            all_response_times = self.df['Response time'].astype(float)
            overall_throughput = total_requests / self.test_duration if self.test_duration > 0 else 0
            
            metrics.insert(0, {
                'Transaction': 'ALL TRANSACTIONS',
                'Count': total_requests,
                'Errors': total_errors,
                'Error Rate (%)': f"{overall_error_rate:.2f}%",
                'Throughput (req/sec)': f"{overall_throughput:.2f}",
                'Min (ms)': f"{all_response_times.min():.2f}",
                'Max (ms)': f"{all_response_times.max():.2f}",
                'Avg (ms)': f"{all_response_times.mean():.2f}",
                'P90 (ms)': f"{all_response_times.quantile(0.90):.2f}",
                'P95 (ms)': f"{all_response_times.quantile(0.95):.2f}",
                'P99 (ms)': f"{all_response_times.quantile(0.99):.2f}"
            })
            
            # Convert to DataFrame
            metrics_df = pd.DataFrame(metrics)
            
            # Generate HTML table with improved styling
            html_table = '''
            <table class="confluenceTable" style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                <tbody>
                    <tr style="background-color: #f0f0f0; font-weight: bold;">
            '''
            
            # Add headers
            for col in metrics_df.columns:
                html_table += f'<th class="confluenceTh" style="padding: 8px; border: 1px solid #ddd; text-align: left;">{col}</th>'
            html_table += '</tr>'
            
            # Add rows
            for _, row in metrics_df.iterrows():
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
            self.logger.error(f"Error generating metrics table: {str(e)}")
            raise

    def generate_concurrent_users_graph(self) -> str:
        """Generate a static graph of concurrent users and response time over time"""
        try:
            # Group by 10-second intervals
            self.df['Time'] = pd.to_datetime(self.df['Time'])
            self.df['TimeInterval'] = self.df['Time'].dt.floor('10S')
            
            # Calculate concurrent users and average response time per interval
            concurrent_users = self.df.groupby('TimeInterval')['Virtual User ID'].nunique()
            avg_response_time = self.df.groupby('TimeInterval')['Response time'].mean()
            
            # Create figure and axis objects with a single subplot
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # Plot concurrent users on primary y-axis
            color1 = '#0052cc'
            ax1.set_xlabel('Time')
            ax1.set_ylabel('Number of Users', color=color1)
            line1 = ax1.plot(concurrent_users.index, concurrent_users.values, color=color1, linewidth=2, label='Concurrent Users')
            ax1.fill_between(concurrent_users.index, concurrent_users.values, alpha=0.1, color=color1)
            ax1.tick_params(axis='y', labelcolor=color1)
            
            # Create secondary y-axis for response time
            ax2 = ax1.twinx()
            color2 = '#36b37e'
            ax2.set_ylabel('Average Response Time (ms)', color=color2)
            line2 = ax2.plot(avg_response_time.index, avg_response_time.values, color=color2, linewidth=2, label='Avg Response Time')
            ax2.tick_params(axis='y', labelcolor=color2)
            
            # Add legend
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='upper left')
            
            # Customize the plot
            plt.title('Concurrent Users and Response Time Over Time (10-second intervals)', pad=20)
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Format x-axis
            plt.gcf().autofmt_xdate()
            
            # Adjust layout
            plt.tight_layout()
            
            # Convert plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f'<img src="data:image/png;base64,{image_base64}" alt="Performance Metrics Graph" style="width: 100%; max-width: 1200px;">'
            
        except Exception as e:
            self.logger.error(f"Error generating performance metrics graph: {str(e)}")
            raise

    def generate_throughput_graph(self) -> str:
        """Generate a static graph of concurrent users and throughput over time"""
        try:
            # Group by 10-second intervals
            self.df['Time'] = pd.to_datetime(self.df['Time'])
            self.df['TimeInterval'] = self.df['Time'].dt.floor('10S')
            
            # Calculate concurrent users and throughput per interval
            concurrent_users = self.df.groupby('TimeInterval')['Virtual User ID'].nunique()
            throughput = self.df.groupby('TimeInterval').size() / 10  # transactions per second
            
            # Create figure and axis objects with a single subplot
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # Plot concurrent users on primary y-axis
            color1 = '#0052cc'
            ax1.set_xlabel('Time')
            ax1.set_ylabel('Number of Users', color=color1)
            line1 = ax1.plot(concurrent_users.index, concurrent_users.values, color=color1, linewidth=2, label='Concurrent Users')
            ax1.fill_between(concurrent_users.index, concurrent_users.values, alpha=0.1, color=color1)
            ax1.tick_params(axis='y', labelcolor=color1)
            
            # Create secondary y-axis for throughput
            ax2 = ax1.twinx()
            color2 = '#ff5630'  # Using a different color for throughput
            ax2.set_ylabel('Transactions Per Second', color=color2)
            line2 = ax2.plot(throughput.index, throughput.values, color=color2, linewidth=2, label='Throughput')
            ax2.tick_params(axis='y', labelcolor=color2)
            
            # Add legend
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='upper left')
            
            # Customize the plot
            plt.title('Concurrent Users and Throughput Over Time (10-second intervals)', pad=20)
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Format x-axis
            plt.gcf().autofmt_xdate()
            
            # Adjust layout
            plt.tight_layout()
            
            # Convert plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f'<img src="data:image/png;base64,{image_base64}" alt="Throughput Graph" style="width: 100%; max-width: 1200px;">'
            
        except Exception as e:
            self.logger.error(f"Error generating throughput graph: {str(e)}")
            raise

    def generate_response_time_graph(self) -> str:
        """Generate a static graph of response times and throughput over time"""
        try:
            # Group by 10-second intervals
            self.df['Time'] = pd.to_datetime(self.df['Time'])
            self.df['TimeInterval'] = self.df['Time'].dt.floor('10S')
            
            # Calculate response time statistics per interval
            response_time_stats = self.df.groupby('TimeInterval')['Response time'].agg(['mean'])
            # Calculate throughput per interval (transactions per second)
            throughput = self.df.groupby('TimeInterval').size() / 10  # 10-second intervals
            
            # Create figure and axis objects
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # Plot average response time on primary y-axis
            color1 = '#0052cc'
            ax1.set_xlabel('Time')
            ax1.set_ylabel('Average Response Time (ms)', color=color1)
            line1 = ax1.plot(response_time_stats.index, response_time_stats['mean'], color=color1, linewidth=2, label='Avg Response Time')
            ax1.tick_params(axis='y', labelcolor=color1)
            
            # Create secondary y-axis for throughput
            ax2 = ax1.twinx()
            color2 = '#ff5630'
            ax2.set_ylabel('Transactions Per Second', color=color2)
            line2 = ax2.plot(throughput.index, throughput.values, color=color2, linewidth=2, label='Throughput (TPS)')
            ax2.tick_params(axis='y', labelcolor=color2)
            
            # Add legend
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='upper left')
            
            # Customize the plot
            ax1.set_title('Response Time and Throughput Over Time (10-second intervals)', pad=20)
            ax1.grid(True, linestyle='--', alpha=0.7)
            
            # Format x-axis
            plt.gcf().autofmt_xdate()
            
            # Adjust layout
            plt.tight_layout()
            
            # Convert plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f'<img src="data:image/png;base64,{image_base64}" alt="Response Time and Throughput Graph" style="width: 100%; max-width: 1200px;">'
            
        except Exception as e:
            self.logger.error(f"Error generating response time graph: {str(e)}")
            raise

    def process(self, test_name: str, environment: str) -> Dict[str, Any]:
        """Process NeoLoad test results and generate reports"""
        try:
            # Store test name and environment
            self.test_name = test_name
            self.environment = environment
            
            # Read and process data
            self.read_data()
            self.stats = self.calculate_overall_stats()
            
            # Get LLM analysis of the results
            llm_analysis = self.ollama_client.analyze_performance_results(self.stats)
            
            # Generate reports
            html_report = self.generate_html_report(test_name, environment, llm_analysis)
            json_report = self.generate_json_report()
            console_table = self.generate_console_table()
            
            return {
                'html_report': html_report,
                'json_report': json_report,
                'console_table': console_table
            }
            
        except Exception as e:
            self.logger.error(f"Error processing NeoLoad results: {str(e)}")
            raise

    def generate_html_report(self, test_name: str, environment: str, llm_analysis: str) -> str:
        """Generate HTML report with LLM analysis"""
        try:
            # Get template
            template = self.template_env.get_template('report_template.html')
            
            # Generate graphs
            response_time_graph = self.generate_response_time_graph()
            throughput_graph = self.generate_throughput_graph()
            concurrent_users_graph = self.generate_concurrent_users_graph()
            
            # Generate metrics table
            metrics_table = self.generate_metrics_table()
            
            # Calculate test times
            test_times = f"{self.actual_start_time.strftime('%Y-%m-%d %H:%M:%S %Z')} to {self.actual_end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
            
            # Render template
            html_content = template.render(
                test_name=test_name,
                environment=environment,
                test_times=test_times,
                test_duration=f"{self.test_duration:.2f} seconds",
                avg_response=f"{self.stats['avg_response_time']:.2f} ms",
                throughput=f"{self.stats['throughput']:.2f} req/sec",
                error_rate=f"{self.stats['error_rate']:.2f}%",
                llm_observations=llm_analysis,
                metrics_table=metrics_table,
                response_time_graph=response_time_graph,
                throughput_graph=throughput_graph,
                concurrent_users_graph=concurrent_users_graph
            )
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {str(e)}")
            raise

    def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON report from NeoLoad data"""
        try:
            # Calculate overall statistics
            stats = self.calculate_overall_stats()
            
            # Get current time in Eastern timezone
            current_time = datetime.now(pytz.UTC).astimezone(self.eastern_tz)
            
            # Convert NumPy types to Python native types
            report = {
                'test_name': self.test_name,
                'environment': self.environment,
                'timestamp': current_time.isoformat(),
                'duration': float(self.test_duration),
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
            self.logger.error(f"Error generating JSON report: {str(e)}")
            raise

    def generate_console_table(self) -> str:
        """Generate console-friendly table for NeoLoad results"""
        try:
            # Create table header
            lines = [
                f"\nTest: {self.test_name}",
                f"Environment: {self.environment}",
                f"Duration: {self.test_duration:.2f} seconds",
                "\nPerformance Metrics:"
            ]
            
            # Define column widths
            col_widths = {
                'Transaction': 30,
                'Count': 8,
                'Errors': 8,
                'Error Rate': 10,
                'Throughput': 12,
                'Min': 10,
                'Max': 10,
                'Avg': 10,
                'P90': 10,
                'P95': 10,
                'P99': 10
            }
            
            # Create header row
            header = "| " + " | ".join(
                f"{col:<{width}}" for col, width in col_widths.items()
            ) + " |"
            
            # Create separator row
            separator = "+" + "+".join("-" * width for width in col_widths.values()) + "+"
            
            lines.extend([separator, header, separator])
            
            # Add overall statistics row
            overall_throughput = self.stats['total_requests'] / self.test_duration if self.test_duration > 0 else 0
            overall_row = "| " + " | ".join([
                "ALL TRANSACTIONS".ljust(col_widths['Transaction']),
                str(self.stats['total_requests']).ljust(col_widths['Count']),
                str(self.stats['error_requests']).ljust(col_widths['Errors']),
                f"{self.stats['error_rate']:.2f}%".ljust(col_widths['Error Rate']),
                f"{overall_throughput:.2f}".ljust(col_widths['Throughput']),
                f"{self.stats['min_response_time']:.2f}".ljust(col_widths['Min']),
                f"{self.stats['max_response_time']:.2f}".ljust(col_widths['Max']),
                f"{self.stats['avg_response_time']:.2f}".ljust(col_widths['Avg']),
                f"{self.stats['p90_response_time']:.2f}".ljust(col_widths['P90']),
                f"{self.stats['p95_response_time']:.2f}".ljust(col_widths['P95']),
                f"{self.stats['p99_response_time']:.2f}".ljust(col_widths['P99'])
            ]) + " |"
            lines.append(overall_row)
            lines.append(separator)
            
            # Sort labels in ascending alphabetical order
            sorted_labels = sorted(self.stats['label_stats'].keys())
            
            # Add rows for each label
            for label in sorted_labels:
                stats = self.stats['label_stats'][label]
                # Calculate throughput for this label
                throughput = stats['count'] / self.test_duration if self.test_duration > 0 else 0
                
                row = "| " + " | ".join([
                    label[:col_widths['Transaction']].ljust(col_widths['Transaction']),
                    str(stats['count']).ljust(col_widths['Count']),
                    str(stats['error_count']).ljust(col_widths['Errors']),
                    f"{stats['error_rate']:.2f}%".ljust(col_widths['Error Rate']),
                    f"{throughput:.2f}".ljust(col_widths['Throughput']),
                    f"{stats['min']:.2f}".ljust(col_widths['Min']),
                    f"{stats['max']:.2f}".ljust(col_widths['Max']),
                    f"{stats['mean']:.2f}".ljust(col_widths['Avg']),
                    f"{stats['p90']:.2f}".ljust(col_widths['P90']),
                    f"{stats['p95']:.2f}".ljust(col_widths['P95']),
                    f"{stats['p99']:.2f}".ljust(col_widths['P99'])
                ]) + " |"
                lines.append(row)
            
            lines.append(separator)
            
            # Add units row
            units_row = "| " + " | ".join([
                "".ljust(col_widths['Transaction']),
                "".ljust(col_widths['Count']),
                "".ljust(col_widths['Errors']),
                "".ljust(col_widths['Error Rate']),
                "req/sec".ljust(col_widths['Throughput']),
                "ms".ljust(col_widths['Min']),
                "ms".ljust(col_widths['Max']),
                "ms".ljust(col_widths['Avg']),
                "ms".ljust(col_widths['P90']),
                "ms".ljust(col_widths['P95']),
                "ms".ljust(col_widths['P99'])
            ]) + " |"
            lines.append(units_row)
            
            return '\n'.join(lines)
            
        except Exception as e:
            self.logger.error(f"Error generating NeoLoad console table: {str(e)}")
            raise