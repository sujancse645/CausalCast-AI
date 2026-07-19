import json
import os

class ExecutiveSummaryReporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate(self, data: dict):
        report_path = os.path.join(self.output_dir, "executive-summary.md")
        
        md = [
            "# Executive Summary",
            "",
            "## Overall Assessment",
            "This report is generated deterministically by the Autonomous Auditor.",
            ""
        ]
        
        inventory = data.get("inventory", {})
        md.append(f"**Total Python Files**: {inventory.get('.py', 0)}")
        md.append(f"**Total TypeScript Files**: {inventory.get('.ts', 0) + inventory.get('.tsx', 0)}")
        
        test_results = data.get("test_results", {})
        md.append(f"**Backend Test Status**: {'PASS' if test_results.get('returncode') == 0 else 'FAIL'}")
        
        md.append("")
        md.append("## Next Actions (Deterministic)")
        md.append("1. Address any critical security findings.")
        md.append("2. Ensure E2E tests pass before deployment.")
        md.append("3. Review performance bottlenecks.")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
            
        print(f"Executive summary generated at {report_path}")
