"""Unified ingestion orchestrator for FiberPulse Phase 2.

Manages the ingestion process for multiple data sources (freight, macro, cotton)
and provide aggregated reporting.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agents.data_fetcher import DataFetcher, IngestionResult

if TYPE_CHECKING:
    from agents.normalizer import Normalizer
    from db.repository import Repository

logger = logging.getLogger(__name__)


class UnifiedIngestionOrchestrator:
    """Orchestrates ingestion across all Phase 2 source types (freight, macro, cotton).

    Provides a high-level interface to execute the full Phase 2 ingestion pipeline
    sequentially for multiple sources, collecting results and calculating aggregated
    quality metrics.

    Attributes:
        fetcher (DataFetcher): The underlying orchestrator for individual source ingestion.
    """

    def __init__(
        self,
        repository: Repository,
        normalizer: Normalizer | None = None,
    ) -> None:
        """Initialize the unified orchestrator.

        Args:
            repository: Database repository for persistence.
            normalizer: Optional normalizer instance (uses global if omitted).
        """
        self.fetcher = DataFetcher(repository=repository, normalizer=normalizer)

    async def run_ingestion(self, sources: list[str]) -> dict[str, Any]:
        """Run ingestion for a specified list of sources and return aggregated results.

        Iterates through the provided source names, executes ingestion for each,
        and compiles a summary including success/failure counts and total records.

        Args:
            sources: List of canonical source names to ingest (e.g. ['ccfi_med', 'oil_spot']).

        Returns:
            A dictionary with two keys:
                - 'results': Per-source ingestion details (to_dict representation).
                - 'summary': Aggregated metrics (total_sources, successful_sources, etc.).
        """
        results: dict[str, Any] = {}
        successful = 0
        failed = 0
        total_records = 0

        for source_name in sources:
            try:
                result = await self.fetcher.ingest_source(source_name)
                results[source_name] = result.to_dict()
                if result.success:
                    successful += 1
                    total_records += result.records_ingested
                else:
                    failed += 1
            except Exception as e:
                logger.exception(f"Unexpected error ingesting {source_name}")
                failed += 1
                results[source_name] = {
                    "success": False,
                    "error": str(e)
                }

        summary = {
            "total_sources": len(sources),
            "successful_sources": successful,
            "failed_sources": failed,
            "total_records_ingested": total_records,
        }
        
        return {
            "results": results,
            "summary": summary
        }
