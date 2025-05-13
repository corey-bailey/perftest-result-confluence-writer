import os
import logging
import requests
import html
from typing import Dict, Any
import base64

logger = logging.getLogger(__name__)

class ConfluenceClient:
    def __init__(self):
        """Initialize Confluence client with configuration from environment variables."""
        self.base_url = os.getenv('CONFLUENCE_URL')
        self.username = os.getenv('CONFLUENCE_USERNAME')
        self.token = os.getenv('CONFLUENCE_TOKEN')
        self.space_id = os.getenv('CONFLUENCE_SPACE_ID')
        self.logger = logger
        
        # Validate required environment variables
        if not all([self.base_url, self.username, self.token, self.space_id]):
            raise ValueError("Missing required Confluence environment variables")
        
        # Set up headers for API calls
        auth_str = f"{self.username}:{self.token}"
        auth_bytes = auth_str.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {base64_auth}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Log configuration (masking sensitive data)
        self.logger.debug(f"Base URL: {self.base_url}")
        self.logger.debug(f"Username: {self.username}")
        self.logger.debug(f"Token: {'*' * len(self.token)}")
        self.logger.debug(f"Space ID: {self.space_id}")
        
    def create_page(self, title: str, content: str, parent_id: str = None) -> dict:
        """Create a new page in Confluence."""
        try:
            # First check if page exists
            existing_page = self.get_page_by_title(title)
            if existing_page:
                # Update existing page
                page_id = existing_page['id']
                version = existing_page['version']['number'] + 1
                
                data = {
                    'version': {'number': version},
                    'title': title,
                    'type': 'page',
                    'body': {
                        'storage': {
                            'value': content,
                            'representation': 'storage'
                        }
                    }
                }
                
                if parent_id:
                    data['ancestors'] = [{'id': parent_id}]
                
                response = requests.put(
                    f"{self.base_url}/wiki/api/v2/pages/{page_id}",
                    headers=self.headers,
                    json=data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    self._log_response_details(response)
                    response.raise_for_status()
            else:
                # Create new page
                data = {
                    'title': title,
                    'type': 'page',
                    'spaceId': self.space_id,
                    'body': {
                        'storage': {
                            'value': content,
                            'representation': 'storage'
                        }
                    }
                }
                
                if parent_id:
                    data['ancestors'] = [{'id': parent_id}]
                
                response = requests.post(
                    f"{self.base_url}/wiki/api/v2/pages",
                    headers=self.headers,
                    json=data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    self._log_response_details(response)
                    response.raise_for_status()
                    
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise 

    def get_page_by_title(self, title: str) -> dict:
        """Get a page by its title."""
        try:
            # Search for pages with the given title
            response = requests.get(
                f"{self.base_url}/wiki/api/v2/pages",
                headers=self.headers,
                params={
                    'title': title,
                    'space-id': self.space_id,
                    'type': 'page'
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                if results['results']:
                    return results['results'][0]
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching for page: {e}")
            raise
            
    def _log_response_details(self, response: requests.Response) -> None:
        """Log response details for debugging."""
        self.logger.error(f"Response status: {response.status_code}")
        self.logger.error(f"Response headers: {response.headers}")
        try:
            self.logger.error(f"Response body: {response.json()}")
        except:
            self.logger.error(f"Response body: {response.text}") 