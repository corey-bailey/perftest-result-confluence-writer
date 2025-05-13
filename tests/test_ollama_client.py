import os
import pytest
import json
from unittest.mock import patch, MagicMock
from src.utils.ollama_client import OllamaClient, NumpyEncoder

@pytest.fixture
def sample_performance_data():
    """Create sample performance test data for analysis (mimics real NeoLoad JSON report)"""
    return {
        "test_name": "NeoLoad Test",
        "environment": "Test Environment",
        "timestamp": "2025-05-13T10:55:03.351284-04:00",
        "duration": 1797.846,
        "overall_stats": {
            "total_requests": 6079,
            "error_requests": 9,
            "error_rate": 0.14805066622799803,
            "throughput": 3.381268473495505,
            "min_response_time": 5.0,
            "max_response_time": 10034.0,
            "avg_response_time": 101.6126007567034,
            "p50_response_time": 7.0,
            "p90_response_time": 18.0,
            "p95_response_time": 181.1999999999989,
            "p99_response_time": 2664.2600000000084
        },
        "label_stats": {
            "S01_T01_Category": {
                "count": 14,
                "error_count": 0,
                "error_rate": 0.0,
                "min": 6.0,
                "max": 15.0,
                "mean": 8.785714285714286,
                "p50": 8.0,
                "p90": 11.400000000000002,
                "p95": 13.049999999999999,
                "p99": 14.609999999999998
            },
            "Crt AH Screen Response": {
                "count": 86,
                "error_count": 0,
                "error_rate": 0.0,
                "min": 5.0,
                "max": 42.0,
                "mean": 8.55813953488372,
                "p50": 7.0,
                "p90": 10.5,
                "p95": 19.5,
                "p99": 30.950000000000074
            },
            "Crt LL Screen Response": {
                "count": 28,
                "error_count": 8,
                "error_rate": 0.2857142857142857,
                "min": 37.0,
                "max": 10034.0,
                "mean": 2929.75,
                "p50": 121.5,
                "p90": 10014.8,
                "p95": 10019.0,
                "p99": 10029.95
            }
        }
    }

def test_ollama_client_initialization():
    """Test Ollama client initialization with default values"""
    with patch.dict(os.environ, {}, clear=True):
        client = OllamaClient()
        assert client.base_url == 'http://localhost:11434'
        assert client.api_url == 'http://localhost:11434/api/generate'
        assert client.use_ollama is False

def test_ollama_client_initialization_with_env_vars():
    """Test Ollama client initialization with environment variables"""
    with patch.dict(os.environ, {
        'OLLAMA_URL': 'http://custom-url:11434',
        'USE_OLLAMA': 'true'
    }):
        client = OllamaClient()
        assert client.base_url == 'http://custom-url:11434'
        assert client.api_url == 'http://custom-url:11434/api/generate'
        assert client.use_ollama is True

def test_analyze_performance_results_disabled():
    """Test performance analysis when Ollama is disabled"""
    with patch.dict(os.environ, {}, clear=True):
        client = OllamaClient()
        result = client.analyze_performance_results({})
        assert result == "LLM analysis is disabled. Enable by setting USE_OLLAMA=true in .env file."

@patch('requests.post')
def test_analyze_performance_results_success(mock_post, sample_performance_data):
    """Test successful performance analysis with Ollama"""
    # Mock the Ollama API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Test analysis result"}
    mock_post.return_value = mock_response

    # Enable Ollama
    with patch.dict(os.environ, {'USE_OLLAMA': 'true'}):
        client = OllamaClient()
        result = client.analyze_performance_results(sample_performance_data)
        
        # Verify the result
        assert result == "Test analysis result"
        
        # Verify the API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]['json']
        assert call_args['model'] == 'llama2'
        assert 'prompt' in call_args
        assert 'Test Results:' in call_args['prompt']
        
        # Verify the pretty-printed JSON data is in the prompt
        json_data = json.dumps(sample_performance_data, indent=2, cls=NumpyEncoder)
        assert json_data in call_args['prompt']

@patch('requests.post')
def test_analyze_performance_results_api_error(mock_post, sample_performance_data):
    """Test performance analysis when Ollama API returns an error"""
    # Mock the Ollama API error response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    # Enable Ollama
    with patch.dict(os.environ, {'USE_OLLAMA': 'true'}):
        client = OllamaClient()
        result = client.analyze_performance_results(sample_performance_data)
        
        # Verify the error handling
        assert result == "Unable to generate analysis at this time."

@patch('requests.post')
def test_analyze_performance_results_exception(mock_post, sample_performance_data):
    """Test performance analysis when an exception occurs"""
    # Mock an exception during the API call
    mock_post.side_effect = Exception("Test exception")

    # Enable Ollama
    with patch.dict(os.environ, {'USE_OLLAMA': 'true'}):
        client = OllamaClient()
        result = client.analyze_performance_results(sample_performance_data)
        
        # Verify the error handling
        assert result == "Unable to generate analysis at this time."

def test_numpy_encoder():
    """Test the custom JSON encoder for numpy types"""
    import numpy as np
    import pandas as pd
    
    # Create test data with numpy types
    test_data = {
        'integer': np.int64(42),
        'float': np.float64(3.14),
        'array': np.array([1, 2, 3]),
        'series': pd.Series([1, 2, 3])
    }
    
    # Encode the data
    encoded = json.dumps(test_data, cls=NumpyEncoder)
    decoded = json.loads(encoded)
    
    # Verify the encoding
    assert decoded['integer'] == 42
    assert decoded['float'] == 3.14
    assert decoded['array'] == [1, 2, 3]
    assert decoded['series'] == {'0': 1, '1': 2, '2': 3}  # Pandas Series indices are strings 