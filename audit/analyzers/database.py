import os
import ast

class DatabaseAnalyzer:
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
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            
                            if "sqlalchemy" in content:
                                findings.append(f"Found SQLAlchemy usage in {file}")
                                evidence.append(filepath)
                                if "Column(" in content or "Mapped[" in content:
                                    findings.append(f"Found SQLAlchemy models in {file}")
                                    
                            if "alembic" in content or "op.create_table" in content:
                                findings.append(f"Found Alembic migration patterns in {file}")
                                evidence.append(filepath)
                    except Exception as e:
                        pass

        return {
            "findings": list(set(findings)),
            "evidence": list(set(evidence))
        }
