import json
import logging
import os
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API to analyze performance test results"""
    
    def __init__(self):
        """Initialize the Ollama client using environment variables"""
        self.base_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.use_ollama = os.getenv('USE_OLLAMA', 'false').lower() == 'true'
        self.api_url = f"{self.base_url.rstrip('/')}/api/generate"
        
        if self.use_ollama:
            logger.info(f"Ollama client initialized with URL: {self.base_url}")
        else:
            logger.info("Ollama client initialized but disabled")
        
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
            prompt = f"""Please analyze these performance test results and provide a high-level summary of the key observations. 
            Focus on important metrics like response times, error rates, throughput, and any concerning patterns.
            Keep the analysis concise and actionable.
            
            Test Results:
            {json.dumps(json_report, indent=2)}
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
                logger.error(f"Ollama API request failed with status {response.status_code}")
                return "Unable to generate analysis at this time."
                
            result = response.json()
            return result.get('response', 'No analysis available.')
            
        except Exception as e:
            logger.error(f"Error analyzing performance results with Ollama: {str(e)}")
            return "Unable to generate analysis at this time." 