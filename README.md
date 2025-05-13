# Performance Test Result Confluence Writer

A Python application that processes performance test results from various tools (JMeter, k6, NeoLoad) and generates formatted reports for Confluence.

## Features

- Supports multiple performance testing tools:
  - JMeter (.jtl files)
  - k6 (.json files)
  - NeoLoad (.csv files)
- Automatic file type detection
- Generates multiple report formats:
  - HTML reports
  - JSON reports
  - Console tables
  - Metrics tables
- Detailed statistics including:
  - Response times (min, max, average)
  - Error rates
  - Transaction counts
  - Test duration
  - Concurrent users over time
  - Throughput analysis
- GitHub Actions workflow for automated report generation and publishing
- Optional LLM analysis of test results using Ollama

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/perftest-result-confluence-writer.git
cd perftest-result-confluence-writer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in editable mode:
```bash
pip install -e .
```

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration:
     ```
     # Confluence Configuration
     CONFLUENCE_URL=https://your-domain.atlassian.net
     CONFLUENCE_USERNAME=your-email@example.com
     CONFLUENCE_TOKEN=your-api-token
     CONFLUENCE_SPACE_ID=your-space-id
     CONFLUENCE_ANCESTOR_PAGE_ID=your-ancestor-page-id

     # Ollama Configuration (Optional)
     OLLAMA_URL=http://localhost:11434
     USE_OLLAMA=true
     OLLAMA_MODEL=llama2  # Specify which Ollama model to use (defaults to llama2)
     ```

## Usage

### Local Usage

The application automatically detects the type of performance test result file based on its extension and content structure. Run the application using:

```bash
python src/main.py --input-file path/to/results/file --test-name "Test Name" --environment "Environment" --processor [jmeter|k6|neoload] --output-dir reports
```

### Command Line Arguments

- `--input-file`: Path to the performance test results file (required)
- `--test-name`: Name of the test run (required)
- `--environment`: Environment where the test was run (required)
- `--processor`: Type of processor to use (optional, auto-detected if not specified)
- `--output-dir`: Directory to save reports (optional)

Example:
```bash
python src/main.py --input-file tests/test_data/jmeter_sample_results.jtl --test-name "Load Test" --environment "Production" --processor jmeter --output-dir reports
```

### LLM Analysis with Ollama

The application can optionally use Ollama to analyze performance test results and provide insights. To enable this:

1. Install and run Ollama locally or on a server
2. Set the following environment variables in `.env`:
   - `OLLAMA_URL`: URL of your Ollama server (default: http://localhost:11434)
   - `USE_OLLAMA`: Set to "true" to enable LLM analysis

The LLM analysis will appear at the top of the HTML report and in the Confluence page.

### GitHub Actions Workflow

The project includes a GitHub Actions workflow for automated report generation and publishing to Confluence. To use it:

1. Add the following secrets to your GitHub repository:
   - `CONFLUENCE_API_TOKEN`: Your Confluence API token
   - `CONFLUENCE_URL`: Your Confluence instance URL
   - `OLLAMA_URL`: (Optional) Your Ollama server URL
   - `USE_OLLAMA`: (Optional) Set to "true" to enable LLM analysis

2. Manually trigger the workflow from the Actions tab with the following inputs:
   - `workspace_id`: NeoLoad Workspace ID
   - `result_id`: NeoLoad Result ID
   - `test_name`: Name of the test
   - `environment`: Test environment (e.g., DEV, QA, PROD)
   - `confluence_space_key`: Confluence Space Key
   - `ancestor_page_id`: Parent Confluence Page ID
   - `page_title`: Title for the new Confluence page

The workflow will:
1. Set up Python and install dependencies
2. Run the report generator
3. Publish the report to Confluence

### Supported File Types

1. **JMeter Results (.jtl or .csv)**
   - Must contain columns: timeStamp, elapsed, label, responseCode, success
   - Example: `results.jtl`

2. **k6 Results (.json)**
   - Must contain metrics array with http_req_duration points
   - Example: `results.json`

3. **NeoLoad Results (.csv)**
   - Must contain columns: Time, Element, Response time, Success
   - Example: `results.csv`

## Output

The application generates:
1. Console output showing test results
2. HTML report with detailed metrics and graphs
3. JSON report for programmatic access
4. Metrics table for quick analysis
5. LLM analysis (if enabled)

## Development

### Project Structure
```
perftest-result-confluence-writer/
├── src/
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── base_processor.py
│   │   ├── jmeter.py
│   │   ├── k6.py
│   │   └── neoload.py
│   ├── reporters/
│   │   ├── __init__.py
│   │   ├── html_reporter.py
│   │   ├── json_reporter.py
│   │   └── console_reporter.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── confluence_client.py
│   │   └── ollama_client.py
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── test_data/
│   │   ├── jmeter_sample_results.jtl
│   │   ├── k6_sample_results.json
│   │   └── neoload_sample_results.csv
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_jmeter_processor.py
│   ├── test_k6_processor.py
│   └── test_neoload_processor.py
├── .github/
│   └── workflows/
│       └── publish_neoload_report.yml
├── setup.py
└── README.md
```

### Running Tests

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 