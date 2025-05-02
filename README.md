# Performance Test Report Publisher

This project automates the process of publishing performance test results from various tools (NeoLoad, JMeter, and K6) to Confluence Cloud. It consists of Python scripts and GitHub Actions workflows that retrieve test results and create formatted report pages in Confluence.

## Supported Tools

The project supports three major performance testing tools:

1. **NeoLoad**
   - Retrieves results via NeoLoad Web API
   - Requires NeoLoad API token
   - Supports detailed timing metrics and percentiles

2. **JMeter**
   - Processes JTL (JMeter Test Log) files
   - Calculates comprehensive statistics
   - Supports grouping by test name

3. **K6**
   - Processes JSON output from K6
   - Handles K6-specific metrics
   - Includes HTTP request statistics

## Prerequisites

- Python 3.8 or higher
- GitHub repository with Actions enabled
- Confluence Cloud API token
- Tool-specific requirements:
  - NeoLoad: NeoLoad API token
  - JMeter: JTL file output
  - K6: JSON output file

## Setup

1. Clone this repository

2. Add the following secrets to your GitHub repository:
   - `CONFLUENCE_API_TOKEN`: Your Confluence Cloud API token (Base64 encoded)
   - `NEOLOAD_API_TOKEN`: Your NeoLoad API token (for NeoLoad reports only)

3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### NeoLoad Reports

1. Navigate to your GitHub repository's Actions tab
2. Select the "Publish NeoLoad Report" workflow
3. Click "Run workflow"
4. Fill in the required inputs:
   - Workspace ID: Your NeoLoad workspace ID
   - Result ID: The ID of the test result to publish
   - Test Name: Name of the performance test
   - Environment: Test environment (e.g., DEV, QA, PROD)
   - Confluence Space Key: Your Confluence space key
   - Ancestor Page ID: ID of the parent page in Confluence
   - Page Title: Title for the new report page

### JMeter Reports

1. Run your JMeter test and save the results as a JTL file
2. Add the JTL file to your repository
3. Go to the Actions tab
4. Select "Publish JMeter Report"
5. Fill in the required inputs:
   - JTL file path: Path to your JTL file in the repository
   - Test Name: Name of the test
   - Environment: Test environment
   - Confluence Space Key: Your Confluence space key
   - Ancestor Page ID: ID of the parent page
   - Page Title: Title for the new report page

### K6 Reports

1. Run your K6 test with JSON output:
   ```bash
   k6 run --out json=results.json your-test.js
   ```
2. Add the JSON file to your repository
3. Go to the Actions tab
4. Select "Publish K6 Report"
5. Fill in the required inputs:
   - K6 JSON file path: Path to your JSON file in the repository
   - Test Name: Name of the test
   - Environment: Test environment
   - Confluence Space Key: Your Confluence space key
   - Ancestor Page ID: ID of the parent page
   - Page Title: Title for the new report page

## Report Contents

Each report includes:

### Common Elements
- Test name and environment
- Run timestamp
- Formatted HTML table with metrics

### Tool-Specific Metrics

#### NeoLoad
- User Path metrics
- Elements Per Second
- Min, Avg, Max response times
- Percentiles (50, 90, 95, 99)
- Error counts

#### JMeter
- Test name grouping
- Throughput (requests/second)
- Response time statistics
- Error rates
- Percentiles
- Request counts

#### K6
- HTTP request duration metrics
- Request counts and rates
- Error statistics
- Iteration metrics
- Summary statistics

## Error Handling

The scripts include comprehensive error handling for:
- Missing environment variables
- API authentication failures
- Invalid file formats
- Network errors
- Data parsing errors

Any errors will cause the workflow to fail with a descriptive error message.

## Security

- API tokens are stored as GitHub Secrets
- All API calls use HTTPS
- No credentials are stored in the code or repository
- File contents are handled securely in GitHub Actions

## Contributing

Feel free to submit issues and enhancement requests! When contributing, please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 