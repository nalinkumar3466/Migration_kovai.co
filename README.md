# Document Analysis & Migration Readiness Tool

Automation tool that analyzes **Microsoft Word (`.docx`)** and **PDF (`.pdf`)** files and produces **structured JSON** plus a **migration readiness summary report**. Built for content auditing and documentation migration scenarios (e.g. into Document360).

**No API key required** - uses an automated rule-based analysis engine.

---

## Features

| Capability | Description |
|------------|-------------|
| Document parsing | Text, headings, tables, links, images, metadata |
| Metrics extraction | Pages, words, paragraphs, headings, averages, hierarchy issues |
| Migration insights | Readability, clarity, consistency, structural quality, readiness score |
| JSON output | Master report + executive summary + one JSON per document |
| Summary report | Markdown with quick-answers table and per-file detail |
| HTML dashboard | Interactive UI with search, filters, and expandable cards |

---

## Project Structure

```
.
??? input/                          # Company sample documents (DOCX + PDF)
??? output/
?   ??? analysis_report.json        # Full structured output (all documents)
?   ??? analysis_report.md          # Human-readable summary
?   ??? documents/                  # One JSON per input file
??? output/samples/                 # Pre-generated outputs for submission
??? src/doc_analyzer/
?   ??? cli.py
?   ??? pipeline.py
?   ??? parsers/                    # DOCX & PDF
?   ??? analysis/                   # Readiness scoring + insights
?   ??? output/                     # JSON & Markdown writers
??? tests/
??? run.py
??? requirements.txt
??? README.md
```

---

## Setup

**Prerequisites:** Python 3.10+, pip

```bash
git clone <your-repo-url>
cd Kovai

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

## How to Run

```bash
python run.py

# Open interactive dashboard in browser when done
python run.py --open-dashboard
```

Custom paths:

```bash
python run.py --input input --output output
```

| Option | Description |
|--------|-------------|
| `-i, --input` | Input folder (default: `input`) |
| `-o, --output` | Output folder (default: `output`) |
| `--no-recursive` | Scan only top-level of input folder |
| `--json-only` | JSON only, no Markdown |
| `--md-only` | Markdown only, no JSON |
| `--open-dashboard` | Open `dashboard.html` in browser after run |

---

## Output Format

### 1. JSON (`output/analysis_report.json`)

Structured report including:

- `report_meta` - timestamp, document count
- `executive_summary` - readiness counts and overview table
- `pairs` - DOCX/PDF topic comparisons
- `documents[]` - per-file analysis with schema:

```json
{
  "file_info": {},
  "metrics": {},
  "content_analysis": {},
  "quality_scores": {},
  "migration_readiness": {},
  "migration_question": {
    "question": "Is this document ready for migration? If not, what needs improvement?",
    "answer": "...",
    "improvements_needed": []
  },
  "issues_detected": [],
  "recommendations": []
}
```

### 2. Per-document JSON (`output/documents/*.json`)

Same structure as each entry in `documents[]` - one file per input document.

### 3. Executive summary JSON (`output/executive_summary.json`)

Compact JSON with stats, quick answers, and pairs only.

### 4. Summary report (`output/analysis_report.md`)

Answers for each file:

- **Is this document ready for migration?**
- **What needs improvement?**

### 5. Interactive dashboard (`output/dashboard.html`)

Open in any web browser. Features:

- Executive stats (Ready / Partial / Restructuring / Not Ready)
- Search and filter documents
- Expandable cards with verdict, metrics, issues, and improvements
- DOCX vs PDF pair comparison table

---

## Tools & Libraries

| Library | Purpose |
|---------|---------|
| [python-docx](https://python-docx.readthedocs.io/) | Parse `.docx` |
| [PyMuPDF](https://pymupdf.readthedocs.io/) | Parse `.pdf` |
| [Click](https://click.palletsprojects.com/) | CLI |
| [Rich](https://rich.readthedocs.io/) | Terminal output |

---

## Sample Input & Output

**Input:** 5 Document360 articles in `input/` (DOCX + PDF pairs)

**Output:** See `output/samples/` for pre-generated:

- `analysis_report.json`
- `analysis_report.md`
- `executive_summary.json`
- `dashboard.html`
- `documents/*.json`

---

## Tests

```bash
python -m unittest discover -s tests -v
```

---

## Migration Readiness Ratings

| Rating | Meaning |
|--------|---------|
| Ready | Migrate with standard preprocessing |
| Partially Ready | Fix listed issues first |
| Requires Restructuring | Heading/metadata cleanup needed |
| Not Ready | Major rework required |

---

## License

MIT
