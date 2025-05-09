import os
import pandas as pd
import json
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseProcessor:
    """Base class for processing performance test results"""
    
    def __init__(self, input_file: str):
        """
        Initialize the processor
        
        Args:
            input_file: Path to the input file
        """
        self.input_file = input_file
        self.data = None
        self.overall_stats = None
        
        # Get the absolute path to the templates directory
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        logger.debug(f"Current directory: {current_dir}")
        
        template_dir = os.path.abspath(os.path.join(current_dir, 'config', 'templates'))
        logger.debug(f"Looking for templates in: {template_dir}")
        
        if not os.path.exists(template_dir):
            logger.error(f"Template directory does not exist: {template_dir}")
            # List contents of parent directory to help debug
            parent_dir = os.path.dirname(template_dir)
            if os.path.exists(parent_dir):
                logger.error(f"Contents of {parent_dir}:")
                for item in os.listdir(parent_dir):
                    logger.error(f"  - {item}")
            raise Exception(f"Template directory not found: {template_dir}")
            
        template_file = os.path.join(template_dir, 'report_template.html')
        logger.debug(f"Looking for template file: {template_file}")
        
        if not os.path.exists(template_file):
            logger.error(f"Template file not found: {template_file}")
            # List contents of template directory to help debug
            logger.error(f"Contents of {template_dir}:")
            for item in os.listdir(template_dir):
                logger.error(f"  - {item}")
            raise Exception(f"Template file not found: {template_file}")
            
        logger.info(f"Found template file: {template_file}")
        
        try:
            # Create the Jinja2 environment with the absolute path
            self.template_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=True
            )
            # Test template loading
            self.template_env.get_template('report_template.html')
            logger.info("Template environment initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing template environment: {str(e)}")
            raise
        
    def read_data(self) -> None:
        """Read and parse the input file"""
        raise NotImplementedError
        
    def calculate_overall_stats(self) -> Dict[str, Any]:
        """Calculate overall statistics"""
        raise NotImplementedError
        
    def generate_metrics_table(self) -> str:
        """Generate HTML table with metrics"""
        raise NotImplementedError
        
    def generate_html_report(self, test_name: str, environment: str) -> str:
        """
        Generate HTML report
        
        Args:
            test_name: Name of the test
            environment: Environment where the test was run
            
        Returns:
            HTML report as string
        """
        try:
            logger.info("Attempting to load template...")
            template = self.template_env.get_template('report_template.html')
            logger.info("Template loaded successfully")
            
            logger.info("Rendering template...")
            html = template.render(
                test_name=test_name,
                environment=environment,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                total_requests=self.overall_stats['total_requests'],
                total_errors=self.overall_stats['error_requests'],
                error_rate=f"{self.overall_stats['error_rate']:.2%}",
                throughput=f"{self.overall_stats.get('throughput', 0):.2f}",
                min_response=f"{self.overall_stats['min_response_time']:.2f}",
                max_response=f"{self.overall_stats['max_response_time']:.2f}",
                avg_response=f"{self.overall_stats['avg_response_time']:.2f}",
                p50_response=f"{self.overall_stats.get('p50_response_time', 0):.2f}",
                p90_response=f"{self.overall_stats.get('p90_response_time', 0):.2f}",
                p95_response=f"{self.overall_stats.get('p95_response_time', 0):.2f}",
                p99_response=f"{self.overall_stats.get('p99_response_time', 0):.2f}",
                metrics_table=self.generate_metrics_table()
            )
            logger.info("Template rendered successfully")
            return html
            
        except Exception as e:
            logger.error(f"Error in generate_html_report: {str(e)}")
            raise Exception(f"Error reading template: {str(e)}")
            
    def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON report"""
        raise NotImplementedError
        
    def generate_console_table(self) -> str:
        """Generate console-friendly table"""
        raise NotImplementedError
        
    def process(self, test_name: str, environment: str) -> Dict[str, Any]:
        """
        Process the test results
        
        Args:
            test_name: Name of the test
            environment: Environment where the test was run
            
        Returns:
            Dictionary containing generated reports
        """
        self.read_data()
        self.overall_stats = self.calculate_overall_stats()
        
        return {
            'html_report': self.generate_html_report(test_name, environment),
            'json_report': self.generate_json_report(),
            'console_table': self.generate_console_table()
        } 