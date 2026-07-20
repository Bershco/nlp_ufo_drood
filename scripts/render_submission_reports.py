"""Render the concise Markdown submission reports as paginated PDFs."""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "outputs" / "reports"
REPORTS = ("ufo_submission_report", "drood_submission_report")


def inline_markup(value: str) -> str:
    value = html.escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\*(.+?)\*", r"<em>\1</em>", value)
    value = re.sub(r"`(.+?)`", r"<code>\1</code>", value)
    return value


def markdown_to_html(source: str, asset_dir: Path) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{inline_markup(' '.join(paragraph))}</p>")
            paragraph.clear()

    for raw_line in source.splitlines():
        line = raw_line.strip()
        image_match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line)
        list_match = re.match(r"^\d+\.\s+(.*)", line)
        if not line:
            flush_paragraph()
            if in_list:
                blocks.append("</ol>")
                in_list = False
        elif line.startswith("## "):
            flush_paragraph()
            blocks.append(f"<h2>{inline_markup(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_paragraph()
            blocks.append(f"<h1>{inline_markup(line[2:])}</h1>")
        elif image_match:
            flush_paragraph()
            source_image = (REPORT_DIR / image_match.group(2)).resolve()
            image_path = asset_dir / source_image.name
            with Image.open(source_image) as figure:
                figure.thumbnail((540, 270), Image.Resampling.LANCZOS)
                figure.save(image_path)
            blocks.append(
                f'<div class="chart"><img src="{image_path.as_uri()}" alt="{html.escape(image_match.group(1))}"><br>'
                f'<span class="caption">Figure: {html.escape(image_match.group(1))}</span></div>'
            )
        elif list_match:
            flush_paragraph()
            if not in_list:
                blocks.append("<ol>")
                in_list = True
            blocks.append(f"<li>{inline_markup(list_match.group(1))}</li>")
        else:
            paragraph.append(line)
    flush_paragraph()
    if in_list:
        blocks.append("</ol>")
    return "\n".join(blocks)


def render(name: str, soffice: str) -> None:
    markdown_path = REPORT_DIR / f"{name}.md"
    html_path = REPORT_DIR / f"{name}.html"
    with tempfile.TemporaryDirectory(prefix=f"{name}_") as temp_dir:
        body = markdown_to_html(markdown_path.read_text(encoding="utf-8"), Path(temp_dir))
        document = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 13mm 15mm; }}
body {{ font-family: Arial, sans-serif; font-size: 9.5pt; line-height: 1.15;
        color: #20242a; max-width: 180mm; margin: auto; }}
h1 {{ font-size: 18pt; color: #18354f; margin: 0 0 5mm; }}
h2 {{ font-size: 12.5pt; color: #245678; margin: 4mm 0 1.5mm;
      border-bottom: 0.4pt solid #9bb4c7; }}
p {{ margin: 0 0 2.2mm; text-align: justify; }}
ol {{ margin: 0 0 2mm 6mm; padding-left: 4mm; }}
li {{ margin-bottom: 1mm; }}
.chart {{ margin: 2.5mm auto 3mm; text-align: center; page-break-inside: avoid; }}
img {{ max-width: 165mm; max-height: 61mm; }}
.caption {{ font-size: 8pt; color: #52606b; }}
code {{ font-size: 8.5pt; }}
</style></head><body>{body}</body></html>"""
        html_path.write_text(document, encoding="utf-8")
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(REPORT_DIR), str(html_path)],
            check=True,
        )
    html_path.unlink()


def main() -> None:
    soffice = shutil.which("libreoffice") or shutil.which("soffice")
    if not soffice:
        raise RuntimeError("LibreOffice is required to render submission PDFs")
    for report in REPORTS:
        render(report, soffice)


if __name__ == "__main__":
    main()
