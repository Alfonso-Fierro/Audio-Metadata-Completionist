"""Integration tests for enrichment pipeline."""

import pytest

from src.pipeline.enrichment_pipeline import EnrichmentPipeline, ProcessingStats


class TestEnrichmentPipeline:
    """Tests for EnrichmentPipeline."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = EnrichmentPipeline(dry_run=True)
        assert pipeline.dry_run is True
        assert pipeline.identifier is not None
        assert pipeline.artwork_aggregator is not None

    def test_processing_stats(self):
        """Test processing statistics."""
        stats = ProcessingStats(
            total_files=10,
            successful=8,
            failed=2,
            identified=7,
            artwork_added=6,
        )

        assert stats.total_files == 10
        assert stats.successful == 8
        assert stats.failed == 2
        assert stats.success_rate() == 80.0

    def test_processing_stats_zero_division(self):
        """Test stats with zero files."""
        stats = ProcessingStats()
        assert stats.success_rate() == 0.0
