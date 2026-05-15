"""Build and save the RAG index from PDF guides in data/public/.

Usage:
    python scripts/build_rag_index.py
    python scripts/build_rag_index.py --pdf-dir data/public --out data/rag_index
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.rag_index import RAGIndex


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", default=str(ROOT / "data" / "public"))
    ap.add_argument("--out", default=str(ROOT / "data" / "rag_index"))
    args = ap.parse_args()

    pdf_dir = Path(args.pdf_dir)
    pdfs = list(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No se encontraron PDFs en {pdf_dir}")
        print("Ejecuta primero: python scripts/download_public_data.py")
        return 1

    print(f"PDFs encontrados en {pdf_dir}:")
    for p in sorted(pdfs):
        print(f"  {p.name}")
    print()

    idx = RAGIndex()
    idx.build(pdf_dir)
    idx.save(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
