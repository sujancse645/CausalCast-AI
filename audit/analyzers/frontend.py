import os
import re

class FrontendAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def analyze(self):
        findings = []
        evidence = []
        
        frontend_dir = os.path.join(self.root_dir, "frontend")
        if not os.path.exists(frontend_dir):
            return {"findings": ["Frontend directory not found"], "evidence": []}

        for root, _, files in os.walk(frontend_dir):
            for file in files:
                if file.endswith((".tsx", ".ts", ".js", ".jsx")):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            
                            # API clients / fetches
                            if "fetch(" in content or "axios" in content or "useQuery" in content:
                                findings.append(f"Found API client usage in {file}")
                                evidence.append(filepath)
                                
                            # Pages/Components (Next.js app router or pages router)
                            if "export default function" in content or "export const" in content:
                                if "page.tsx" in file or "layout.tsx" in file:
                                    findings.append(f"Found Next.js page/layout in {file}")
                                    evidence.append(filepath)
                    except Exception as e:
                        pass

        return {
            "findings": list(set(findings)),
            "evidence": list(set(evidence))
        }
