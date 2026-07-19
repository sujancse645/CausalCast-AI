import os
import json

def analyze_dependencies(repo_path):
    findings = []
    req_path = os.path.join(repo_path, 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            deps = f.readlines()
            findings.append(f"Found {len(deps)} lines in requirements.txt")
            for dep in deps:
                dep_stripped = dep.strip()
                if dep_stripped and not dep_stripped.startswith('#') and '==' not in dep_stripped:
                    findings.append(f"Unpinned dependency in requirements.txt: {dep_stripped}")
    else:
        findings.append("No requirements.txt found.")

    pkg_path = os.path.join(repo_path, 'package.json')
    if os.path.exists(pkg_path):
        with open(pkg_path, 'r', encoding='utf-8') as f:
            try:
                pkg = json.load(f)
                deps = pkg.get('dependencies', {})
                dev_deps = pkg.get('devDependencies', {})
                findings.append(f"Found {len(deps)} dependencies and {len(dev_deps)} devDependencies in package.json")
            except json.JSONDecodeError:
                findings.append("Failed to parse package.json")
    else:
        findings.append("No package.json found.")

    return {"status": "completed", "findings": findings}
