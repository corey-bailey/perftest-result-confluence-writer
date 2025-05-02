#!/usr/bin/env python3

import os
import sys
import json
import requests
import csv
from typing import Dict, Any, List
from datetime import datetime
from io import StringIO

class JMeterReportPublisher:
    def __init__(self, 
                 confluence_token: str,
                 test_name: str,
                 environment: str,
                 confluence_space_key: str,
                 ancestor_page_id: str,
                 page_title: str):
        self.confluence_token = confluence_token
        self.test_name = test_name
        self.environment = environment
        self.confluence_space_key = confluence_space_key
        self.ancestor_page_id = ancestor_page_id
        self.page_title = page_title
        
        # API endpoints
        self.confluence_base_url = "https://your-domain.atlassian.net/wiki/api/v2"

    def parse_jtl_file(self, jtl_content: str) -> List[Dict[str, Any]]:
        """Parse JMeter JTL file content and extract metrics."""
        results = []
        csv_reader = csv.DictReader(StringIO(jtl_content))
        
        # Group results by label (test name)
        label_groups = {}
        for row in csv_reader:
            label = row.get('label', 'Unknown')
            if label not in label_groups:
                label_groups[label] = {
                    'count': 0,
                    'errors': 0,
                    'response_times': []
                }
            
            group = label_groups[label]
            group['count'] += 1
            
            # Check for errors
            if row.get('success', '').lower() == 'false':
                group['errors'] += 1
            
            # Add response time
            try:
                response_time = float(row.get('elapsed', 0))
                group['response_times'].append(response_time)
            except ValueError:
                continue
        
        # Calculate statistics for each group
        for label, group in label_groups.items():
            response_times = group['response_times']
            if not response_times:
                continue
                
            response_times.sort()
            count = len(response_times)
            
            result = {
                'label': label,
                'count': group['count'],
                'errors': group['errors'],
                'min': min(response_times),
                'max': max(response_times),
                'avg': sum(response_times) / count,
                'p50': response_times[int(count * 0.5)],
                'p90': response_times[int(count * 0.9)],
                'p95': response_times[int(count * 0.95)],
                'p99': response_times[int(count * 0.99)],
                'throughput': group['count'] / (max(response_times) - min(response_times)) if len(response_times) > 1 else 0
            }
            results.append(result)
        
        return results

    def generate_html_table(self, results: List[Dict[str, Any]]) -> str:
        """Generate HTML table from JMeter results."""
        html = f"""
        <h2>JMeter Performance Test Results</h2>
        <p><strong>Test Name:</strong> {self.test_name}</p>
        <p><strong>Environment:</strong> {self.environment}</p>
        <p><strong>Run Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>Test Name</th>
                <th>Throughput (req/sec)</th>
                <th>Min (ms)</th>
                <th>Avg (ms)</th>
                <th>Max (ms)</th>
                <th>Count</th>
                <th>Errors</th>
                <th>P50 (ms)</th>
                <th>P90 (ms)</th>
                <th>P95 (ms)</th>
                <th>P99 (ms)</th>
            </tr>
        """
        
        for result in results:
            html += f"""
            <tr>
                <td>{result['label']}</td>
                <td>{result['throughput']:.2f}</td>
                <td>{result['min']:.2f}</td>
                <td>{result['avg']:.2f}</td>
                <td>{result['max']:.2f}</td>
                <td>{result['count']}</td>
                <td>{result['errors']}</td>
                <td>{result['p50']:.2f}</td>
                <td>{result['p90']:.2f}</td>
                <td>{result['p95']:.2f}</td>
                <td>{result['p99']:.2f}</td>
            </tr>
            """
        
        html += "</table>"
        return html

    def create_confluence_page(self, html_content: str) -> str:
        """Create a new page in Confluence with the test results."""
        headers = {
            "Authorization": f"Basic {self.confluence_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "type": "page",
            "title": self.page_title,
            "space": {"key": self.confluence_space_key},
            "ancestors": [{"id": self.ancestor_page_id}],
            "body": {
                "storage": {
                    "value": html_content,
                    "representation": "storage"
                }
            }
        }
        
        url = f"{self.confluence_base_url}/pages"
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get('_links', {}).get('webui', '')
        except requests.exceptions.RequestException as e:
            print(f"Error creating Confluence page: {str(e)}")
            sys.exit(1)

def main():
    # Get required environment variables
    required_vars = [
        'CONFLUENCE_API_TOKEN',
        'TEST_NAME',
        'ENVIRONMENT',
        'CONFLUENCE_SPACE_KEY',
        'ANCESTOR_PAGE_ID',
        'PAGE_TITLE',
        'JTL_CONTENT'
    ]
    
    # Validate all required variables are present
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Initialize the publisher
    publisher = JMeterReportPublisher(
        confluence_token=os.getenv('CONFLUENCE_API_TOKEN'),
        test_name=os.getenv('TEST_NAME'),
        environment=os.getenv('ENVIRONMENT'),
        confluence_space_key=os.getenv('CONFLUENCE_SPACE_KEY'),
        ancestor_page_id=os.getenv('ANCESTOR_PAGE_ID'),
        page_title=os.getenv('PAGE_TITLE')
    )
    
    # Parse JTL content
    jtl_content = os.getenv('JTL_CONTENT')
    results = publisher.parse_jtl_file(jtl_content)
    
    # Generate HTML content
    html_content = publisher.generate_html_table(results)
    
    # Create Confluence page
    page_url = publisher.create_confluence_page(html_content)
    
    print(f"Successfully created Confluence page: {page_url}")

if __name__ == "__main__":
    main() 