import os
import re

def analyze_ai_pipeline(repo_path):
    findings = []
    ai_keywords = ['baseline', 'gradient boosting', 'xgboost', 'lightgbm', 'random forest', 'hyperparameters']
    metric_patterns = [(r'(accuracy|precision|recall|f1|mse|rmse)\s*=\s*[0-9\.]+', "Potential hardcoded metric found")]

    has_ai_code = False
    for root, _, files in os.walk(repo_path):
        if '.git' in root or 'node_modules' in root or 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for kw in ai_keywords:
                            if kw in content.lower():
                                has_ai_code = True
                                findings.append(f"Found AI keyword '{kw}' in {os.path.relpath(path, repo_path)}")
                        
                        for pattern, desc in metric_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                findings.append(f"{desc} in {os.path.relpath(path, repo_path)}")
                except Exception:
                    pass
    
    if not has_ai_code:
        findings.append("No significant AI pipeline code found (baselines, gradient boosting).")
    
    return {"status": "completed", "findings": findings}
