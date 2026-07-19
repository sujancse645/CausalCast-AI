import argparse
import os
import sys

# Ensure the project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json

import yaml
from audit.analyzers.repository import RepositoryAnalyzer
from audit.collectors.command_runner import run_command


def load_config():
    with open("audit/config/audit_config.yaml") as f:
        return yaml.safe_load(f)


def run_quick_profile(config):
    print("Running quick audit...")
    repo_analyzer = RepositoryAnalyzer(os.getcwd())
    repo_results = repo_analyzer.audit()

    # Run tests
    print("Running backend tests...")
    test_result = run_command(config["audit"]["commands"]["backend_test"], timeout=300)
    print(f"Backend test exit code: {test_result.returncode}")

    print("Running backend linting...")
    lint_result = run_command(config["audit"]["commands"]["backend_lint"], timeout=300)

    return {
        "repository_findings": repo_results.get("findings", []),
        "inventory": repo_results.get("inventory", {}),
        "test_results": test_result.model_dump(),
        "lint_results": lint_result.model_dump(),
    }


def main():
    parser = argparse.ArgumentParser(description="Autonomous QA, Repository Audit, and Release Intelligence")
    parser.add_argument("--profile", choices=["quick", "full", "security", "release"], default="quick")
    parser.add_argument("--output-dir", default="reports/audit/latest")
    parser.add_argument("--no-ai-summary", action="store_true")
    args = parser.parse_args()

    config = load_config()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Starting {args.profile} audit...")

    results = {}
    if args.profile == "quick":
        results = run_quick_profile(config)

    output_path = os.path.join(args.output_dir, "release-report.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    # Generate Markdown Report
    try:
        from audit.reporters.executive_summary import ExecutiveSummaryReporter
        from audit.reporters.markdown_reporter import MarkdownReporter

        md_reporter = MarkdownReporter(args.output_dir)
        md_reporter.generate(results)

        exec_reporter = ExecutiveSummaryReporter(args.output_dir)
        exec_reporter.generate(results)
    except Exception as e:
        print(f"Failed to generate reports: {e}")

    print(f"Audit complete. Results written to {output_path}")


if __name__ == "__main__":
    main()
