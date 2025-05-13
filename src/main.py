#!/usr/bin/env python3

import os
import sys
import json
import logging
import argparse
from datetime import datetime
import pytz
from typing import Dict, Any, Optional

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from processors.jmeter import JMeterProcessor
from processors.neoload import NeoLoadProcessor
from utils.confluence_client import ConfluenceClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CONFLUENCE_PARENT_PAGE_ID = os.getenv('CONFLUENCE_PARENT_PAGE_ID')
EASTERN_TZ = pytz.timezone('US/Eastern')

def save_report_files(results: Dict[str, Any], output_dir: str) -> None:
    """Save report files to disk"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for filenames in Eastern timezone
        timestamp = datetime.now(pytz.UTC).astimezone(EASTERN_TZ).strftime('%Y%m%d_%H%M%S')
        
        # Save HTML report
        html_file = os.path.join(output_dir, f'report_{timestamp}.html')
        with open(html_file, 'w') as f:
            f.write(results['html_report'])
        logger.info(f"HTML report saved to: {html_file}")
        
        # Save JSON report
        json_file = os.path.join(output_dir, f'report_{timestamp}.json')
        with open(json_file, 'w') as f:
            json.dump(results['json_report'], f, indent=2)
        logger.info(f"JSON report saved to: {json_file}")
        
        # Save console output
        txt_file = os.path.join(output_dir, f'report_{timestamp}.txt')
        with open(txt_file, 'w') as f:
            f.write(results['console_table'])
        logger.info(f"Console output saved to: {txt_file}")
        
    except Exception as e:
        logger.error(f"Error saving report files: {str(e)}")
        raise

def update_confluence(report_html: str, test_name: str, environment: str, confluence_client: ConfluenceClient) -> None:
    """Update Confluence with test results"""
    try:
        # Create page title with Eastern timezone timestamp
        current_time = datetime.now(pytz.UTC).astimezone(EASTERN_TZ)
        page_title = f"{test_name} - {environment} - {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        
        # Create page in Confluence
        confluence_client.create_page(
            title=page_title,
            content=report_html,
            parent_id=CONFLUENCE_PARENT_PAGE_ID
        )
        
        logger.info(f"Successfully updated Confluence page: {page_title}")
    except Exception as e:
        logger.error(f"Error updating Confluence: {str(e)}")
        raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Process performance test results')
    parser.add_argument('--input-file', required=True, help='Input file path')
    parser.add_argument('--test-name', required=True, help='Test name')
    parser.add_argument('--environment', required=True, help='Test environment')
    parser.add_argument('--processor', required=True, choices=['jmeter', 'neoload'], help='Processor type')
    parser.add_argument('--output-dir', default='reports', help='Output directory')
    
    args = parser.parse_args()
    
    try:
        # Initialize appropriate processor
        if args.processor == 'jmeter':
            processor = JMeterProcessor(args.input_file)
        elif args.processor == 'neoload':
            processor = NeoLoadProcessor(args.input_file)
        else:
            raise ValueError(f"Unsupported processor type: {args.processor}")
            
        # Process results
        results = processor.process(args.test_name, args.environment)
        
        # Save report files
        save_report_files(results, args.output_dir)
        
        # Update Confluence if environment variables are set
        if all([os.getenv('CONFLUENCE_URL'), 
                os.getenv('CONFLUENCE_USERNAME'),
                os.getenv('CONFLUENCE_TOKEN'),
                os.getenv('CONFLUENCE_SPACE_ID'),
                os.getenv('CONFLUENCE_ANCESTOR_PAGE_ID')]):
            try:
                confluence_client = ConfluenceClient()
                update_confluence(
                    report_html=results['html_report'],
                    test_name=args.test_name,
                    environment=args.environment,
                    confluence_client=confluence_client
                )
            except Exception as e:
                logger.error(f"Error processing results: {str(e)}")
                sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error processing results: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 