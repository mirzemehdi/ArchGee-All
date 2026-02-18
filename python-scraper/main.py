#!/usr/bin/env python3
"""ArchGee Job Scraper - CLI entry point.

Fetches architecture jobs from external sources worldwide
and sends them to the Laravel ingest API.

Usage:
    python main.py --all                                   # All sources, all countries
    python main.py --source adzuna                         # Adzuna, all countries
    python main.py --source adzuna --country gb,us,de      # Adzuna, specific countries
    python main.py --source adzuna --country all           # Adzuna, all countries (explicit)
    python main.py --schedule                              # Run on schedule (worldwide)
"""

import sys
from typing import List, Optional

import click

from adapters.adzuna import AdzunaAdapter
from adapters.careerjet import CareerJetAdapter
from adapters.jooble import JoobleAdapter
from adapters.base import BaseAdapter
from client.ingest_client import IngestClient
from config import config
from filters.keyword_filter import KeywordFilter
from utils.dedup import DedupCache
from utils.logger import get_logger

logger = get_logger("main")

# Default search keywords for architecture jobs
DEFAULT_KEYWORDS = [
    "architect",
    "interior designer",
    "landscape architect",
    "urban designer",
    "BIM",
]

# Available adapters
ADAPTERS = {
    "adzuna": AdzunaAdapter,
    "careerjet": CareerJetAdapter,
    "jooble": JoobleAdapter,
}


def run_adapter(
    adapter: BaseAdapter,
    keywords: List[str],
    location: str,
    country: str,
    max_results: int,
    ingest_client: IngestClient,
    keyword_filter: KeywordFilter,
    dedup_cache: DedupCache,
) -> dict:
    """Run a single adapter: fetch, filter, deduplicate, and ingest.

    For adapters that support multi-country (like Adzuna), the `country`
    param can be "all" or comma-separated codes — the adapter handles
    iterating countries internally.

    Returns:
        dict with accepted, duplicates, errors, filtered, fetched counts.
    """
    source = adapter.source_name

    logger.info(f"Starting {source} fetch (country={country})...")

    # Fetch jobs from source
    try:
        # Pass country to adapters that support it (Adzuna)
        fetch_kwargs = {
            "keywords": keywords,
            "location": location,
            "max_results": max_results,
        }
        # Check if the adapter's fetch_jobs accepts a country parameter
        import inspect
        sig = inspect.signature(adapter.fetch_jobs)
        if "country" in sig.parameters:
            fetch_kwargs["country"] = country

        jobs = adapter.fetch_jobs(**fetch_kwargs)

    except Exception as e:
        logger.error(f"Failed to fetch from {source}: {e}")
        return {"accepted": 0, "duplicates": 0, "errors": 1, "filtered": 0, "fetched": 0}

    fetched_count = len(jobs)
    logger.info(f"Fetched {fetched_count} jobs from {source}")

    if not jobs:
        return {"accepted": 0, "duplicates": 0, "errors": 0, "filtered": 0, "fetched": 0}

    # Pre-filter by architecture keywords
    filtered_jobs = keyword_filter.filter_jobs(jobs)
    filtered_count = fetched_count - len(filtered_jobs)

    # Local deduplication
    new_jobs = dedup_cache.filter_new(filtered_jobs)

    if not new_jobs:
        logger.info(f"No new jobs to ingest from {source}")
        return {
            "accepted": 0,
            "duplicates": len(filtered_jobs),
            "errors": 0,
            "filtered": filtered_count,
            "fetched": fetched_count,
        }

    # Send to Laravel API
    result = ingest_client.ingest_in_batches(source, new_jobs, batch_size=50)

    # Mark successfully sent jobs as seen
    dedup_cache.mark_batch_seen(new_jobs, source)

    result["filtered"] = filtered_count
    result["fetched"] = fetched_count

    logger.info(
        f"{source} complete: "
        f"fetched={fetched_count}, "
        f"filtered={filtered_count}, "
        f"accepted={result['accepted']}, "
        f"duplicates={result['duplicates']}, "
        f"errors={result['errors']}"
    )

    return result


