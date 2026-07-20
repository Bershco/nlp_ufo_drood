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
    value = value.replace(chr(8212), ", ")
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

    lines = source.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        image_match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line)
        list_match = re.match(r"^\d+\.\s+(.*)", line)
        if not line:
            flush_paragraph()
            if in_list:
                blocks.append("</ol>")
                in_list = False
        elif line.startswith("## "):
            flush_paragraph()
            blocks.append(
                '<div class="section-heading" style="width:100%; clear:both; display:block; text-align:left; '
                'margin:14px 0 6px -15px; padding:0 0 3px 0; border-bottom:1px solid #9bb4c7;">'
                f'<span style="font-size:16px; font-weight:bold; color:#245678;">{inline_markup(line[3:])}</span></div>'
            )
        elif line.startswith("# "):
            flush_paragraph()
            blocks.append(f"<h1>{inline_markup(line[2:])}</h1>")
        elif image_match:
            flush_paragraph()
            source_image = (REPORT_DIR / image_match.group(2)).resolve()
            with Image.open(source_image) as figure:
                pixel_width, pixel_height = figure.size
            display_width = 624
            display_height = round(display_width * pixel_height / pixel_width)
            if display_height > 260:
                display_height = 260
                display_width = round(display_height * pixel_width / pixel_height)
            blocks.append(
                f'<div class="chart"><img src="{source_image.as_uri()}" width="{display_width}" height="{display_height}" '
                f'alt="{html.escape(image_match.group(1))}"><br>'
                f'<span class="caption">Figure: {html.escape(image_match.group(1))}</span></div>'
            )
        elif (
            line.startswith("|")
            and index + 1 < len(lines)
            and re.fullmatch(r"\|?[\s:|-]+\|?", lines[index + 1].strip())
        ):
            flush_paragraph()
            headers = [cell.strip() for cell in line.strip("|").split("|")]
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
                index += 1
            head = "".join(f"<th>{inline_markup(cell)}</th>" for cell in headers)
            body = "".join(
                "<tr>" + "".join(f"<td>{inline_markup(cell)}</td>" for cell in row) + "</tr>"
                for row in rows
            )
            blocks.append(f'<table class="score-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')
            continue
        elif list_match:
            flush_paragraph()
            if not in_list:
                blocks.append("<ol>")
                in_list = True
            blocks.append(f"<li>{inline_markup(list_match.group(1))}</li>")
        else:
            paragraph.append(line)
        index += 1
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
html, body {{ direction: ltr; }}
body {{ font-family: Arial, sans-serif; font-size: 9pt; line-height: 1.10;
        color: #20242a; max-width: 180mm; margin: auto; text-align: left; }}
h1 {{ font-size: 18pt; color: #18354f; margin: 0 0 5mm; clear: both; display: block; text-align: left; }}
h2 {{ font-size: 12.5pt; color: #245678; margin: 4mm 0 1.5mm;
      border-bottom: 0.4pt solid #9bb4c7; clear: both; display: block; text-align: left; }}
.section-heading {{ width: 100%; margin: 4mm 0 1.5mm; padding: 0 0 1mm; border-bottom: 0.4pt solid #9bb4c7; clear: both; display: block; text-align: left; }}
.section-heading span {{ font-family: Arial, sans-serif; font-size: 12.5pt; font-weight: bold; color: #245678; }}
p {{ margin: 0 0 2.2mm; text-align: left; clear: both; }}
ol {{ margin: 0 0 2mm 6mm; padding-left: 4mm; }}
li {{ margin-bottom: 1mm; }}
.chart {{ margin: 2.5mm auto 3mm; text-align: center; page-break-inside: avoid; clear: both; display: block; }}
img {{ max-width: 165mm; max-height: 61mm; }}
.caption {{ font-size: 8pt; color: #52606b; }}
.score-table {{ width: 100%; border-collapse: collapse; margin: 2mm 0 3mm; font-size: 6.6pt; page-break-inside: avoid; clear: both; }}
.score-table th {{ color: #18354f; background: #eaf1f6; font-weight: bold; }}
.score-table th, .score-table td {{ border: 0.4pt solid #9bb4c7; padding: 1.1mm 0.7mm; text-align: center; }}
.score-table th:first-child, .score-table td:first-child {{ text-align: left; white-space: nowrap; }}
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
