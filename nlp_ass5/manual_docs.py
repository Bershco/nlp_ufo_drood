from __future__ import annotations

import csv
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import pandas as pd

from .common import DATA_PROCESSED, REPORTS, ROOT, clean_text, ensure_dirs


MANUAL_RAW = ROOT / "data" / "manual_raw"
MANUAL_EXTRACTED = ROOT / "data" / "manual_extracted"
MANUAL_TEXT = ROOT / "data" / "manual_text"


def normalize_name(value: object) -> str:
    text = str(value).lower()
    text = re.sub(r"https?://[^/]+/", "", text)
    text = re.sub(r"\.[a-z0-9]{2,5}$", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_name(value))


def safe_extract_zip(zip_path: Path, target_root: Path) -> list[Path]:
    extracted: list[Path] = []
    target_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                continue
            target = target_root / member_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.stat().st_size != member.file_size:
                with archive.open(member) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
            extracted.append(target)
    return extracted


def inventory_manual_raw() -> pd.DataFrame:
    rows = []
    for path in sorted(MANUAL_RAW.rglob("*")) if MANUAL_RAW.exists() else []:
        if path.is_file():
            rows.append({
                "path": str(path.relative_to(ROOT)),
                "size_bytes": path.stat().st_size,
                "suffix": "".join(path.suffixes),
                "is_partial": path.name.endswith(".partial") or ".partial" in path.name,
            })
    out = pd.DataFrame(rows)
    REPORTS.mkdir(parents=True, exist_ok=True)
    out.to_csv(REPORTS / "manual_raw_inventory.csv", index=False)
    return out


def extract_archives() -> pd.DataFrame:
    ensure_dirs()
    MANUAL_EXTRACTED.mkdir(parents=True, exist_ok=True)
    rows = []
    for zip_path in sorted(MANUAL_RAW.glob("*.zip")) if MANUAL_RAW.exists() else []:
        target_root = MANUAL_EXTRACTED / zip_path.stem
        try:
            files = safe_extract_zip(zip_path, target_root)
            status = "extracted"
            error = ""
        except zipfile.BadZipFile as exc:
            files = []
            status = "bad_zip"
            error = str(exc)
        rows.append({
            "archive": str(zip_path.relative_to(ROOT)),
            "target_dir": str(target_root.relative_to(ROOT)),
            "files_extracted": len(files),
            "status": status,
            "error": error,
        })
    out = pd.DataFrame(rows)
    out.to_csv(REPORTS / "manual_archive_extraction.csv", index=False)
    return out


def pdftotext_available() -> bool:
    return shutil.which("pdftotext") is not None


def text_output_path(source_path: Path) -> Path:
    rel = source_path.relative_to(MANUAL_EXTRACTED)
    return (MANUAL_TEXT / rel).with_suffix(rel.suffix + ".txt")


def extract_text_file(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        if not pdftotext_available():
            return ("", "pdftotext_missing")
        out_path = text_output_path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), str(out_path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            return ("", clean_text(result.stderr)[:500] or "pdftotext_failed")
        return (out_path.read_text(encoding="utf-8", errors="replace"), "pdf_text")
    if suffix in {".txt", ".csv", ".md", ".html", ".htm", ".json", ".xml"}:
        return (path.read_text(encoding="utf-8", errors="replace"), "plain_text")
    return ("", "unsupported")


def extract_document_texts() -> pd.DataFrame:
    MANUAL_TEXT.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(MANUAL_EXTRACTED.rglob("*")) if MANUAL_EXTRACTED.exists() else []:
        if not path.is_file():
            continue
        text, status = extract_text_file(path)
        rows.append({
            "document_path": str(path.relative_to(ROOT)),
            "text_path": str(text_output_path(path).relative_to(ROOT)) if text else "",
            "file_name": path.name,
            "normalized_name": normalize_name(path.name),
            "compact_name": compact_name(path.name),
            "suffix": path.suffix.lower(),
            "text_status": status,
            "text_length": len(text),
            "text_sample": clean_text(text)[:700],
        })
    out = pd.DataFrame(rows)
    out.to_csv(DATA_PROCESSED / "pursue_document_text_index.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    return out


def organize_manual_documents() -> dict[str, int]:
    inventory = inventory_manual_raw()
    archives = extract_archives()
    texts = extract_document_texts()
    return {
        "raw_files": len(inventory),
        "archives": len(archives),
        "document_files": len(texts),
        "text_extracted": int((texts["text_length"] > 0).sum()) if not texts.empty else 0,
    }


if __name__ == "__main__":
    print(organize_manual_documents())
