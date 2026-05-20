"""End-to-end analysis pipeline."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from doc_analyzer.analysis.insights_engine import analyze_document
from doc_analyzer.models import AnalysisResult, CorpusReport, DocumentMetrics
from doc_analyzer.parsers.docx_parser import parse_docx
from doc_analyzer.parsers.pdf_parser import parse_pdf

SUPPORTED_EXTENSIONS = {".docx", ".pdf"}


def discover_files(input_dir: Path, recursive: bool = True) -> list[Path]:
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    pattern = "**/*" if recursive else "*"
    files = [
        p
        for p in input_dir.glob(pattern)
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files, key=lambda p: p.name.lower())


def parse_file(path: Path) -> DocumentMetrics:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return parse_docx(path)
    if suffix == ".pdf":
        return parse_pdf(path)
    raise ValueError(f"Unsupported file type: {path}")


def pair_name(file_name: str) -> str:
    return re.sub(r"\.(docx|pdf)$", "", file_name, flags=re.I)


def build_pairs(results: list[AnalysisResult]) -> list[dict]:
    by_pair: dict[str, dict] = {}
    for result in results:
        name = result.pair_name or pair_name(result.metrics.file_name)
        key = name.lower()
        entry = by_pair.setdefault(key, {"name": name})
        fmt = result.metrics.file_type.lower()
        entry[f"{fmt}_words"] = result.metrics.word_count
        entry[f"{fmt}_readiness"] = result.insights.migration_readiness
        entry[f"{fmt}_score"] = result.insights.migration_score

    pairs = []
    for entry in by_pair.values():
        docx_w = entry.get("docx_words")
        pdf_w = entry.get("pdf_words")
        if docx_w and pdf_w:
            entry["parity_ratio"] = round(min(docx_w, pdf_w) / max(docx_w, pdf_w), 3)
        pairs.append(entry)
    return sorted(pairs, key=lambda p: p["name"].lower())


def run_pipeline(input_dir: Path, *, recursive: bool = True) -> CorpusReport:
    files = discover_files(input_dir, recursive=recursive)
    if not files:
        raise FileNotFoundError(
            f"No .docx or .pdf files found in {input_dir}. "
            "Place company documents in the input/ folder."
        )

    results: list[AnalysisResult] = []
    errors: list[str] = []

    for path in files:
        try:
            metrics = parse_file(path)
            insights = analyze_document(metrics)
            results.append(
                AnalysisResult(
                    metrics=metrics,
                    insights=insights,
                    pair_name=pair_name(path.name),
                )
            )
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")

    if not results and errors:
        raise RuntimeError("All files failed to parse:\n" + "\n".join(errors))

    pairs = build_pairs(results)
    summary = _build_summary(results, errors)

    return CorpusReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        input_directory=str(Path(input_dir).resolve()),
        documents=results,
        pairs=pairs,
        summary=summary,
    )


def _build_summary(results: list[AnalysisResult], errors: list[str]) -> dict:
    ratings = [r.insights.migration_readiness for r in results]

    return {
        "ready_count": ratings.count("Ready"),
        "partial_count": ratings.count("Partially Ready"),
        "restructure_count": ratings.count("Requires Restructuring"),
        "not_ready_count": ratings.count("Not Ready"),
        "analysis_engine": "automated-rule-based",
        "parse_errors": errors,
        "rows": [
            {
                "file_name": r.metrics.file_name,
                "file_type": r.metrics.file_type,
                "page_count": r.metrics.page_count,
                "word_count": r.metrics.word_count,
                "heading_count": r.metrics.heading_count,
                "readiness": r.insights.migration_readiness,
                "score": r.insights.migration_score,
                "ready_for_migration": r.insights.ready_for_migration,
            }
            for r in results
        ],
    }
