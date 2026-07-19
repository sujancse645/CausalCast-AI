import os
import ast
import re

class BackendAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def analyze(self):
        findings = []
        evidence = []
        
        backend_dir = os.path.join(self.root_dir, "backend")
        if not os.path.exists(backend_dir):
            return {"findings": ["Backend directory not found"], "evidence": []}

        for root, _, files in os.walk(backend_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        # Find routers
                        if "APIRouter(" in content:
                            findings.append(f"Found APIRouter in {file}")
                            evidence.append(filepath)
                            
                        # Find endpoints
                        if "@router." in content or "@app." in content:
                            findings.append(f"Found FastAPI endpoints in {file}")
                            evidence.append(filepath)
                            
                        # Find middleware
                        if "add_middleware(" in content or "BaseHTTPMiddleware" in content:
                            findings.append(f"Found middleware in {file}")
                            evidence.append(filepath)

        return {
            "findings": list(set(findings)),
            "evidence": list(set(evidence))
        }
