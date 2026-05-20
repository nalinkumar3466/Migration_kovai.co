"""Rule-based migration readiness scoring."""

from __future__ import annotations

from doc_analyzer.models import DocumentMetrics
from doc_analyzer.utils.text_utils import corruption_hits


def score_migration_readiness(metrics: DocumentMetrics) -> tuple[str, int, list[str]]:
    """Return (rating, score 0-100, issues)."""
    score = 100
    issues: list[str] = []

    if metrics.word_count < 50:
        issues.append("Very low text content - may be image-only or empty")
        score -= 40

    if metrics.heading_count == 0:
        issues.append("No clear heading structure detected")
        score -= 25

    issues.extend(metrics.heading_hierarchy_issues)
    score -= min(15, len(metrics.heading_hierarchy_issues) * 3)

    h1_count = sum(1 for h in metrics.headings if h.level == 1)
    if h1_count > 15:
        issues.append(f"Over-flattened structure: {h1_count} top-level (H1) headings")
        score -= 15

    if metrics.empty_paragraph_ratio is not None and metrics.empty_paragraph_ratio > 0.4:
        issues.append(
            f"High empty-paragraph ratio ({metrics.empty_paragraph_ratio:.0%}) - export noise"
        )
        score -= 10

    hits = corruption_hits(metrics.text_preview)
    if hits >= 3:
        issues.append(f"Possible text corruption detected ({hits} pattern matches)")
        score -= 15

    if not metrics.metadata.get("title") and not metrics.metadata.get("author"):
        issues.append("Sparse document metadata (title/author missing)")
        score -= 5

    if metrics.file_type == "PDF" and metrics.image_count > 50 and metrics.word_count < 800:
        issues.append("Image-heavy PDF with limited extractable text")
        score -= 10

    score = max(0, min(100, score))

    if score >= 80:
        rating = "Ready"
    elif score >= 60:
        rating = "Partially Ready"
    elif score >= 40:
        rating = "Requires Restructuring"
    else:
        rating = "Not Ready"

    return rating, score, issues
