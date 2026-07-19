import os

def analyze_rag_copilot(repo_path):
    findings = []
    rag_keywords = ['llm', 'embedding', 'vector', 'rag', 'pinecone', 'chroma', 'faiss', 'openai']
    
    has_rag = False
    for root, _, files in os.walk(repo_path):
        if '.git' in root or 'node_modules' in root or 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for kw in rag_keywords:
                            if kw in content.lower():
                                has_rag = True
                                findings.append(f"Found RAG/LLM keyword '{kw}' in {os.path.relpath(path, repo_path)}")
                except Exception:
                    pass
    
    if not has_rag:
        findings.append("STATUS: PLANNED (No LLM/RAG integration found in codebase).")
    
    return {"status": "completed", "findings": findings}
