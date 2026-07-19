import os

def analyze_documentation(repo_path):
    findings = []
    expected_docs = ['README.md', 'SETUP.md', 'CONTRIBUTING.md', 'API.md']
    
    for doc in expected_docs:
        doc_path = os.path.join(repo_path, doc)
        if os.path.exists(doc_path):
            findings.append(f"Found {doc}")
            size = os.path.getsize(doc_path)
            if size < 100:
                findings.append(f"Warning: {doc} is very short ({size} bytes).")
        else:
            findings.append(f"Missing {doc}")
    
    return {"status": "completed", "findings": findings}
