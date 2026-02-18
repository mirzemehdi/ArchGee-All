"""Abstract base class for all job source adapters."""

from abc import ABC, abstractmethod
from typing import List

from models.job import ScrapedJob
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAdapter(ABC):
    """Base class for all job source adapters.

    Each adapter is responsible for fetching jobs from a single
    external source and converting them to ScrapedJob instances.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique source identifier (e.g., 'adzuna')."""
        pass

    @abstractmethod
    def fetch_jobs(
        self, keywords: List[str], location: str = "", max_results: int = 100
    ) -> List[ScrapedJob]:
        """Fetch jobs from the source.

        Args:
            keywords: Search keywords (e.g., ["architect", "interior designer"]).
            location: Location filter (e.g., "London", "UK").
            max_results: Maximum number of results to return.

        Returns:
            List of ScrapedJob instances.
        """
        pass

    def _log_fetch_start(self, keywords: List[str], location: str) -> None:
        logger.info(
            f"[{self.source_name}] Fetching jobs",
            extra={"keywords": keywords, "location": location},
        )

    def _log_fetch_complete(self, count: int) -> None:
        logger.info(
            f"[{self.source_name}] Fetched {count} jobs",
            extra={"count": count},
        )

    def _log_fetch_error(self, error: Exception) -> None:
        logger.error(
            f"[{self.source_name}] Fetch error: {error}",
            extra={"error": str(error)},
        )
