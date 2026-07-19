import json
import os
from datetime import datetime

class MarkdownReporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate(self, data: dict):
        report_path = os.path.join(self.output_dir, "release-report.md")
        
        md = [
            "# CausalCast AI Release Audit Report",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            "## Executive Summary",
            "This report summarizes the autonomous QA and repository audit findings.",
            "",
            "## Repository Inventory"
        ]
        
        inventory = data.get("inventory", {})
        for ext, count in inventory.items():
            md.append(f"- **{ext}**: {count} files")
            
        md.append("")
        md.append("## Test Results")
        test_results = data.get("test_results", {})
        md.append(f"Backend exit code: {test_results.get('exit_code')}")
        
        md.append("")
        md.append("## Findings")
        findings = data.get("repository_findings", [])
        if not findings:
            md.append("No critical findings.")
        else:
            for f in findings:
                md.append(f"- **{f.get('id')}**: {f.get('title')} ({f.get('severity')})")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
            
        print(f"Markdown report generated at {report_path}")