@click.command()
@click.option("--all", "fetch_all", is_flag=True, help="Fetch from all sources, all countries")
@click.option("--source", type=click.Choice(list(ADAPTERS.keys())), help="Specific source adapter")
@click.option("--keywords", default=None, help="Comma-separated keywords")
@click.option("--location", default="", help="Location filter (single-country mode only)")
@click.option(
    "--country", default="all",
    help="Country codes: 'all' (default), or comma-separated (gb,us,de,fr,au,ca,...)"
)
@click.option("--max-results", default=None, type=int, help="Max results per country per source")
@click.option("--schedule", is_flag=True, help="Run worldwide on a recurring schedule")
@click.option("--cleanup", is_flag=True, help="Cleanup expired dedup cache entries")
def main(
    fetch_all: bool,
    source: Optional[str],
    keywords: Optional[str],
    location: str,
    country: str,
    max_results: Optional[int],
    schedule: bool,
    cleanup: bool,
):
    """ArchGee Job Scraper - Fetch architecture jobs worldwide."""
    # Validate configuration
    if not config.API_URL or not config.API_TOKEN:
        logger.error("ARCHGEE_API_URL and ARCHGEE_API_TOKEN must be configured.")
        sys.exit(1)

    # Parse keywords
    search_keywords = keywords.split(",") if keywords else DEFAULT_KEYWORDS
    fetch_max = max_results or config.MAX_JOBS_PER_FETCH

    # Initialize shared components
    ingest_client = IngestClient()
    keyword_filter = KeywordFilter()
    dedup_cache = DedupCache()

    # Cleanup expired cache entries
    if cleanup:
        removed = dedup_cache.cleanup_expired()
        logger.info(f"Cleaned up {removed} expired cache entries")
        return

    # Run on schedule (worldwide by default)
    if schedule:
        import schedule as sched
        import time

        logger.info(
            f"Starting worldwide scheduler (every {config.FETCH_INTERVAL_HOURS} hours, "
            f"country={country})"
        )

        def scheduled_run():
            _run_all_sources(
                search_keywords, location, country, fetch_max,
                ingest_client, keyword_filter, dedup_cache,
            )

        sched.every(config.FETCH_INTERVAL_HOURS).hours.do(scheduled_run)
        scheduled_run()  # Run immediately on start

        while True:
            sched.run_pending()
            time.sleep(60)

    # Determine which sources to fetch
    if fetch_all:
        _run_all_sources(
            search_keywords, location, country, fetch_max,
            ingest_client, keyword_filter, dedup_cache,
        )
    elif source:
        adapter_class = ADAPTERS[source]
        adapter = adapter_class()
        run_adapter(
            adapter, search_keywords, location, country, fetch_max,
            ingest_client, keyword_filter, dedup_cache,
        )
    else:
        click.echo("Please specify --all or --source. Use --help for options.")
        sys.exit(1)


def _run_all_sources(
    keywords: List[str],
    location: str,
    country: str,
    max_results: int,
    ingest_client: IngestClient,
    keyword_filter: KeywordFilter,
    dedup_cache: DedupCache,
) -> None:
    """Run all available adapters worldwide."""
    logger.info(f"Running all source adapters worldwide (country={country})...")

    total = {"accepted": 0, "duplicates": 0, "errors": 0, "filtered": 0, "fetched": 0}

    for name, adapter_class in ADAPTERS.items():
        try:
            adapter = adapter_class()
            result = run_adapter(
                adapter, keywords, location, country, max_results,
                ingest_client, keyword_filter, dedup_cache,
            )
            for key in total:
                total[key] += result.get(key, 0)
        except Exception as e:
            logger.error(f"Adapter {name} failed: {e}")
            total["errors"] += 1

    logger.info(
        f"All sources complete (worldwide): "
        f"fetched={total['fetched']}, "
        f"filtered={total['filtered']}, "
        f"accepted={total['accepted']}, "
        f"duplicates={total['duplicates']}, "
        f"errors={total['errors']}"
    )


if __name__ == "__main__":
    main()
