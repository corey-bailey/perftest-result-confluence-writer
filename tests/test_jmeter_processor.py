#!/usr/bin/env python3

import os
import json
import pytest
import pandas as pd
from datetime import datetime
from src.processors.jmeter import JMeterProcessor

class TestJMeterProcessor:
    """Test JMeter processor"""
    
    @pytest.fixture
    def sample_jtl_data(self, tmp_path):
        """Create a sample JTL file with test data from actual JMeter results"""
        jtl_file = tmp_path / "test.jtl"
        
        # Read the actual JMeter results file
        with open("tests/test_data/jmeter_sample_results.jtl", "r") as f:
            content = f.read()
            
        # Write the content to the temporary file
        with open(jtl_file, "w") as f:
            f.write(content)
            
        return str(jtl_file)
    
    @pytest.fixture
    def sample_template(self, tmp_path):
        """Create a sample template file"""
        template_dir = tmp_path / "config" / "templates"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "report_template.html"
        
        # Read the sample template content
        with open("tests/test_data/sample_template.html", "r") as f:
            content = f.read()
            
        # Write the content to the temporary file
        with open(template_file, "w") as f:
            f.write(content)
            
        return template_file
    
    @pytest.fixture
    def processor(self, sample_jtl_data, sample_template):
        """Create a JMeterProcessor instance with the sample data"""
        processor = JMeterProcessor(sample_jtl_data)
        processor.template_dir = str(sample_template.parent)
        return processor
    
    def test_read_data(self, processor):
        """Test reading JTL data"""
        processor.read_data()
        assert processor.data is not None
        assert len(processor.data) > 0
        assert 'timeStamp' in processor.data.columns
        assert 'elapsed' in processor.data.columns
        assert 'label' in processor.data.columns
        assert 'responseCode' in processor.data.columns
        assert 'success' in processor.data.columns
    
    def test_calculate_overall_stats(self, processor):
        """Test calculating overall statistics"""
        processor.read_data()
        stats = processor.calculate_overall_stats()
        assert stats is not None
        assert 'total_requests' in stats
        assert 'error_requests' in stats
        assert 'error_rate' in stats
        assert 'avg_response_time' in stats
        assert 'min_response_time' in stats
        assert 'max_response_time' in stats
        assert 'test_duration' in stats
    
    def test_generate_metrics_table(self, processor):
        """Test generating metrics table"""
        processor.read_data()
        metrics_table = processor.generate_metrics_table()
        assert metrics_table is not None
        assert isinstance(metrics_table, str)
        assert '<table' in metrics_table
        assert '</table>' in metrics_table
        assert 'Transaction' in metrics_table
        assert 'Count' in metrics_table
        assert 'Error Rate' in metrics_table
    
    def test_generate_html_report(self, processor, sample_template):
        """Test generating HTML report"""
        processor.read_data()
        html_report = processor.generate_html_report("Test Run", "Production")
        assert html_report is not None
        assert isinstance(html_report, str)
        assert 'Test Run' in html_report
        assert 'Production' in html_report
        assert '<table' in html_report
        assert '</table>' in html_report
    
    def test_generate_json_report(self, processor):
        """Test generating JSON report"""
        processor.read_data()
        json_report = processor.generate_json_report("Test Run", "Production")
        assert json_report is not None
        assert isinstance(json_report, dict)
        assert 'test_name' in json_report
        assert 'environment' in json_report
        assert 'overall_stats' in json_report
        assert 'metrics' in json_report
    
    def test_generate_console_table(self, processor):
        """Test generating console table"""
        processor.read_data()
        console_table = processor.generate_console_table()
        assert console_table is not None
        assert isinstance(console_table, str)
        assert 'Transaction' in console_table
        assert 'Count' in console_table
        assert 'Error Rate' in console_table
    
    def test_process(self, processor, sample_template):
        """Test processing test results"""
        result = processor.process("Test Run", "Production")
        assert result is not None
        assert isinstance(result, dict)
        assert 'html_report' in result
        assert 'json_report' in result
        assert 'console_table' in result
        assert isinstance(result['html_report'], str)
        assert isinstance(result['json_report'], dict)
        assert isinstance(result['console_table'], str) 