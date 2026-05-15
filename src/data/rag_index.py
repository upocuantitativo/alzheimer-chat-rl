"""RAG index over public guides (CEAFA, Alzheimer's Association, papers).

Build:
    python scripts/build_rag_index.py

Query:
    from src.data.rag_index import RAGIndex
    idx = RAGIndex.load("data/rag_index")
    for chunk in idx.query("cómo gestionar la ansiedad", k=3):
        print(chunk.source, chunk.page, chunk.text[:120])
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_CHUNK_WORDS = 120
_OVERLAP_WORDS = 25
_MIN_WORDS = 30


@dataclass
class Chunk:
    text: str
    source: str
    page: int


class RAGIndex:
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._embeddings: np.ndarray | None = None
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError("pip install sentence-transformers") from exc
            self._model = SentenceTransformer(_MODEL_NAME)
        return self._model

    def build(self, pdf_dir: Path | str) -> None:
        pdf_dir = Path(pdf_dir)
        self._chunks = []
        for pdf_path in sorted(pdf_dir.glob("*.pdf")):
            chunks = _extract_chunks(pdf_path)
            self._chunks.extend(chunks)
            print(f"  {pdf_path.name}: {len(chunks)} chunks")

        print(f"Total: {len(self._chunks)} chunks. Generando embeddings…")
        texts = [c.text for c in self._chunks]
        self._embeddings = self._get_model().encode(
            texts, show_progress_bar=True, normalize_embeddings=True
        )

    def save(self, index_dir: Path | str) -> None:
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        with open(index_dir / "chunks.json", "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in self._chunks], f, ensure_ascii=False, indent=2)
        np.save(index_dir / "embeddings.npy", self._embeddings)
        print(f"Índice guardado en {index_dir}  ({len(self._chunks)} chunks)")

    @classmethod
    def load(cls, index_dir: Path | str) -> RAGIndex:
        index_dir = Path(index_dir)
        idx = cls()
        with open(index_dir / "chunks.json", encoding="utf-8") as f:
            idx._chunks = [Chunk(**d) for d in json.load(f)]
        idx._embeddings = np.load(index_dir / "embeddings.npy")
        return idx

    def query(self, text: str, k: int = 3) -> list[Chunk]:
        if not self._chunks or self._embeddings is None:
            return []
        q_emb = self._get_model().encode([text], normalize_embeddings=True)
        scores = (self._embeddings @ q_emb.T).squeeze()
        top_k = min(k, len(self._chunks))
        idxs = np.argsort(scores)[::-1][:top_k]
        return [self._chunks[i] for i in idxs]


# ---------------------------------------------------------------------------

def _extract_chunks(pdf_path: Path) -> list[Chunk]:
    pages = _read_pages(pdf_path)
    chunks: list[Chunk] = []
    step = _CHUNK_WORDS - _OVERLAP_WORDS
    for page_num, raw in pages:
        text = _clean(raw)
        if not _is_readable(text):
            continue
        words = text.split()
        for i in range(0, len(words), step):
            window = words[i: i + _CHUNK_WORDS]
            if len(window) < _MIN_WORDS:
                continue
            chunks.append(Chunk(
                text=" ".join(window),
                source=pdf_path.name,
                page=page_num,
            ))
    return chunks


def _read_pages(pdf_path: Path) -> list[tuple[int, str]]:
    try:
        import fitz  # pymupdf
        doc = fitz.open(str(pdf_path))
        pages = [(i + 1, doc[i].get_text()) for i in range(len(doc))]
        doc.close()
        return pages
    except ImportError:
        pass
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            return [
                (i + 1, page.extract_text() or "")
                for i, page in enumerate(pdf.pages)
            ]
    except ImportError:
        pass
    try:
        import pypdf
        with open(pdf_path, "rb") as fh:
            reader = pypdf.PdfReader(fh)
            return [
                (i + 1, page.extract_text() or "")
                for i, page in enumerate(reader.pages)
            ]
    except ImportError as exc:
        raise ImportError("pip install pymupdf") from exc


_MIN_AVG_WORD_LEN = 2.8


def _clean(text: str) -> str:
    try:
        import ftfy
        text = ftfy.fix_text(text)
    except ImportError:
        pass
    return re.sub(r"\s+", " ", text).strip()


def _is_readable(text: str) -> bool:
    words = text.split()
    if not words:
        return False
    avg_len = sum(len(w) for w in words) / len(words)
    return avg_len >= _MIN_AVG_WORD_LEN
