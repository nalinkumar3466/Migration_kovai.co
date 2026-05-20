"""PDF document parser using PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz

from doc_analyzer.models import DocumentMetrics, Heading
from doc_analyzer.utils.text_utils import sentence_stats, word_count


def parse_pdf(path: Path) -> DocumentMetrics:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Empty file: {path}")

    doc = fitz.open(str(path))
    pages_text: list[str] = []
    headings_guess: list[Heading] = []
    image_count = 0
    links: list[str] = []

    try:
        for page_index, page in enumerate(doc):
            text = page.get_text("text") or ""
            pages_text.append(text)
            image_count += len(page.get_images())
            for link in page.get_links():
                uri = link.get("uri")
                if uri:
                    links.append(uri)

            blocks = page.get_text("dict").get("blocks", [])
            for block in blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = (span.get("text") or "").strip()
                        size = span.get("size", 0)
                        if (
                            span_text
                            and size >= 14
                            and len(span_text) < 120
                            and len(span_text.split()) < 15
                        ):
                            headings_guess.append(
                                Heading(
                                    level=_size_to_level(size),
                                    text=span_text,
                                    style=f"font-size-{round(size)}",
                                )
                            )

        full_text = "\n".join(pages_text)
        wc = word_count(full_text)
        sc, avg_sent = sentence_stats(full_text)
        paragraphs = [p for p in full_text.split("\n\n") if p.strip()]
        para_count = len(paragraphs) if paragraphs else len([p for p in full_text.split("\n") if p.strip()])
        avg_wpp = round(wc / para_count, 2) if para_count else 0.0

        unique_headings = _dedupe_headings(headings_guess)
        meta = doc.metadata or {}

        return DocumentMetrics(
            file_name=path.name,
            file_path=str(path.resolve()),
            file_type="PDF",
            size_bytes=path.stat().st_size,
            page_count=len(doc),
            word_count=wc,
            paragraph_count=para_count,
            heading_count=len(unique_headings),
            table_count=0,
            image_count=image_count,
            link_count=len(set(links)),
            bullet_count=0,
            sentence_count=sc,
            avg_words_per_paragraph=avg_wpp,
            avg_sentence_length=round(avg_sent, 2),
            empty_paragraph_ratio=None,
            metadata={
                k: str(meta.get(k, ""))
                for k in ("title", "author", "subject", "creator", "producer", "format")
                if meta.get(k)
            },
            headings=unique_headings[:60],
            heading_hierarchy_issues=[],
            text_preview=full_text[:6000],
        )
    finally:
        doc.close()


def _size_to_level(size: float) -> int:
    if size >= 22:
        return 1
    if size >= 18:
        return 2
    if size >= 16:
        return 3
    return 4


def _dedupe_headings(headings: list[Heading]) -> list[Heading]:
    seen: set[str] = set()
    unique: list[Heading] = []
    for heading in headings:
        key = heading.text.lower()
        if key not in seen:
            seen.add(key)
            unique.append(heading)
    return unique
