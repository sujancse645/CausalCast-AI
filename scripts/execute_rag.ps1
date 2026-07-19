Set-Location "C:\Casualcast AI\backend"

Write-Host "===================================================="
Write-Host "1. Syntax Checks"
Write-Host "===================================================="
python -m py_compile app/rag/loader.py app/rag/chunker.py app/rag/metadata.py app/rag/document_registry.py app/rag/embeddings.py app/rag/retriever.py app/rag/rag_service.py app/api/routes/rag.py app/main.py

Write-Host "`n===================================================="
Write-Host "4. Pytest"
Write-Host "===================================================="
python -m pytest tests/test_rag.py -v

Write-Host "`n===================================================="
Write-Host "5. Start FastAPI Server"
Write-Host "===================================================="
$proc = Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" -PassThru -NoNewWindow
Start-Sleep -Seconds 7

try {
    # Get auth token since endpoints are protected
    $tokenRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/login/developer" -Method Post
    $token = $tokenRes.access_token
    $headers = @{ "Authorization" = "Bearer $token"; "Content-Type" = "application/json" }

    Write-Host "`n===================================================="
    Write-Host "2 & 3. Index all documents & Build FAISS"
    Write-Host "===================================================="
    $reindexRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/reindex" -Method Post -Body '{"force": true}' -Headers $headers
    $reindexRes | ConvertTo-Json

    Write-Host "`n===================================================="
    Write-Host "6. Test /api/v1/chat"
    Write-Host "===================================================="
    $chatBody = @{ "question" = "Which model has the best RMSE for Tourism?"; "minimum_similarity" = 0.0 } | ConvertTo-Json
    $chatRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/chat" -Method Post -Body $chatBody -Headers $headers
    $chatRes | ConvertTo-Json

    Write-Host "`n===================================================="
    Write-Host "7. Test /api/v1/search"
    Write-Host "===================================================="
    $searchBody = @{ "query" = "tourism RMSE"; "dataset" = "tourism"; "minimum_similarity" = 0.0 } | ConvertTo-Json
    $searchRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/search" -Method Post -Body $searchBody -Headers $headers
    $searchRes.results | Select-Object -First 1 | ConvertTo-Json -Depth 3
    
    Write-Host "`n===================================================="
    Write-Host "8. Display Stats"
    Write-Host "===================================================="
    $docsRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/documents" -Method Get -Headers $headers
    Write-Host "`n[9] Indexed Documents Count: $($docsRes.document_count)"
    Write-Host "[10] Chunk Count: $($reindexRes.chunk_count)"
    Write-Host "[11] Embedding Dimension: $($reindexRes.embedding_dimension) (all-MiniLM-L6-v2)"
    
    Write-Host "`n[12] Generated Files:"
    Get-ChildItem -Path app\rag -Filter *.py | ForEach-Object { Write-Host "- backend/app/rag/$($_.Name)" }
    Write-Host "- backend/app/main.py"
    Write-Host "- backend/app/api/routes/rag.py"
    Write-Host "- backend/tests/test_rag.py"
    Write-Host "- frontend/index.html"
    Write-Host "- docs/RAG.md"
} finally {
    Write-Host "`nShutting down server..."
    Stop-Process -Id $proc.Id -Force
}
