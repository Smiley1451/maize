from __future__ import annotations
from pathlib import Path
import json, csv
from typing import Iterable

TEXT_EXTS = {".txt", ".md", ".py", ".ps1", ".psm1", ".log", ".json", ".yaml", ".yml", ".ini", ".cfg", ".toml", ".sql", ".csv"}
BINARY_EXTS = {".joblib", ".zip", ".png", ".jpg", ".jpeg", ".webp", ".exe", ".dll", ".pyd", ".pyc", ".bin"}


def chunk_text(text: str, size: int = 1100, overlap: int = 150) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    if len(text) <= size:
        return [text]
    out=[]; start=0
    step=max(1, size-overlap)
    while start < len(text):
        part=text[start:start+size]
        out.append(part)
        start += step
    return out


def parse_text_file(path: Path, max_chars: int) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return raw[:max_chars]


def parse_csv_rows(path: Path, max_rows: int) -> Iterable[tuple[int, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i >= max_rows + 1:
                break
            if not row:
                continue
            if i == 0:
                header = row
                yield 1, "CSV HEADER: " + " | ".join(header)
                continue
            cells=[]
            for h,v in zip(header, row):
                if v not in (None, ""):
                    cells.append(f"{h}={v}")
            if cells:
                yield i+1, " | ".join(cells)


def parse_pdf(path: Path):
    from pypdf import PdfReader
    reader=PdfReader(str(path))
    for idx,page in enumerate(reader.pages, start=1):
        try:
            text=page.extract_text() or ""
        except Exception as exc:
            text=f"PDF page extraction error: {exc}"
        yield idx, text
