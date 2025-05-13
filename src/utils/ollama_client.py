import json
import logging
import os
import requests
from typing import Dict, Any
import numpy as np
import pandas as pd
from logging.handlers import RotatingFileHandler

# Configure Ollama-specific logger
ollama_logger = logging.getLogger('ollama')
ollama_logger.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure file handler for Ollama logs
file_handler = RotatingFileHandler(
    'logs/ollama.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
ollama_logger.addHandler(file_handler)

def convert_timestamps(obj):
    """Recursively convert any Timestamp objects to strings in both keys and values"""
    try:
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, dict):
            # Convert dictionary keys and values
            return {str(k): convert_timestamps(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_timestamps(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return {str(k): convert_timestamps(v) for k, v in obj.to_dict().items()}
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # For any other type, try to convert to string
            return str(obj)
    except Exception as e:
        ollama_logger.error(f"Error converting object of type {type(obj)}: {str(e)}")
        return str(obj)

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types and pandas timestamps"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super(NumpyEncoder, self).default(obj)

class OllamaClient:
    """Client for interacting with Ollama API to analyze performance test results"""
    
    def __init__(self):
        """Initialize the Ollama client using environment variables"""
        self.base_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.use_ollama = os.getenv('USE_OLLAMA', 'false').lower() == 'true'
        # Strip any comments from the model name
        model = os.getenv('OLLAMA_MODEL', 'llama2')
        self.model = model.split('#')[0].strip()  # Remove any comments and whitespace
        self.api_url = f"{self.base_url.rstrip('/')}/api/generate"
        
        if self.use_ollama:
            ollama_logger.info(f"Ollama client initialized with URL: {self.base_url} and model: {self.model}")
            # Log the full configuration
            ollama_logger.debug(f"Ollama configuration: URL={self.base_url}, Model={self.model}, API URL={self.api_url}")
        else:
            ollama_logger.info("Ollama client initialized but disabled")
        
    def analyze_performance_results(self, json_report: Dict[str, Any]) -> str:
        """Analyze performance test results using Ollama
        
        Args:
            json_report: Dictionary containing the performance test results
            
        Returns:
            str: Analysis of the performance test results
        """
        if not self.use_ollama:
            return "LLM analysis is disabled. Enable by setting USE_OLLAMA=true in .env file."
            
        try:
            # Prepare the prompt for Ollama
            prompt = f"""You are a performance testing expert. Analyze these performance test results and provide a concise summary focusing on:

1. Overall Performance:
   - Test duration and total requests
   - Average response time and throughput
   - Error rate and any concerning patterns

2. Key Metrics:
   - Response time percentiles (P50, P90, P95, P99)
   - Concurrent user behavior
   - Throughput patterns

3. Recommendations:
   - Any potential bottlenecks or issues
   - Areas that might need optimization
   - Suggestions for improvement

Keep the analysis focused on performance metrics and actionable insights. Do not discuss the JSON format or structure.

Test Results:
{json.dumps(json_report, indent=2, cls=NumpyEncoder)}
            """
            
            # Make request to Ollama
            response = requests.post(
                self.api_url,
                json={
                    "model": "llama2",  # or your preferred model
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                ollama_logger.error(f"Ollama API request failed with status {response.status_code}")
                return "Unable to generate analysis at this time."
                
            result = response.json()
            return result.get('response', 'No analysis available.')
            
        except Exception as e:
            ollama_logger.error(f"Error analyzing performance results with Ollama: {str(e)}")
            return "Unable to generate analysis at this time." 