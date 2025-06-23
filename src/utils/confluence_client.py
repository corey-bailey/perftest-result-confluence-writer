import os
import logging
import requests
import html
from typing import Dict, Any
import base64
import urllib3

# Disable SSL warnings since we're using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure Confluence-specific logger
confluence_logger = logging.getLogger('confluence')
confluence_logger.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure file handler for Confluence logs
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(
    'logs/confluence.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
confluence_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

class ConfluenceClient:
    def __init__(self):
        """Initialize Confluence client with configuration from environment variables."""
        self.base_url = os.getenv('CONFLUENCE_URL')
        self.username = os.getenv('CONFLUENCE_USERNAME')
        self.token = os.getenv('CONFLUENCE_TOKEN')
        self.space_key = os.getenv('CONFLUENCE_SPACE_KEY')
        self.logger = confluence_logger
        
        # Validate required environment variables
        if not all([self.base_url, self.username, self.token, self.space_key]):
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
        self.logger.info("Confluence client initialized")
        self.logger.debug(f"Base URL: {self.base_url}")
        self.logger.debug(f"Username: {self.username}")
        self.logger.debug(f"Token: {'*' * len(self.token)}")
        self.logger.debug(f"Space Key: {self.space_key}")
        self.logger.warning("SSL certificate verification is disabled")
        
    def create_page(self, title: str, content: str, parent_id: str = None) -> dict:
        """Create a new page in Confluence."""
        try:
            self.logger.info(f"Attempting to create/update page: {title}")
            
            # First check if page exists
            existing_page = self.get_page_by_title(title)
            if existing_page:
                # Update existing page
                page_id = existing_page['id']
                version = existing_page['version']['number'] + 1
                
                self.logger.info(f"Updating existing page {page_id} to version {version}")
                
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
                
                url = f"{self.base_url}/rest/api/content/{page_id}"
                self.logger.debug(f"PUT request to: {url}")
                self.logger.debug(f"Request data: {data}")
                
                response = requests.put(
                    url,
                    headers=self.headers,
                    json=data,
                    verify=False
                )
                
                self.logger.info(f"Update response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.logger.info(f"Successfully updated page {page_id}")
                    return response.json()
                else:
                    self._log_response_details(response)
                    response.raise_for_status()
            else:
                # Create new page
                self.logger.info("Creating new page")
                
                data = {
                    'title': title,
                    'type': 'page',
                    'space': {'key': self.space_key},
                    'body': {
                        'storage': {
                            'value': content,
                            'representation': 'storage'
                        }
                    }
                }
                
                if parent_id:
                    data['ancestors'] = [{'id': parent_id}]
                
                url = f"{self.base_url}/rest/api/content"
                self.logger.debug(f"POST request to: {url}")
                self.logger.debug(f"Request data: {data}")
                
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    verify=False
                )
                
                self.logger.info(f"Create response status: {response.status_code}")
                
                if response.status_code == 201:
                    result = response.json()
                    self.logger.info(f"Successfully created page {result.get('id', 'unknown')}")
                    return result
                else:
                    self._log_response_details(response)
                    response.raise_for_status()
                    
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise 

    def get_page_by_title(self, title: str) -> dict:
        """Get a page by its title."""
        try:
            self.logger.debug(f"Searching for page with title: {title}")
            
            # Search for pages with the given title
            url = f"{self.base_url}/rest/api/content"
            params = {
                'title': title,
                'spaceKey': self.space_key,
                'type': 'page',
                'expand': 'version'
            }
            
            self.logger.debug(f"GET request to: {url}")
            self.logger.debug(f"Request params: {params}")
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                verify=False
            )
            
            self.logger.debug(f"Search response status: {response.status_code}")
            
            if response.status_code == 200:
                results = response.json()
                if results['results']:
                    page = results['results'][0]
                    self.logger.debug(f"Found existing page: {page['id']}")
                    return page
                else:
                    self.logger.debug("No existing page found")
            else:
                self._log_response_details(response)
                
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching for page: {e}")
            raise
            
    def _log_response_details(self, response: requests.Response) -> None:
        """Log response details for debugging."""
        self.logger.error(f"Response status: {response.status_code}")
        self.logger.error(f"Response headers: {dict(response.headers)}")
        try:
            self.logger.error(f"Response body: {response.json()}")
        except:
            self.logger.error(f"Response body: {response.text}") 