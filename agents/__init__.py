"""FiberPulse ingestion agents for data fetching, normalization, and health tracking."""

from agents.base_scraper import BaseScraper, ScraperResult, SourceCategory
from agents.cai_spot_scraper import CAISpotScraper, create_cai_spot_scraper
from agents.ccfgroup_scraper import CCFGroupScraper, create_ccfgroup_scraper
from agents.ccfi_mediterranean_scraper import CCFIMediterraneanScraper
from agents.data_fetcher import DataFetcher, IngestionResult, run_ingestion
from agents.drewry_wci_scraper import DrewryWCIScraper
from agents.fibre2fashion_scraper import Fibre2FashionScraper, create_fibre2fashion_scraper
from agents.iea_scraper import IEAScraper, create_iea_scraper
from agents.macro_feed_scraper import MacroFeedScraper
from agents.mcx_futures_scraper import MCXFuturesScraper, create_mcx_futures_scraper
from agents.normalizer import Normalizer, NormalizerError, normalize_payload
from agents.source_health import SourceHealthEvaluator, get_evaluator

__all__ = [
    # Base classes
    "BaseScraper",
    "ScraperResult",
    "SourceCategory",
    # Scrapers
    "CAISpotScraper",
    "create_cai_spot_scraper",
    "MCXFuturesScraper",
    "create_mcx_futures_scraper",
    "CCFGroupScraper",
    "create_ccfgroup_scraper",
    "Fibre2FashionScraper",
    "create_fibre2fashion_scraper",
    "IEAScraper",
    "create_iea_scraper",
    "CCFIMediterraneanScraper",
    "DrewryWCIScraper",
    "MacroFeedScraper",
    # Orchestrator
    "DataFetcher",
    "IngestionResult",
    "run_ingestion",
    # Normalizer
    "Normalizer",
    "NormalizerError",
    "normalize_payload",
    # Health evaluator
    "SourceHealthEvaluator",
    "get_evaluator",
]