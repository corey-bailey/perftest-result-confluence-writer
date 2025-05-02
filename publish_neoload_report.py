#!/usr/bin/env python3

import os
import sys
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime

class NeoLoadReportPublisher:
    def __init__(self, 
                 neoload_token: str,
                 confluence_token: str,
                 workspace_id: str,
                 result_id: str,
                 test_name: str,
                 environment: str,
                 confluence_space_key: str,
                 ancestor_page_id: str,
                 page_title: str):
        self.neoload_token = neoload_token
        self.confluence_token = confluence_token
        self.workspace_id = workspace_id
        self.result_id = result_id
        self.test_name = test_name
        self.environment = environment
        self.confluence_space_key = confluence_space_key
        self.ancestor_page_id = ancestor_page_id
        self.page_title = page_title
        
        # API endpoints
        self.neoload_base_url = "https://neoload-api.saas.neotys.com/v3"
        self.confluence_base_url = "https://your-domain.atlassian.net/wiki/api/v2"

    def get_neoload_results(self) -> Dict[str, Any]:
        """Retrieve test results from NeoLoad API."""
        headers = {
            "Authorization": f"Bearer {self.neoload_token}",
            "Accept": "application/json"
        }
        
        url = f"{self.neoload_base_url}/workspaces/{self.workspace_id}/test-results/{self.result_id}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving NeoLoad results: {str(e)}")
            sys.exit(1)

    def generate_html_table(self, results: Dict[str, Any]) -> str:
        """Generate HTML table from NeoLoad results."""
        html = f"""
        <h2>Performance Test Results</h2>
        <p><strong>Test Name:</strong> {self.test_name}</p>
        <p><strong>Environment:</strong> {self.environment}</p>
        <p><strong>Run Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>User Path</th>
                <th>Elements Per Second</th>
                <th>Element Name</th>
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
        
        # Add data rows (this will need to be adjusted based on actual NeoLoad response structure)
        for path in results.get('userPaths', []):
            html += f"""
            <tr>
                <td>{path.get('name', 'N/A')}</td>
                <td>{path.get('elementsPerSecond', 'N/A')}</td>
                <td>{path.get('elementName', 'N/A')}</td>
                <td>{path.get('min', 'N/A')}</td>
                <td>{path.get('avg', 'N/A')}</td>
                <td>{path.get('max', 'N/A')}</td>
                <td>{path.get('count', 'N/A')}</td>
                <td>{path.get('errors', 'N/A')}</td>
                <td>{path.get('p50', 'N/A')}</td>
                <td>{path.get('p90', 'N/A')}</td>
                <td>{path.get('p95', 'N/A')}</td>
                <td>{path.get('p99', 'N/A')}</td>
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
        'NEOLOAD_API_TOKEN',
        'CONFLUENCE_API_TOKEN',
        'WORKSPACE_ID',
        'RESULT_ID',
        'TEST_NAME',
        'ENVIRONMENT',
        'CONFLUENCE_SPACE_KEY',
        'ANCESTOR_PAGE_ID',
        'PAGE_TITLE'
    ]
    
    # Validate all required variables are present
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Initialize the publisher
    publisher = NeoLoadReportPublisher(
        neoload_token=os.getenv('NEOLOAD_API_TOKEN'),
        confluence_token=os.getenv('CONFLUENCE_API_TOKEN'),
        workspace_id=os.getenv('WORKSPACE_ID'),
        result_id=os.getenv('RESULT_ID'),
        test_name=os.getenv('TEST_NAME'),
        environment=os.getenv('ENVIRONMENT'),
        confluence_space_key=os.getenv('CONFLUENCE_SPACE_KEY'),
        ancestor_page_id=os.getenv('ANCESTOR_PAGE_ID'),
        page_title=os.getenv('PAGE_TITLE')
    )
    
    # Get results from NeoLoad
    results = publisher.get_neoload_results()
    
    # Generate HTML content
    html_content = publisher.generate_html_table(results)
    
    # Create Confluence page
    page_url = publisher.create_confluence_page(html_content)
    
    print(f"Successfully created Confluence page: {page_url}")

if __name__ == "__main__":
    main() 