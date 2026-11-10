import os
import json
import argparse
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings

class ChunkInspector:
    """
    Inspection utility to analyze token distributions, headings, and metadata of processed agricultural chunks.
    """

    @classmethod
    def load_processed_document(cls, document_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(settings.PROCESSED_DATA_PATH, f"{document_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def list_processed_documents(cls) -> List[str]:
        if not os.path.exists(settings.PROCESSED_DATA_PATH):
            return []
        files = [f.replace(".json", "") for f in os.listdir(settings.PROCESSED_DATA_PATH) if f.endswith(".json")]
        return files

    @classmethod
    def inspect(cls, document_id: str, page_filter: Optional[int] = None, tag_filter: Optional[str] = None) -> Dict[str, Any]:
        data = cls.load_processed_document(document_id)
        if not data:
            return {"error": f"Processed document '{document_id}' not found."}

        chunks = data.get("chunks", [])
        if page_filter is not None:
            chunks = [c for c in chunks if c.get("page_number") == page_filter]

        if tag_filter:
            tag_filter_lower = tag_filter.lower()
            chunks = [
                c for c in chunks
                if any(tag_filter_lower in t.lower() for t in c.get("crop_tags", [])) or
                   any(tag_filter_lower in t.lower() for t in c.get("topic_tags", []))
            ]

        token_counts = [c.get("token_count", 0) for c in chunks]
        stats = {
            "document_id": data.get("document_id"),
            "document_title": data.get("title"),
            "total_pages": data.get("page_count"),
            "total_chunks_in_file": data.get("chunk_count"),
            "filtered_chunks_count": len(chunks),
            "token_stats": {
                "min_tokens": min(token_counts) if token_counts else 0,
                "max_tokens": max(token_counts) if token_counts else 0,
                "avg_tokens": round(sum(token_counts) / len(token_counts), 1) if token_counts else 0
            },
            "sample_chunks": chunks[:3]  # Preview first 3
        }
        return stats

def main():
    parser = argparse.ArgumentParser(description="KrishiRAG Chunk Inspector Utility")
    parser.add_argument("--doc-id", type=str, help="Document ID to inspect")
    parser.add_argument("--latest", action="store_true", help="Inspect latest ingested document")
    parser.add_argument("--page", type=int, help="Filter by specific page number")
    parser.add_argument("--tag", type=str, help="Filter by crop or topic tag")

    args = parser.parse_args()

    doc_ids = ChunkInspector.list_processed_documents()
    if not doc_ids:
        print("No processed documents found in ./data/processed/")
        return

    target_id = args.doc_id
    if args.latest or not target_id:
        target_id = doc_ids[-1]

    print(f"\n=======================================================")
    print(f"  KRISHIRAG CHUNK INSPECTOR: {target_id}")
    print(f"=======================================================\n")

    res = ChunkInspector.inspect(target_id, page_filter=args.page, tag_filter=args.tag)
    if "error" in res:
        print(f"Error: {res['error']}")
        return

    print(f"Title:         {res['document_title']}")
    print(f"Total Pages:   {res['total_pages']}")
    print(f"Total Chunks:  {res['total_chunks_in_file']}")
    print(f"Filtered:      {res['filtered_chunks_count']}")
    print(f"Token Stats:   Min={res['token_stats']['min_tokens']}, Max={res['token_stats']['max_tokens']}, Avg={res['token_stats']['avg_tokens']}")

    print(f"\n--- Preview of First Chunks ---")
    for idx, c in enumerate(res["sample_chunks"], 1):
        print(f"\n[Chunk {idx}] ID: {c['chunk_id']} | Page: {c['page_number']} | Tokens: {c['token_count']}")
        print(f"Heading:  {c.get('section_heading') or 'None'}")
        print(f"Crops:    {', '.join(c.get('crop_tags', [])) or 'None'}")
        print(f"Topics:   {', '.join(c.get('topic_tags', [])) or 'None'}")
        print(f"Text Preview:\n{c['text'][:250]}...")
        print("-" * 50)

if __name__ == "__main__":
    main()
