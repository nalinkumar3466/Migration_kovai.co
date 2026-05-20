"""Unit tests for document analyzer."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from doc_analyzer.analysis.readiness import score_migration_readiness
from doc_analyzer.models import DocumentMetrics, Heading
from doc_analyzer.pipeline import discover_files, pair_name
from doc_analyzer.utils.text_utils import corruption_hits, word_count


class TestTextUtils(unittest.TestCase):
    def test_word_count(self):
        self.assertEqual(word_count("Hello world test"), 3)

    def test_corruption_detection(self):
        text = "Crgating an articlg with tgxt stylgs"
        self.assertGreaterEqual(corruption_hits(text), 3)


class TestReadiness(unittest.TestCase):
    def test_empty_document_low_score(self):
        metrics = DocumentMetrics(
            file_name="empty.docx",
            file_path="/tmp/empty.docx",
            file_type="DOCX",
            size_bytes=100,
            page_count=None,
            word_count=10,
            paragraph_count=1,
            heading_count=0,
            table_count=0,
            image_count=0,
            link_count=0,
            bullet_count=0,
            sentence_count=1,
            avg_words_per_paragraph=10.0,
            avg_sentence_length=10.0,
            empty_paragraph_ratio=0.0,
        )
        rating, score, issues = score_migration_readiness(metrics)
        self.assertIn(rating, ("Not Ready", "Requires Restructuring", "Partially Ready"))
        self.assertLess(score, 80)
        self.assertTrue(issues)

    def test_healthy_document_high_score(self):
        metrics = DocumentMetrics(
            file_name="good.docx",
            file_path="/tmp/good.docx",
            file_type="DOCX",
            size_bytes=5000,
            page_count=None,
            word_count=1500,
            paragraph_count=40,
            heading_count=10,
            table_count=2,
            image_count=0,
            link_count=5,
            bullet_count=10,
            sentence_count=80,
            avg_words_per_paragraph=37.5,
            avg_sentence_length=14.0,
            empty_paragraph_ratio=0.1,
            headings=[Heading(1, "Intro"), Heading(2, "Section A")],
            metadata={"title": "Guide"},
        )
        rating, score, _ = score_migration_readiness(metrics)
        self.assertGreaterEqual(score, 80)
        self.assertEqual(rating, "Ready")


class TestPipeline(unittest.TestCase):
    def test_pair_name(self):
        self.assertEqual(pair_name("Managing articles.docx"), "Managing articles")

    def test_discover_input_files(self):
        input_dir = ROOT / "input"
        if not input_dir.exists():
            self.skipTest("input/ folder not present")
        files = discover_files(input_dir)
        self.assertGreater(len(files), 0)
        extensions = {f.suffix.lower() for f in files}
        self.assertTrue(extensions <= {".docx", ".pdf"})


if __name__ == "__main__":
    unittest.main()
