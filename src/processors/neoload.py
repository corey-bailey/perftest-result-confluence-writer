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

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NeoLoadProcessor(BaseProcessor):
    """Processor for NeoLoad test results"""
    
    def __init__(self, input_file: str):
        """Initialize the NeoLoad processor"""
        super().__init__(input_file)
        self.df = None
        self.test_duration = 0
    
    def read_data(self) -> None:
        """Read and process NeoLoad CSV data"""
        try:
            # Read CSV with semicolon separator
            self.df = pd.read_csv(self.input_file, sep=';')
            
            # Convert timestamp
            self.df['Time'] = pd.to_datetime(self.df['Time'])
            
            # Calculate test duration in seconds
            self.test_duration = (self.df['Time'].max() - self.df['Time'].min()).total_seconds()
            
            logger.debug(f"Read {len(self.df)} rows from NeoLoad CSV file")
            logger.debug(f"Test duration: {self.test_duration} seconds")
            
            return self.df
        except Exception as e:
            logger.error(f"Error reading NeoLoad CSV file: {str(e)}")
            raise
    
    def calculate_overall_stats(self) -> Dict[str, Any]:
        """Calculate overall statistics from NeoLoad data"""
        try:
            # Calculate basic statistics
            total_requests = len(self.df)
            error_requests = len(self.df[self.df['Success'].str.lower() != 'yes'])
            error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0
            
            # Calculate test duration and throughput
            test_duration = (self.df['Time'].max() - self.df['Time'].min()).total_seconds()
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
                'max_concurrent_users': max_concurrent,
                'avg_concurrent_users': avg_concurrent,
                'min_concurrent_users': min_concurrent,
                'concurrent_users_over_time': concurrent_users_over_time
            }
            
        except Exception as e:
            logger.error(f"Error calculating NeoLoad statistics: {str(e)}")
            raise
    
    def generate_metrics_table(self) -> str:
        """Generate metrics table in HTML format for Confluence"""
        try:
            metrics = []
            test_duration = (self.df['Time'].max() - self.df['Time'].min()).total_seconds()
            
            for element in self.df['Element'].unique():
                transaction_data = self.df[self.df['Element'] == element]
                total = len(transaction_data)
                errors = len(transaction_data[transaction_data['Success'].str.lower() != 'yes'])
                error_rate = (errors / total) * 100 if total > 0 else 0
                response_times = transaction_data['Response time'].astype(float)
                
                # Calculate transaction duration and throughput
                transaction_duration = (transaction_data['Time'].max() - transaction_data['Time'].min()).total_seconds()
                throughput = total / transaction_duration if transaction_duration > 0 else 0
                
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
            
            # Add summary row with overall metrics
            total_requests = len(self.df)
            total_errors = len(self.df[self.df['Success'].str.lower() != 'yes'])
            overall_error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
            all_response_times = self.df['Response time'].astype(float)
            overall_throughput = total_requests / test_duration if test_duration > 0 else 0
            
            metrics.append({
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
            logger.error(f"Error generating metrics table: {str(e)}")
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
            logger.error(f"Error generating performance metrics graph: {str(e)}")
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
            logger.error(f"Error generating throughput graph: {str(e)}")
            raise

    def process(self, test_name: str, environment: str) -> Dict[str, Any]:
        """Process test results and generate reports"""
        try:
            # Store test name and environment
            self.test_name = test_name
            self.environment = environment
            
            # Read and validate data
            self.read_data()
            
            # Calculate statistics
            overall_stats = self.calculate_overall_stats()
            
            # Generate metrics table
            metrics_table = self.generate_metrics_table()
            
            # Generate graphs
            response_time_graph = self.generate_concurrent_users_graph()
            throughput_graph = self.generate_throughput_graph()
            
            # Prepare data for reporters
            report_data = {
                'start_time': self.df['Time'].min(),
                'end_time': self.df['Time'].max(),
                'test_duration': overall_stats['test_duration'],
                'total_requests': overall_stats['total_requests'],
                'error_requests': overall_stats['error_requests'],
                'error_rate': overall_stats['error_rate'],
                'throughput': overall_stats['throughput'],
                'min_response_time': overall_stats['min_response_time'],
                'max_response_time': overall_stats['max_response_time'],
                'avg_response_time': overall_stats['avg_response_time'],
                'p90_response_time': overall_stats['p90_response_time'],
                'p95_response_time': overall_stats['p95_response_time'],
                'p99_response_time': overall_stats['p99_response_time'],
                'max_concurrent_users': overall_stats['max_concurrent_users'],
                'avg_concurrent_users': overall_stats['avg_concurrent_users'],
                'min_concurrent_users': overall_stats['min_concurrent_users'],
                'metrics_table': metrics_table,
                'response_time_graph': response_time_graph,
                'throughput_graph': throughput_graph,
                'metrics': {
                    'transactions': [
                        {
                            'name': element,
                            'count': len(self.df[self.df['Element'] == element]),
                            'errors': len(self.df[(self.df['Element'] == element) & (self.df['Success'].str.lower() != 'yes')]),
                            'error_rate': len(self.df[(self.df['Element'] == element) & (self.df['Success'].str.lower() != 'yes')]) / len(self.df[self.df['Element'] == element]) if len(self.df[self.df['Element'] == element]) > 0 else 0,
                            'throughput': len(self.df[self.df['Element'] == element]) / overall_stats['test_duration'] if overall_stats['test_duration'] > 0 else 0,
                            'min_response_time': self.df[self.df['Element'] == element]['Response time'].min(),
                            'max_response_time': self.df[self.df['Element'] == element]['Response time'].max(),
                            'avg_response_time': self.df[self.df['Element'] == element]['Response time'].mean(),
                            'p90_response_time': self.df[self.df['Element'] == element]['Response time'].quantile(0.90),
                            'p95_response_time': self.df[self.df['Element'] == element]['Response time'].quantile(0.95),
                            'p99_response_time': self.df[self.df['Element'] == element]['Response time'].quantile(0.99)
                        }
                        for element in self.df['Element'].unique()
                    ]
                }
            }
            
            # Initialize reporters
            from src.reporters import HTMLReporter, JSONReporter, ConsoleReporter
            html_reporter = HTMLReporter()
            json_reporter = JSONReporter()
            console_reporter = ConsoleReporter()
            
            # Generate reports
            html_report = html_reporter.generate_report(report_data, test_name, environment)
            json_report = json_reporter.generate_report(report_data, test_name, environment)
            console_table = console_reporter.generate_report(report_data, test_name, environment)
            
            return {
                'html_report': html_report,
                'json_report': json_report,
                'console_table': console_table,
                'overall_stats': overall_stats
            }
            
        except Exception as e:
            logger.error(f"Error processing test results: {str(e)}")
            raise