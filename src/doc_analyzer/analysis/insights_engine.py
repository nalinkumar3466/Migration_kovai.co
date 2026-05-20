"""Automated migration readiness and content quality analysis (no external API)."""

from __future__ import annotations

from doc_analyzer.analysis.readiness import score_migration_readiness
from doc_analyzer.models import DocumentMetrics, MigrationInsights
from doc_analyzer.utils.text_utils import corruption_hits


def analyze_document(metrics: DocumentMetrics) -> MigrationInsights:
    """Produce migration readiness and quality insights from extracted metrics."""
    rating, score, issues = score_migration_readiness(metrics)
    wc = metrics.word_count
    avg_sent = metrics.avg_sentence_length

    if wc < 600:
        readability = "Easy"
    elif wc < 2500:
        readability = "Medium"
    else:
        readability = "Complex"
    if avg_sent > 22:
        readability = "Complex"

    corruption = corruption_hits(metrics.text_preview)
    if corruption >= 5:
        clarity = "Confusing"
    elif corruption >= 2 or len(issues) > 4:
        clarity = "Moderate"
    else:
        clarity = "Clear"

    if len(metrics.heading_hierarchy_issues) > 3 or (
        sum(1 for h in metrics.headings if h.level == 1) > 15
    ):
        consistency = "Poor"
    elif issues:
        consistency = "Medium"
    else:
        consistency = "High"

    if metrics.heading_count >= 5 and not metrics.heading_hierarchy_issues:
        structural = "Well-organized"
    elif metrics.heading_count >= 2:
        structural = "Moderately organized"
    else:
        structural = "Fragmented"

    if wc > 3000 or "API" in metrics.text_preview[:500]:
        tech = "Advanced"
    elif wc > 1000:
        tech = "Intermediate"
    else:
        tech = "Beginner"

    suggestions = _build_suggestions(metrics, issues)

    return MigrationInsights(
        readability=readability,
        clarity=clarity,
        consistency=consistency,
        structural_quality=structural,
        technical_complexity=tech,
        migration_readiness=rating,
        migration_score=score,
        ready_for_migration=rating in ("Ready", "Partially Ready"),
        migration_verdict=_migration_verdict(rating),
        reasoning={
            "readability": f"Based on {wc} words and average sentence length {avg_sent}.",
            "clarity": f"Corruption pattern hits: {corruption}; issues found: {len(issues)}.",
            "structural_quality": (
                f"{metrics.heading_count} headings; "
                f"{len(metrics.heading_hierarchy_issues)} hierarchy issues."
            ),
            "migration_readiness": f"Automated score {score}/100 maps to '{rating}'.",
        },
        suggestions=suggestions,
        issues_detected=issues,
    )


def _migration_verdict(rating: str) -> str:
    if rating == "Ready":
        return "Yes - suitable for migration with standard preprocessing."
    if rating == "Partially Ready":
        return "Partially - address listed improvements before migration."
    if rating == "Requires Restructuring":
        return "Not yet - heading structure and content cleanup required."
    return "No - significant restructuring needed before migration."


def _build_suggestions(metrics: DocumentMetrics, issues: list[str]) -> list[str]:
    suggestions: list[str] = []
    if any("corruption" in i.lower() for i in issues):
        suggestions.append(
            "Fix character substitution in source DOCX (e.g. articlg -> article) before migration."
        )
    if metrics.empty_paragraph_ratio and metrics.empty_paragraph_ratio > 0.4:
        suggestions.append("Remove empty paragraphs from DOCX exports to reduce CMS noise.")
    if metrics.heading_hierarchy_issues:
        suggestions.append("Normalize heading hierarchy - avoid skipping levels (e.g. H2 to H4).")
    if sum(1 for h in metrics.headings if h.level == 1) > 15:
        suggestions.append("Demote procedural step headings (Method 1, 2...) from H1 to H3/H4.")
    if not metrics.metadata:
        suggestions.append("Add metadata: title, author, product area, plan tier, last-reviewed date.")
    if metrics.table_count > 0 and metrics.file_type == "PDF":
        suggestions.append("Use DOCX source for tables - PDF text layer may not preserve them.")
    if metrics.image_count > 20:
        suggestions.append("Add alt text to screenshots and map images to procedural steps.")
    if not suggestions:
        suggestions.append("Proceed with staged migration; spot-check formatting after import.")
    return suggestions
