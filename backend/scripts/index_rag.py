from __future__ import annotations

import argparse
import json

from app.rag.dependencies import get_rag_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the CausalCast project-document FAISS index")
    parser.add_argument("--force", action="store_true", help="Re-embed every chunk instead of using the verified cache")
    args = parser.parse_args()
    result = get_rag_service().reindex(force=args.force)
    print(
        json.dumps(
            {
                "document_count": result.document_count,
                "chunk_count": result.chunk_count,
                "embedding_dimension": result.embedding_dimension,
                "embedded_chunks": result.embedded_chunks,
                "reused_chunks": result.reused_chunks,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
