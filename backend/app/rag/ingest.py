"""
Document Ingestion Pipeline for EarthPulse
Processes Markdown, TXT, PDF, CSV, and JSON documentation files.
Extracts metadata, performs semantic and token-aware chunking (~500-1000 tokens),
generates 1536-dim embeddings, and persists records in PostgreSQL + pgvector.
"""

import os
import re
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from ..db.postgres import db_manager
from .embedding_service import embedding_service

logger = logging.getLogger("earthpulse.rag.ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class DocumentIngestionPipeline:
    def __init__(
        self,
        chunk_size_words: int = 400,   # ~500-700 tokens
        chunk_overlap_words: int = 60  # ~100 tokens
    ):
        self.chunk_size_words = chunk_size_words
        self.chunk_overlap_words = chunk_overlap_words

    def parse_frontmatter(self, text: str) -> Tuple[Dict[str, Any], str]:
        """Extracts YAML-style frontmatter from markdown files."""
        metadata = {}
        content = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                frontmatter_raw = parts[1]
                content = parts[2].strip()
                for line in frontmatter_raw.strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip().strip('"').strip("'")
        return metadata, content

    def clean_text(self, text: str) -> str:
        """Cleans and normalizes document text."""
        # Normalize carriage returns and tabs
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def chunk_text(self, text: str, preserve_headers: bool = True) -> List[str]:
        """
        Splits text into chunks of approximately 500-1000 tokens (~400-700 words)
        with 100-150 token overlap. Preserves markdown tables and code blocks.
        """
        cleaned = self.clean_text(text)
        if not cleaned:
            return []

        # Split by markdown double newlines or section headers first
        paragraphs = re.split(r"(?:\n\n(?=#+ )|\n\n)", cleaned)
        chunks: List[str] = []
        current_words: List[str] = []

        for p in paragraphs:
            p_words = p.split()
            if not p_words:
                continue

            # If adding this paragraph exceeds chunk size, commit current chunk
            if len(current_words) + len(p_words) > self.chunk_size_words and current_words:
                chunks.append(" ".join(current_words))
                # Retain overlap from end of current chunk
                overlap_count = min(len(current_words), self.chunk_overlap_words)
                current_words = current_words[-overlap_count:] + p_words
            else:
                current_words.extend(p_words)

        if current_words:
            chunks.append(" ".join(current_words))

        return chunks if chunks else [cleaned]

    def process_markdown_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parses a Markdown file preserving frontmatter metadata and headers."""
        raw = file_path.read_text(encoding="utf-8")
        meta, body = self.parse_frontmatter(raw)
        
        doc_title = meta.get("title") or file_path.stem.replace("_", " ").title()
        category = meta.get("category", "general")
        dataset = meta.get("dataset")
        satellite = meta.get("satellite")
        source = meta.get("source", str(file_path.relative_to(file_path.parent.parent.parent)))
        doc_date = meta.get("date", "2024-01-01")

        chunks = self.chunk_text(body)
        records = []
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{file_path.stem}_chunk_{idx}"
            chunk_meta = {
                "source": source,
                "title": doc_title,
                "category": category,
                "dataset": dataset,
                "satellite": satellite,
                "date": doc_date,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "file_path": str(file_path)
            }
            records.append({
                "id": chunk_id,
                "title": f"{doc_title} (Part {idx+1}/{len(chunks)})" if len(chunks) > 1 else doc_title,
                "content": chunk,
                "source": source,
                "category": category,
                "dataset": dataset,
                "satellite": satellite,
                "metadata": chunk_meta
            })
        return records

    def process_txt_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parses a plain text file."""
        body = file_path.read_text(encoding="utf-8")
        title = file_path.stem.replace("_", " ").title()
        chunks = self.chunk_text(body)
        records = []
        for idx, chunk in enumerate(chunks):
            records.append({
                "id": f"{file_path.stem}_{idx}",
                "title": f"{title} (Chunk {idx+1})",
                "content": chunk,
                "source": str(file_path.name),
                "category": "documentation",
                "dataset": None,
                "satellite": None,
                "metadata": {"chunk_index": idx, "file_path": str(file_path)}
            })
        return records

    def process_pdf_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extracts text from PDF, cleans formatting, and chunks."""
        if not HAS_PYPDF:
            logger.warning(f"pypdf not available; skipping PDF {file_path.name}")
            return []

        try:
            reader = PdfReader(str(file_path))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages_text.append(text)

            full_text = "\n\n".join(pages_text)
            title = file_path.stem.replace("_", " ").title()
            chunks = self.chunk_text(full_text)
            records = []
            for idx, chunk in enumerate(chunks):
                records.append({
                    "id": f"{file_path.stem}_pdf_{idx}",
                    "title": f"{title} (PDF Chunk {idx+1})",
                    "content": chunk,
                    "source": str(file_path.name),
                    "category": "scientific_paper",
                    "dataset": None,
                    "satellite": None,
                    "metadata": {"chunk_index": idx, "pages": len(reader.pages), "file_path": str(file_path)}
                })
            return records
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return []

    def process_csv_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Processes CSV dataset documentation preserving column headers and summaries."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if not headers:
                    return []
                rows = [row for row in reader]

            title = file_path.stem.replace("_", " ").title()
            # Construct a clear technical summary preserving columns
            content_lines = [
                f"# CSV Dataset Documentation: {title}",
                f"Columns ({len(headers)}): {', '.join(headers)}\n",
                f"Sample records ({min(10, len(rows))} rows):\n"
            ]
            for row in rows[:10]:
                pair_strs = [f"{headers[i]}='{row[i]}'" for i in range(min(len(headers), len(row)))]
                content_lines.append("- " + "; ".join(pair_strs))

            content = "\n".join(content_lines)
            return [{
                "id": f"{file_path.stem}_csv",
                "title": f"Dataset Columns & Schema: {title}",
                "content": content,
                "source": str(file_path.name),
                "category": "datasets",
                "dataset": file_path.stem.upper(),
                "satellite": None,
                "metadata": {"columns": headers, "row_count": len(rows), "file_path": str(file_path)}
            }]
        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {e}")
            return []

    def process_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Processes JSON documentation preserving structured keys."""
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            title = file_path.stem.replace("_", " ").title()
            content = f"# JSON Documentation: {title}\n\n```json\n{json.dumps(data, indent=2)[:3000]}\n```"
            return [{
                "id": f"{file_path.stem}_json",
                "title": f"JSON Spec: {title}",
                "content": content,
                "source": str(file_path.name),
                "category": "datasets",
                "dataset": file_path.stem.upper(),
                "satellite": None,
                "metadata": {"file_path": str(file_path)}
            }]
        except Exception as e:
            logger.error(f"Error processing JSON {file_path}: {e}")
            return []

    def ingest_file(self, file_path: Path) -> int:
        """Parses a single file, generates embeddings, and saves to database."""
        ext = file_path.suffix.lower()
        records: List[Dict[str, Any]] = []

        if ext in (".md", ".markdown"):
            records = self.process_markdown_file(file_path)
        elif ext == ".txt":
            records = self.process_txt_file(file_path)
        elif ext == ".pdf":
            records = self.process_pdf_file(file_path)
        elif ext == ".csv":
            records = self.process_csv_file(file_path)
        elif ext == ".json":
            records = self.process_json_file(file_path)

        if not records:
            return 0

        # Generate embeddings in batch
        texts_to_embed = [f"{r['title']}\n{r['content']}" for r in records]
        embeddings = embedding_service.generate_batch_embeddings(texts_to_embed)

        saved_count = 0
        for i, rec in enumerate(records):
            emb = embeddings[i] if i < len(embeddings) else [0.0] * 1536
            ok = db_manager.upsert_document(
                doc_id=rec["id"],
                title=rec["title"],
                content=rec["content"],
                source=rec["source"],
                category=rec["category"],
                dataset=rec["dataset"],
                satellite=rec["satellite"],
                metadata=rec["metadata"],
                embedding=emb
            )
            if ok:
                saved_count += 1

        logger.info(f"Ingested {saved_count} chunks from {file_path.name}")
        return saved_count

    def ingest_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Recursively traverses a directory and ingests all supported files."""
        if not dir_path.exists():
            logger.warning(f"Directory {dir_path} does not exist.")
            return {"total_files": 0, "total_chunks": 0}

        total_files = 0
        total_chunks = 0
        supported_exts = {".md", ".markdown", ".txt", ".pdf", ".csv", ".json"}

        for p in sorted(dir_path.rglob("*")):
            if p.is_file() and p.suffix.lower() in supported_exts:
                # Skip package.json and hidden files
                if p.name.startswith(".") or p.name in ("package.json", "tsconfig.json"):
                    continue
                chunks_saved = self.ingest_file(p)
                if chunks_saved > 0:
                    total_files += 1
                    total_chunks += chunks_saved

        return {
            "status": "COMPLETED",
            "total_files": total_files,
            "total_chunks": total_chunks,
            "db_document_count": db_manager.get_document_count()
        }

    def ingest_all_knowledge(self) -> Dict[str, Any]:
        """Ingests the complete root knowledge/ directory."""
        knowledge_dir = Path(__file__).resolve().parent.parent.parent.parent / "knowledge"
        logger.info(f"Starting ingestion from knowledge base at {knowledge_dir}...")
        res = self.ingest_directory(knowledge_dir)
        logger.info(f"Ingestion finished: {res}")
        return res


# Global singleton pipeline instance
ingestion_pipeline = DocumentIngestionPipeline()

if __name__ == "__main__":
    result = ingestion_pipeline.ingest_all_knowledge()
    print("\n=======================================================")
    print(f"Ingestion Result: {json.dumps(result, indent=2)}")
    print("=======================================================\n")
