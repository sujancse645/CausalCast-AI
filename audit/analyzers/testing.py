import os
import re

class TestingAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def analyze(self):
        findings = []
        evidence = []
        
        for root, dirs, files in os.walk(self.root_dir):
            # Skip common ignores
            if "node_modules" in root or ".venv" in root or "venv" in root or ".git" in root:
                continue
                
            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx")) and ("test" in file or "spec" in file):
                    filepath = os.path.join(root, file)
                    evidence.append(filepath)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            if "pytest" in content or "def test_" in content:
                                findings.append(f"Found pytest usage in {file}")
                            if "describe(" in content or "it(" in content or "test(" in content:
                                if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                                    findings.append(f"Found JS/TS testing usage in {file}")
                            if "playwright" in content or "page.goto(" in content:
                                findings.append(f"Found Playwright usage in {file}")
                    except Exception as e:
                        pass

        return {
            "findings": list(set(findings)),
            "evidence": list(set(evidence))
        }
