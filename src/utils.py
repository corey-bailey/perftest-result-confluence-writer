import os
import json
import pandas as pd
from typing import Tuple, Optional

def detect_file_type(file_path: str) -> Tuple[str, Optional[str]]:
    """
    Detect the type of performance test result file.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Tuple containing:
        - File type ('jmeter', 'k6', 'neoload', or 'unknown')
        - Error message if detection fails, None otherwise
    """
    if not os.path.exists(file_path):
        return 'unknown', f"File not found: {file_path}"
        
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # Check JMeter (.jtl or .csv)
        if file_ext in ['.jtl', '.csv']:
            df = pd.read_csv(file_path)
            # Check for JMeter specific columns
            if all(col in df.columns for col in ['timeStamp', 'elapsed', 'label', 'responseCode', 'success']):
                return 'jmeter', None
                
            # Check for NeoLoad specific columns (if CSV)
            if file_ext == '.csv' and all(col in df.columns for col in ['Time', 'Element', 'Response time', 'Success']):
                return 'neoload', None
                
        # Check k6 (.json)
        elif file_ext == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Check for k6 specific structure
                if 'metrics' in data and isinstance(data['metrics'], list):
                    for metric in data['metrics']:
                        if metric.get('type') == 'Point' and metric.get('metric') == 'http_req_duration':
                            return 'k6', None
                            
        return 'unknown', f"Unable to determine file type for: {file_path}"
        
    except Exception as e:
        return 'unknown', f"Error analyzing file {file_path}: {str(e)}"

def get_processor_class(file_type: str):
    """
    Get the appropriate processor class based on the file type.
    
    Args:
        file_type: Type of file ('jmeter', 'k6', or 'neoload')
        
    Returns:
        Processor class or None if file type is unknown
    """
    from src.processors.jmeter import JMeterProcessor
    from src.processors.k6 import K6Processor
    from src.processors.neoload import NeoLoadProcessor
    
    processors = {
        'jmeter': JMeterProcessor,
        'k6': K6Processor,
        'neoload': NeoLoadProcessor
    }
    
    return processors.get(file_type) 