"""JSON report export - combined report and per-document files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from doc_analyzer.models import AnalysisResult, CorpusReport

MIGRATION_QUESTION = "Is this document ready for migration? If not, what needs improvement?"


def _readiness_status(ins) -> dict[str, Any]:
    return {
        "rating": ins.migration_readiness,
        "score": ins.migration_score,
        "ready_for_migration": ins.ready_for_migration,
        "verdict": ins.migration_verdict,
        "reasoning": ins.reasoning,
    }


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
        "migration_readiness": _readiness_status(ins),
        "migration_question": {
            "question": MIGRATION_QUESTION,
            "ready": ins.ready_for_migration,
            "answer": ins.migration_verdict,
            "improvements_needed": ins.suggestions if not ins.ready_for_migration else [],
        },
        "issues_detected": ins.issues_detected,
        "recommendations": ins.suggestions,
    }


def _quick_answers(documents: list[dict]) -> list[dict]:
    return [
        {
            "file_name": d["file_info"]["file_name"],
            "file_type": d["file_info"]["file_type"],
            "ready_for_migration": d["migration_readiness"]["ready_for_migration"],
            "readiness": d["migration_readiness"]["rating"],
            "score": d["migration_readiness"]["score"],
            "answer": d["migration_question"]["answer"],
        }
        for d in documents
    ]


def write_json_report(report: CorpusReport, output_dir: Path) -> dict[str, Path]:
    """Write master JSON, executive summary, and per-document JSON files."""
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
            "outputs": {
                "full_report": "analysis_report.json",
                "executive_summary": "executive_summary.json",
                "per_document": "documents/<filename>.json",
                "summary_report": "analysis_report.md",
                "dashboard": "dashboard.html",
            },
        },
        "migration_question": {
            "question": MIGRATION_QUESTION,
            "quick_answers": _quick_answers(documents),
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

    executive = {
        "generated_at": report.generated_at,
        "migration_question": MIGRATION_QUESTION,
        "stats": payload["executive_summary"],
        "quick_answers": payload["migration_question"]["quick_answers"],
        "pairs": report.pairs,
    }

    master_path = output_dir / "analysis_report.json"
    exec_path = output_dir / "executive_summary.json"
    master_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    exec_path.write_text(json.dumps(executive, indent=2, ensure_ascii=False), encoding="utf-8")

    written: dict[str, Path] = {"master": master_path, "executive": exec_path}
    for doc in documents:
        safe = re.sub(r"[^\w\-.]+", "_", doc["file_info"]["file_name"])
        path = per_doc_dir / f"{safe}.json"
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        written[doc["file_info"]["file_name"]] = path

    return written
