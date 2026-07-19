import os
from typing import List, Dict, Any

class RepositoryAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def audit(self) -> Dict[str, Any]:
        """Runs the repository audit."""
        findings = []
        file_counts = {}
        
        for root, dirs, files in os.walk(self.root_dir):
            if '.git' in root or 'node_modules' in root or '__pycache__' in root or '.next' in root:
                continue
                
            for file in files:
                ext = os.path.splitext(file)[1] or "no_extension"
                file_counts[ext] = file_counts.get(ext, 0) + 1
                
                path = os.path.join(root, file)
                # Check for placeholders
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "TODO" in content or "FIXME" in content or "HACK" in content or "XXX" in content:
                            findings.append({
                                "id": f"REP-TODO-{os.path.basename(path)}",
                                "title": f"Placeholder or technical debt in {os.path.basename(path)}",
                                "category": "Repository Health",
                                "severity": "INFORMATIONAL",
                                "file": path,
                            })
                except Exception:
                    pass
                    
        return {
            "inventory": file_counts,
            "findings": findings
        }
