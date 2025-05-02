#!/usr/bin/env python3

import os
import sys
import json
import requests
from typing import Dict, Any, List
from datetime import datetime

class K6ReportPublisher:
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

    def parse_k6_results(self, k6_content: str) -> List[Dict[str, Any]]:
        """Parse K6 JSON results and extract metrics."""
        try:
            data = json.loads(k6_content)
        except json.JSONDecodeError as e:
            print(f"Error parsing K6 JSON: {str(e)}")
            sys.exit(1)

        results = []
        
        # Process metrics from the root level
        metrics = data.get('metrics', {})
        
        # Extract HTTP metrics
        http_metrics = {
            'http_req_duration': metrics.get('http_req_duration', {}),
            'http_reqs': metrics.get('http_reqs', {}),
            'http_req_failed': metrics.get('http_req_failed', {})
        }
        
        # Process each HTTP metric
        for metric_name, metric_data in http_metrics.items():
            if not metric_data:
                continue
                
            result = {
                'label': metric_name,
                'count': metric_data.get('count', 0),
                'errors': 0,  # Will be calculated for failed requests
                'min': metric_data.get('min', 0),
                'max': metric_data.get('max', 0),
                'avg': metric_data.get('avg', 0),
                'p50': metric_data.get('med', 0),  # K6 uses 'med' for median
                'p90': metric_data.get('p90', 0),
                'p95': metric_data.get('p95', 0),
                'p99': metric_data.get('p99', 0),
                'throughput': metric_data.get('rate', 0)  # K6 provides rate directly
            }
            
            # Calculate errors for failed requests
            if metric_name == 'http_req_failed':
                result['errors'] = metric_data.get('value', 0)
            
            results.append(result)
        
        # Add summary metrics
        summary = {
            'label': 'Summary',
            'count': metrics.get('iterations', {}).get('count', 0),
            'errors': metrics.get('errors', {}).get('count', 0),
            'min': 0,  # Not applicable for summary
            'max': 0,  # Not applicable for summary
            'avg': 0,  # Not applicable for summary
            'p50': 0,  # Not applicable for summary
            'p90': 0,  # Not applicable for summary
            'p95': 0,  # Not applicable for summary
            'p99': 0,  # Not applicable for summary
            'throughput': metrics.get('iterations', {}).get('rate', 0)
        }
        results.append(summary)
        
        return results

    def generate_html_table(self, results: List[Dict[str, Any]]) -> str:
        """Generate HTML table from K6 results."""
        html = f"""
        <h2>K6 Performance Test Results</h2>
        <p><strong>Test Name:</strong> {self.test_name}</p>
        <p><strong>Environment:</strong> {self.environment}</p>
        <p><strong>Run Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>Metric</th>
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
        'K6_CONTENT'
    ]
    
    # Validate all required variables are present
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Initialize the publisher
    publisher = K6ReportPublisher(
        confluence_token=os.getenv('CONFLUENCE_API_TOKEN'),
        test_name=os.getenv('TEST_NAME'),
        environment=os.getenv('ENVIRONMENT'),
        confluence_space_key=os.getenv('CONFLUENCE_SPACE_KEY'),
        ancestor_page_id=os.getenv('ANCESTOR_PAGE_ID'),
        page_title=os.getenv('PAGE_TITLE')
    )
    
    # Parse K6 content
    k6_content = os.getenv('K6_CONTENT')
    results = publisher.parse_k6_results(k6_content)
    
    # Generate HTML content
    html_content = publisher.generate_html_table(results)
    
    # Create Confluence page
    page_url = publisher.create_confluence_page(html_content)
    
    print(f"Successfully created Confluence page: {page_url}")

if __name__ == "__main__":
    main() 