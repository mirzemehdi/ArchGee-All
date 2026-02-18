"""Pre-filter jobs by architecture keywords before sending to Laravel.

This reduces API calls and AI processing costs by removing
obviously irrelevant jobs before they reach the server.
"""

from __future__ import annotations

import re
from typing import List

from models.job import ScrapedJob
from utils.logger import get_logger

logger = get_logger(__name__)

# Keywords indicating architecture/built-environment jobs
ARCHITECTURE_KEYWORDS = [
    "architect",
    "architecture",
    "architectural",
    "interior design",
    "interior designer",
    "landscape architect",
    "landscape design",
    "urban design",
    "urban planner",
    "urban planning",
    "bim",
    "revit",
    "autocad",
    "archicad",
    "building design",
    "sustainable design",
    "heritage",
    "conservation architect",
    "masterplan",
    "town planner",
    "town planning",
    "sustainability consultant",
    "planning consultant",
    "building surveyor",
    "quantity surveyor",
    "construction manager",
    "project architect",
    "design architect",
    "residential architect",
    "commercial architect",
    "3d visualiser",
    "3d visualizer",
    "architectural technologist",
    "architectural technician",
    "riba",
    "arb",
    "aia",
]

# Keywords indicating tech/software jobs (false positives)
EXCLUDE_KEYWORDS = [
    "software architect",
    "cloud architect",
    "data architect",
    "solutions architect",
    "enterprise architect",
    "network architect",
    "security architect",
    "system architect",
    "systems architect",
    "it architect",
    "information architect",
    "web architect",
    "platform architect",
    "infrastructure architect",
    "technical architect",
    "application architect",
    "devops",
    "kubernetes",
    "terraform",
    "machine learning",
    "deep learning",
    "fullstack",
    "full-stack",
    "frontend developer",
    "backend developer",
]


class KeywordFilter:
    """Filters scraped jobs by architecture-related keywords.

    A job passes if:
    1. Title OR description contains at least one ARCHITECTURE_KEYWORDS match
    2. Title does NOT contain any EXCLUDE_KEYWORDS match
    """

    def __init__(
        self,
        include_keywords: List[str] | None = None,
        exclude_keywords: List[str] | None = None,
    ):
        self.include_keywords = include_keywords or ARCHITECTURE_KEYWORDS
        self.exclude_keywords = exclude_keywords or EXCLUDE_KEYWORDS

        # Compile patterns for efficient matching
        self._include_pattern = self._compile_pattern(self.include_keywords)
        self._exclude_pattern = self._compile_pattern(self.exclude_keywords)

    @staticmethod
    def _compile_pattern(keywords: List[str]) -> re.Pattern:
        """Compile a list of keywords into a single regex pattern."""
        escaped = [re.escape(kw) for kw in keywords]
        pattern = "|".join(escaped)
        return re.compile(pattern, re.IGNORECASE)

    def is_relevant(self, job: ScrapedJob) -> bool:
        """Check if a job passes the keyword filter."""
        title_lower = job.title.lower()
        desc_lower = job.description.lower() if job.description else ""

        # Check exclude list (title only)
        if self._exclude_pattern.search(title_lower):
            return False

        # Check include list (title + description)
        if self._include_pattern.search(title_lower):
            return True

        if self._include_pattern.search(desc_lower):
            return True

        return False

    def filter_jobs(self, jobs: List[ScrapedJob]) -> List[ScrapedJob]:
        """Filter a list of jobs, keeping only relevant ones.

        Args:
            jobs: List of scraped jobs.

        Returns:
            Filtered list of relevant jobs.
        """
        original_count = len(jobs)
        filtered = [job for job in jobs if self.is_relevant(job)]
        removed_count = original_count - len(filtered)

        logger.info(
            f"Keyword filter: {original_count} → {len(filtered)} "
            f"({removed_count} removed)"
        )

        return filtered
