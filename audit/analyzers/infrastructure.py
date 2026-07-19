import os

def analyze_infrastructure(repo_path):
    findings = []
    dockerfile_path = os.path.join(repo_path, 'Dockerfile')
    if os.path.exists(dockerfile_path):
        findings.append("Found Dockerfile")
        with open(dockerfile_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'latest' in content.lower():
                findings.append("Warning: Dockerfile uses 'latest' tag.")
    else:
        findings.append("No Dockerfile found.")

    compose_path = os.path.join(repo_path, 'docker-compose.yml')
    if os.path.exists(compose_path):
        findings.append("Found docker-compose.yml")
    else:
        findings.append("No docker-compose.yml found.")

    workflows_dir = os.path.join(repo_path, '.github', 'workflows')
    if os.path.exists(workflows_dir):
        workflows = os.listdir(workflows_dir)
        findings.append(f"Found GitHub Actions workflows: {', '.join(workflows)}")
    else:
        findings.append("No GitHub Actions CI/CD workflows found.")

    return {"status": "completed", "findings": findings}
