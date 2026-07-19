import os

def analyze_performance(repo_path):
    findings = []
    # Check for large files / bundle sizes
    for root, _, files in os.walk(repo_path):
        if '.git' in root or 'node_modules' in root or 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path)
                if size > 5 * 1024 * 1024:  # > 5MB
                    findings.append(f"Large file found: {os.path.relpath(path, repo_path)} ({size / 1024 / 1024:.2f} MB)")
            except OSError:
                pass
    
    # Check if there's any test report with timing
    pytest_cache = os.path.join(repo_path, '.pytest_cache')
    if os.path.exists(pytest_cache):
        findings.append("Pytest cache found, performance timings may be available in local test runs.")
    else:
        findings.append("No .pytest_cache found, unable to extract local test timings.")

    return {"status": "completed", "findings": findings}
