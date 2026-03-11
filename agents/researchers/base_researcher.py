"""Base class for all research agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Callable

from config.prompts import RESEARCH_EXTRACTION_SYSTEM, RESEARCH_EXTRACTION_USER
from config.settings import MAX_PAGES_TO_PARSE_PER_QUERY, MODEL_FAST
from models.data_models import BusinessProfile, ResearchFinding
from services.dataforseo_client import DataForSEOClient
from services.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)


class BaseResearcher(ABC):
    """Abstract base for all research dimension agents."""

    dimension: str = ""

    def __init__(
        self,
        llm: OpenRouterClient,
        dfs: DataForSEOClient,
        profile: BusinessProfile,
        status_callback: Callable[[str], None] | None = None,
    ) -> None:
        self.llm = llm
        self.dfs = dfs
        self.profile = profile
        self._status = status_callback or (lambda _: None)

    @abstractmethod
    def get_queries(self, query_list: list[str]) -> list[str]:
        """Return the list of search queries for this dimension."""
        ...

    def _score_url(self, result: dict) -> float:
        """Score a SERP result URL by likely relevance for psychographic research."""
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        desc = result.get("description", "").lower()

        score = 0.5  # base

        # High-value domains for consumer psychology
        high_value = [
            "reddit.com", "quora.com", "trustpilot.com", "bbb.org",
            "yelp.com", "g2.com", "capterra.com", "glassdoor.com",
            "consumeraffairs.com", "sitejabber.com",
        ]
        for domain in high_value:
            if domain in url:
                score += 0.3
                break

        # Content signals
        psych_signals = [
            "complaint", "frustrat", "problem", "hate", "love",
            "worst", "best", "review", "experience", "regret",
            "recommend", "avoid", "scam", "worth", "mistake",
            "honest", "opinion", "testimonial", "story",
        ]
        text = f"{title} {desc}"
        for signal in psych_signals:
            if signal in text:
                score += 0.05

        return min(score, 1.0)

    def research(self, queries: list[str]) -> list[ResearchFinding]:
        """Run the full research pipeline for this dimension."""
        findings: list[ResearchFinding] = []

        for i, query in enumerate(queries):
            self._status(f"[{self.dimension}] Searching ({i+1}/{len(queries)}): {query[:60]}...")

            try:
                serp_results = self.dfs.serp_search(query)
            except Exception as e:
                logger.warning("SERP search failed for '%s': %s", query, e)
                continue

            if not serp_results:
                continue

            # Score and pick top URLs
            scored = [(r, self._score_url(r)) for r in serp_results]
            scored.sort(key=lambda x: x[1], reverse=True)
            top_results = scored[:MAX_PAGES_TO_PARSE_PER_QUERY]

            for result, url_score in top_results:
                url = result["url"]
                try:
                    content = self.dfs.parse_content(url)
                except Exception as e:
                    logger.warning("Content parse failed for '%s': %s", url, e)
                    continue

                if not content or len(content.strip()) < 100:
                    continue

                # Extract insights via LLM
                try:
                    extraction = self.llm.analyze_json(
                        system_prompt=RESEARCH_EXTRACTION_SYSTEM,
                        user_prompt=RESEARCH_EXTRACTION_USER.format(
                            dimension=self.dimension,
                            industry=self.profile.industry,
                            vertical=self.profile.vertical,
                            business_model=self.profile.business_model,
                            source_url=url,
                            content=content,
                        ),
                        model=MODEL_FAST,
                        max_tokens=2048,
                    )
                except Exception as e:
                    logger.warning("LLM extraction failed for '%s': %s", url, e)
                    continue

                insights = extraction.get("insights", [])
                if not insights:
                    continue

                finding = ResearchFinding(
                    dimension=self.dimension,
                    source_url=url,
                    source_type=extraction.get("source_type", "other"),
                    content_snippet=content[:500],
                    extracted_insights=[
                        ins.get("insight", "") for ins in insights if ins.get("insight")
                    ],
                    relevance_score=extraction.get("relevance_score", 0.5),
                )

                # Append notable quotes as separate findings
                for quote in extraction.get("notable_quotes", []):
                    if quote and len(quote) > 20:
                        quote_finding = ResearchFinding(
                            dimension="voice_of_customer",
                            source_url=url,
                            source_type=extraction.get("source_type", "other"),
                            content_snippet=quote,
                            extracted_insights=[quote],
                            relevance_score=extraction.get("relevance_score", 0.5),
                        )
                        findings.append(quote_finding)

                findings.append(finding)

        self._status(
            f"[{self.dimension}] Complete — {len(findings)} findings from {len(queries)} queries"
        )
        return findings
