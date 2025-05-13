#!/usr/bin/env python3

import os
import sys
import logging
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from jinja2 import Environment, FileSystemLoader, Template

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class BaseProcessor(ABC):
    """Base class for all processors"""
    
    def __init__(self, input_file: str):
        """Initialize the processor"""
        self.input_file = input_file
        self.test_name = None
        self.environment = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'templates')
        self.template_env = Environment(loader=FileSystemLoader(template_dir))
    
    @abstractmethod
    def read_data(self) -> None:
        """Read and process input data"""
        pass
    
    @abstractmethod
    def calculate_overall_stats(self) -> Dict[str, Any]:
        """Calculate overall statistics from data"""
        pass
    
    @abstractmethod
    def process(self, test_name: str, environment: str) -> Dict[str, Any]:
        """Process test results and generate reports"""
        pass
    
    def read_template(self) -> Template:
        """Read HTML template file"""
        try:
            env = Environment(loader=FileSystemLoader(self.template_dir))
            template = env.get_template('report_template.html')
            return template
        except Exception as e:
            raise FileNotFoundError(f"Error reading template: {str(e)}")
    
    def _read_template(self) -> str:
        """Read the HTML template file with error handling"""
        template_path = os.path.join('config', 'templates', 'report_template.html')
        try:
            with open(template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.error(f"Template file not found at {template_path}")
            raise FileNotFoundError(f"Template file not found at {template_path}. Please ensure the template exists in the config/templates directory.")
        except Exception as e:
            self.logger.error(f"Error reading template file: {e}")
            raise 