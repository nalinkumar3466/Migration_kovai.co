"""JSON report export - combined report and per-document files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from doc_analyzer.models import AnalysisResult, CorpusReport


def _serialize_result(result: AnalysisResult) -> dict[str, Any]:
    metrics = result.metrics
    ins = result.insights
    return {
        "file_info": {
            "file_name": metrics.file_name,
            "file_path": metrics.file_path,
            "file_type": metrics.file_type,
            "size_bytes": metrics.size_bytes,
            "size_kb": round(metrics.size_bytes / 1024, 1),
            "pair_name": result.pair_name,
        },
        "metrics": {
            "page_count": metrics.page_count,
            "word_count": metrics.word_count,
            "paragraph_count": metrics.paragraph_count,
            "heading_count": metrics.heading_count,
            "table_count": metrics.table_count,
            "image_count": metrics.image_count,
            "link_count": metrics.link_count,
            "bullet_count": metrics.bullet_count,
            "sentence_count": metrics.sentence_count,
            "avg_words_per_paragraph": metrics.avg_words_per_paragraph,
            "avg_sentence_length": metrics.avg_sentence_length,
            "empty_paragraph_ratio": metrics.empty_paragraph_ratio,
            "metadata": metrics.metadata,
            "heading_hierarchy_issues": metrics.heading_hierarchy_issues,
            "headings": [
                {"level": h.level, "text": h.text, "style": h.style}
                for h in metrics.headings
            ],
        },
        "content_analysis": {
            "text_preview": metrics.text_preview[:2000],
        },
        "quality_scores": {
            "readability": ins.readability,
            "clarity": ins.clarity,
            "consistency": ins.consistency,
            "structural_quality": ins.structural_quality,
            "technical_complexity": ins.technical_complexity,
        },
        "migration_readiness": {
            "rating": ins.migration_readiness,
            "score": ins.migration_score,
            "ready_for_migration": ins.ready_for_migration,
            "verdict": ins.migration_verdict,
            "reasoning": ins.reasoning,
        },
        "migration_question": {
            "question": "Is this document ready for migration? If not, what needs improvement?",
            "answer": ins.migration_verdict,
            "improvements_needed": ins.suggestions if not ins.ready_for_migration else [],
        },
        "issues_detected": ins.issues_detected,
        "recommendations": ins.suggestions,
    }


def write_json_report(report: CorpusReport, output_dir: Path) -> dict[str, Path]:
    """Write master JSON and one JSON file per document. Returns paths written."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    per_doc_dir = output_dir / "documents"
    per_doc_dir.mkdir(parents=True, exist_ok=True)

    documents = [_serialize_result(r) for r in report.documents]

    payload = {
        "report_meta": {
            "generated_at": report.generated_at,
            "input_directory": report.input_directory,
            "document_count": len(report.documents),
            "analysis_engine": "automated-rule-based",
        },
        "executive_summary": {
            "ready_count": report.summary.get("ready_count", 0),
            "partially_ready_count": report.summary.get("partial_count", 0),
            "requires_restructuring_count": report.summary.get("restructure_count", 0),
            "not_ready_count": report.summary.get("not_ready_count", 0),
            "overview": report.summary.get("rows", []),
        },
        "pairs": report.pairs,
        "documents": documents,
    }

    master_path = output_dir / "analysis_report.json"
    master_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    written: dict[str, Path] = {"master": master_path}
    for doc in documents:
        safe = re.sub(r"[^\w\-.]+", "_", doc["file_info"]["file_name"])
        path = per_doc_dir / f"{safe}.json"
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        written[doc["file_info"]["file_name"]] = path

    return written
