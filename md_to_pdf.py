"""
Convert Markdown files to PDF using fpdf2.

Handles emojis, tables, code blocks, headers, and lists.

Usage:
    python md_to_pdf.py file1.md file2.md ...
    python md_to_pdf.py --all    # Convert all *_readme.md files
"""

import sys
import glob
import re
from pathlib import Path


EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f900-\U0001f9FF"
    "\U0001fa00-\U0001fa6F"
    "\U0001fa70-\U0001faFF"
    "\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)


def clean(text: str) -> str:
    """Remove emojis and force latin-1 safe output."""
    text = EMOJI_RE.sub("", text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    return text.encode("latin-1", "replace").decode("latin-1").strip()


def convert(md_path: str) -> str:
    """Convert a single markdown file to PDF. Returns PDF path or empty string."""
    from fpdf import FPDF

    md_file = Path(md_path)
    if not md_file.exists():
        print(f"  Error: {md_path} not found")
        return ""

    lines = md_file.read_text(encoding="utf-8").split("\n")
    pdf_path = str(md_file.with_suffix(".pdf"))

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    in_code_block = False

    for raw_line in lines:
        s = raw_line.rstrip()

        try:
            # Code block toggle
            if s.strip().startswith("```"):
                in_code_block = not in_code_block
                if in_code_block:
                    pdf.ln(2)
                else:
                    pdf.ln(2)
                continue

            # Inside code block
            if in_code_block:
                pdf.set_font("Courier", "", 7)
                pdf.set_text_color(88, 96, 105)
                code_line = s.encode("latin-1", "replace").decode("latin-1")
                pdf.cell(0, 4, code_line[:120], new_x="LMARGIN", new_y="NEXT")
                continue

            # Table separator row
            if s.startswith("|") and set(s.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
                continue

            # Table row
            if s.startswith("|"):
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(36, 41, 46)
                cells = [c.strip() for c in s.split("|")]
                cells = [c for c in cells if c]
                row_text = " | ".join(clean(c)[:50] for c in cells)
                pdf.cell(0, 4, row_text[:140], new_x="LMARGIN", new_y="NEXT")
                continue

            # H1
            if s.startswith("# ") and not s.startswith("## "):
                pdf.ln(4)
                pdf.set_font("Helvetica", "B", 18)
                pdf.set_text_color(3, 102, 214)
                pdf.cell(0, 10, clean(s.lstrip("# "))[:100], new_x="LMARGIN", new_y="NEXT")
                pdf.set_draw_color(3, 102, 214)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(3)
                continue

            # H2
            if s.startswith("## "):
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(36, 41, 46)
                pdf.cell(0, 8, clean(s.lstrip("# "))[:100], new_x="LMARGIN", new_y="NEXT")
                pdf.set_draw_color(225, 228, 232)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(2)
                continue

            # H3
            if s.startswith("### "):
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(36, 41, 46)
                pdf.cell(0, 7, clean(s.lstrip("# "))[:100], new_x="LMARGIN", new_y="NEXT")
                pdf.ln(1)
                continue

            # Empty line
            if s.strip() == "":
                pdf.ln(2)
                continue

            # List item
            if s.strip().startswith("- ") or s.strip().startswith("* ") or re.match(r'\d+\.\s', s.strip()):
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(36, 41, 46)
                text = clean(s)
                if not text.startswith(("- ", "* ")) and not re.match(r'\d+\.', text):
                    text = "  " + text
                pdf.cell(0, 5, text[:140], new_x="LMARGIN", new_y="NEXT")
                continue

            # Regular text
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(36, 41, 46)
            text = clean(s)
            if text:
                pdf.cell(0, 5, text[:140], new_x="LMARGIN", new_y="NEXT")

        except Exception:
            # Skip lines that cause rendering issues
            continue

    pdf.output(pdf_path)
    size_kb = Path(pdf_path).stat().st_size / 1024
    print(f"  Created: {Path(pdf_path).name} ({size_kb:.0f} KB)")
    return pdf_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python md_to_pdf.py file1.md file2.md ...")
        print("       python md_to_pdf.py --all")
        return 1

    if sys.argv[1] == "--all":
        files = sorted(glob.glob("*_readme.md")) + sorted(glob.glob("*readme*.md"))
        files = list(dict.fromkeys(files))
    else:
        files = sys.argv[1:]

    if not files:
        print("No markdown files found.")
        return 1

    print(f"\nConverting {len(files)} file(s) to PDF:\n")
    created = []
    for f in files:
        result = convert(f)
        if result:
            created.append(result)

    print(f"\nDone! Created {len(created)} PDF(s).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
