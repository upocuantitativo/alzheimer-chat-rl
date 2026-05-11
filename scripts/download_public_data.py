"""Download public guides and freely available research papers.

Clinical speech corpora (DementiaBank, ADReSS, TAUKADIAL, SpeechDx) are NOT
downloaded here because they require signed agreements — see
docs/DATA_ACCESS.md.

Usage:
    python scripts/download_public_data.py [--out data/public]
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

import requests
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.public_resources import PUBLIC_RESOURCES   # noqa: E402


def download(url: str, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size > 1024:
        print(f"  ✓ existe ya: {dst.name}")
        return True
    try:
        with requests.get(url, stream=True, timeout=60, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0 (research)"}) as r:
            if r.status_code != 200:
                print(f"  ✗ HTTP {r.status_code} — saltando")
                return False
            total = int(r.headers.get("Content-Length", 0))
            with open(dst, "wb") as f, tqdm(
                total=total, unit="B", unit_scale=True, desc=dst.name, leave=False
            ) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        return True
    except Exception as e:
        print(f"  ✗ error: {e}")
        if dst.exists() and dst.stat().st_size == 0:
            dst.unlink()
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "public"))
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Descargando recursos públicos a: {out_dir}\n")
    n_ok = 0
    for res in PUBLIC_RESOURCES:
        print(f"→ {res.name}")
        print(f"    {res.url}")
        dst = out_dir / res.filename
        if download(res.url, dst):
            n_ok += 1
        print()

    print(f"Listo: {n_ok}/{len(PUBLIC_RESOURCES)} descargados.")
    print("Para datasets clínicos (DementiaBank, ADReSS, TAUKADIAL): "
          "ver docs/DATA_ACCESS.md")
    return 0 if n_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
