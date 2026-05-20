"""Shared text analysis utilities."""

from __future__ import annotations

import re


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def sentence_stats(text: str) -> tuple[int, float]:
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return 0, 0.0
    lengths = [len(re.findall(r"\b\w+\b", s)) for s in sentences]
    return len(sentences), sum(lengths) / len(lengths)


def heading_level_from_style(style_name: str | None) -> int | None:
    if not style_name:
        return None
    match = re.match(r"Heading\s*(\d+)", style_name, re.I)
    if match:
        return int(match.group(1))
    lower = style_name.lower()
    if lower == "title":
        return 1
    if lower == "subtitle":
        return 2
    return None


def detect_hierarchy_issues(levels: list[int]) -> list[str]:
    issues: list[str] = []
    if not levels:
        issues.append("No styled headings detected")
        return issues
    if levels[0] != 1:
        issues.append(f"Document starts at heading level {levels[0]}, not H1")
    prev = 0
    for level in levels:
        if prev and level > prev + 1:
            issues.append(f"Skipped heading level: H{prev} -> H{level}")
        prev = level
    return issues[:15]


# Common corruption patterns from Document360 Word exports
CORRUPTION_PATTERNS = re.compile(
    r"\b(articlg|tgxt|Crgating|Mgthod|Palgttg|tgmplatg|numbgrgd|unsupportgd|"
    r"insgrt|mgnu|namg|stylgs|Hgadings|Dglgting|Rgnaming)\b",
    re.I,
)


def corruption_hits(text: str) -> int:
    return len(CORRUPTION_PATTERNS.findall(text))
