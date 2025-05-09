#!/usr/bin/env python3

import os
from datetime import datetime
from typing import Dict, Any, List

class HTMLReportGenerator:
    def __init__(self, template_path: str = "templates/report_template.html"):
        self.template_path = template_path
        self._load_template()

    def _load_template(self) -> None:
        """Load the HTML template file."""
        try:
            with open(self.template_path, 'r') as f:
                self.template = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found at {self.template_path}")

    def generate_metrics_table(self, results: List[Dict[str, Any]], tool: str) -> str:
        """Generate the metrics table HTML based on the tool type."""
        if tool == "neoload":
            return self._generate_neoload_table(results)
        elif tool == "jmeter":
            return self._generate_jmeter_table(results)
        elif tool == "k6":
            return self._generate_k6_table(results)
        else:
            raise ValueError(f"Unsupported tool type: {tool}")

    def _generate_neoload_table(self, results: List[Dict[str, Any]]) -> str:
        """Generate table HTML for NeoLoad results."""
        html = """
        <table>
            <tr>
                <th>User Path</th>
                <th>Elements Per Second</th>
                <th>Element Name</th>
                <th>Min (ms)</th>
                <th>Avg (ms)</th>
                <th>Max (ms)</th>
                <th>Count</th>
                <th>Errors</th>
                <th>P50 (ms)</th>
                <th>P90 (ms)</th>
                <th>P95 (ms)</th>
                <th>P99 (ms)</th>
            </tr>
        """
        
        for result in results:
            html += f"""
            <tr>
                <td>{result['label']}</td>
                <td>{result['elements_per_second']:.2f}</td>
                <td>{result['element_name']}</td>
                <td>{result['min']:.2f}</td>
                <td>{result['avg']:.2f}</td>
                <td>{result['max']:.2f}</td>
                <td>{result['count']}</td>
                <td>{result['errors']}</td>
                <td>{result['p50']:.2f}</td>
                <td>{result['p90']:.2f}</td>
                <td>{result['p95']:.2f}</td>
                <td>{result['p99']:.2f}</td>
            </tr>
            """
        
        html += "</table>"
        return html

    def _generate_jmeter_table(self, results: List[Dict[str, Any]]) -> str:
        """Generate table HTML for JMeter results."""
        html = """
        <table>
            <tr>
                <th>Test Name</th>
                <th>Throughput (transactions/sec)</th>
                <th>Min (ms)</th>
                <th>Avg (ms)</th>
                <th>Max (ms)</th>
                <th>Count</th>
                <th>Errors</th>
                <th>P50 (ms)</th>
                <th>P90 (ms)</th>
                <th>P95 (ms)</th>
                <th>P99 (ms)</th>
            </tr>
        """
        
        for result in results:
            html += f"""
            <tr>
                <td>{result['label']}</td>
                <td>{result['throughput']:.2f}</td>
                <td>{result['min']:.2f}</td>
                <td>{result['avg']:.2f}</td>
                <td>{result['max']:.2f}</td>
                <td>{result['count']}</td>
                <td>{result['errors']}</td>
                <td>{result['p50']:.2f}</td>
                <td>{result['p90']:.2f}</td>
                <td>{result['p95']:.2f}</td>
                <td>{result['p99']:.2f}</td>
            </tr>
            """
        
        html += "</table>"
        return html

    def _generate_k6_table(self, results: List[Dict[str, Any]]) -> str:
        """Generate table HTML for K6 results."""
        html = """
        <table>
            <tr>
                <th>Metric</th>
                <th>Throughput (transactions/sec)</th>
                <th>Min (ms)</th>
                <th>Avg (ms)</th>
                <th>Max (ms)</th>
                <th>Count</th>
                <th>Errors</th>
                <th>P50 (ms)</th>
                <th>P90 (ms)</th>
                <th>P95 (ms)</th>
                <th>P99 (ms)</th>
            </tr>
        """
        
        for result in results:
            html += f"""
            <tr>
                <td>{result['label']}</td>
                <td>{result['throughput']:.2f}</td>
                <td>{result['min']:.2f}</td>
                <td>{result['avg']:.2f}</td>
                <td>{result['max']:.2f}</td>
                <td>{result['count']}</td>
                <td>{result['errors']}</td>
                <td>{result['p50']:.2f}</td>
                <td>{result['p90']:.2f}</td>
                <td>{result['p95']:.2f}</td>
                <td>{result['p99']:.2f}</td>
            </tr>
            """
        
        html += "</table>"
        return html

    def calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary metrics from the results."""
        total_requests = sum(r['count'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        
        # Calculate weighted average response time
        total_time = sum(r['avg'] * r['count'] for r in results)
        avg_response_time = total_time / total_requests if total_requests > 0 else 0
        
        # Get the highest 95th percentile
        p95_response_time = max(r['p95'] for r in results) if results else 0
        
        # Calculate overall throughput
        throughput = sum(r['throughput'] for r in results)
        
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'avg_response_time': avg_response_time,
            'p95_response_time': p95_response_time,
            'throughput': throughput
        }

    def generate_report(self, 
                       test_name: str,
                       environment: str,
                       results: List[Dict[str, Any]],
                       tool: str) -> str:
        """Generate the complete HTML report."""
        metrics_table = self.generate_metrics_table(results, tool)
        summary = self.calculate_summary(results)
        
        # Format the template with the actual values
        report = self.template.format(
            test_name=test_name,
            environment=environment,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            metrics_table=metrics_table,
            total_requests=summary['total_requests'],
            total_errors=summary['total_errors'],
            avg_response_time=f"{summary['avg_response_time']:.2f}",
            p95_response_time=f"{summary['p95_response_time']:.2f}",
            throughput=f"{summary['throughput']:.2f}"
        )
        
        return report 