"""Data models for parsed documents and analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Heading:
    level: int
    text: str
    style: str = ""


@dataclass
class DocumentMetrics:
    file_name: str
    file_path: str
    file_type: str
    size_bytes: int
    page_count: int | None
    word_count: int
    paragraph_count: int
    heading_count: int
    table_count: int
    image_count: int
    link_count: int
    bullet_count: int
    sentence_count: int
    avg_words_per_paragraph: float
    avg_sentence_length: float
    empty_paragraph_ratio: float | None
    metadata: dict[str, str] = field(default_factory=dict)
    headings: list[Heading] = field(default_factory=list)
    heading_hierarchy_issues: list[str] = field(default_factory=list)
    text_preview: str = ""


@dataclass
class MigrationInsights:
    readability: str
    clarity: str
    consistency: str
    structural_quality: str
    technical_complexity: str
    migration_readiness: str
    migration_score: int
    ready_for_migration: bool
    migration_verdict: str
    reasoning: dict[str, str]
    suggestions: list[str]
    issues_detected: list[str]


@dataclass
class AnalysisResult:
    metrics: DocumentMetrics
    insights: MigrationInsights
    pair_name: str | None = None


@dataclass
class CorpusReport:
    generated_at: str
    input_directory: str
    documents: list[AnalysisResult]
    pairs: list[dict[str, Any]]
    summary: dict[str, Any]
