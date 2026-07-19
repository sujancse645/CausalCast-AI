import os
import re

def analyze_security(repo_path):
    findings = []
    secret_patterns = [
        (r'(?i)(api[_-]?key|secret|password|token)\s*(:|=)\s*[\'"][^\'"]+[\'"]', "Potential hardcoded secret"),
        (r'AKIA[0-9A-Z]{16}', "Potential AWS Access Key"),
    ]
    cors_patterns = [
        (r'allow_origins\s*=\s*\[\s*["\']\*["\']\s*\]', "Weak CORS policy: allow_origins=['*']")
    ]
    
    for root, _, files in os.walk(repo_path):
        if '.git' in root or 'node_modules' in root or 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith(('.py', '.ts', '.js', '.json', '.yml', '.yaml')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern, desc in secret_patterns:
                            if re.search(pattern, content):
                                findings.append(f"{desc} in {os.path.relpath(path, repo_path)}")
                        for pattern, desc in cors_patterns:
                            if re.search(pattern, content):
                                findings.append(f"{desc} in {os.path.relpath(path, repo_path)}")
                except Exception:
                    pass
    return {"status": "completed", "findings": findings}
