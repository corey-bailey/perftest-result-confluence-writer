import os
import pytest
import shutil
from pathlib import Path

@pytest.fixture
def sample_jtl_data(tmp_path):
    """Create a sample JTL file for testing"""
    jtl_file = tmp_path / "jmeter_results.jtl"
    src_file = Path("tests/test_data/jmeter_sample_results.jtl")
    shutil.copy(src_file, jtl_file)
    return str(jtl_file)

@pytest.fixture
def sample_k6_data(tmp_path):
    """Create a sample k6 JSON file for testing"""
    json_file = tmp_path / "k6_results.json"
    src_file = Path("tests/test_data/k6_sample_results.json")
    shutil.copy(src_file, json_file)
    return str(json_file)

@pytest.fixture
def sample_neoload_data(tmp_path):
    """Create a sample NeoLoad CSV file for testing"""
    csv_file = tmp_path / "neoload_results.csv"
    src_file = Path("tests/test_data/neoload_sample_results.csv")
    shutil.copy(src_file, csv_file)
    return str(csv_file)

@pytest.fixture
def sample_template(tmp_path):
    """Create a sample HTML template for testing"""
    template_dir = tmp_path / "config" / "templates"
    template_dir.mkdir(parents=True)
    template_file = template_dir / "report_template.html"
    
    template_content = """<!DOCTYPE html>
<html>
<head>
    <title>Performance Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ test_name }}</h1>
        <h2>Environment: {{ environment }}</h2>
        
        <div class="overall-stats">
            <h3>Overall Statistics</h3>
            <p>Total Requests: {{ overall_stats.total_requests }}</p>
            <p>Error Requests: {{ overall_stats.error_requests }}</p>
            <p>Error Rate: {{ "%.2f"|format(overall_stats.error_rate) }}%</p>
            <p>Average Response Time: {{ "%.2f"|format(overall_stats.avg_response_time) }} ms</p>
            <p>Min Response Time: {{ "%.2f"|format(overall_stats.min_response_time) }} ms</p>
            <p>Max Response Time: {{ "%.2f"|format(overall_stats.max_response_time) }} ms</p>
            <p>Test Duration: {{ "%.2f"|format(overall_stats.test_duration) }} seconds</p>
        </div>
        
        <div class="metrics-table">
            <h3>Transaction Metrics</h3>
            {{ metrics_table|safe }}
        </div>
    </div>
</body>
</html>"""
    
    template_file.write_text(template_content)
    return template_file 