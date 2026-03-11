"""Phase 2: Research Orchestrator.

Spawns all research agents using ThreadPoolExecutor for parallelism.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from agents.researchers.pain_point_researcher import PainPointResearcher
from agents.researchers.buying_trigger_researcher import BuyingTriggerResearcher
from agents.researchers.fear_objection_researcher import FearObjectionResearcher
from agents.researchers.industry_researcher import IndustryResearcher
from agents.researchers.channel_researcher import ChannelResearcher
from agents.researchers.competitor_reviewer import CompetitorReviewer
from agents.researchers.emotional_language_miner import EmotionalLanguageMiner
from models.data_models import BusinessProfile, ResearchFinding, ResearchPlan
from services.dataforseo_client import DataForSEOClient
from services.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)


def run_research(
    llm: OpenRouterClient,
    dfs: DataForSEOClient,
    profile: BusinessProfile,
    plan: ResearchPlan,
    status_callback: Callable[[str], None] | None = None,
) -> list[ResearchFinding]:
    """Run all research agents in parallel and return combined findings.

    Args:
        llm: OpenRouter client (shared across agents).
        dfs: DataForSEO client (shared, rate-limited via threading.Lock).
        profile: Business profile from Phase 1.
        plan: Research plan with queries per dimension.
        status_callback: Optional callback for progress updates.

    Returns:
        Combined list of ResearchFinding from all agents.
    """
    cb = status_callback or (lambda _: None)

    # Build agent instances
    agents_and_queries = [
        (PainPointResearcher(llm, dfs, profile, cb), plan.pain_point_queries),
        (BuyingTriggerResearcher(llm, dfs, profile, cb), plan.buying_trigger_queries),
        (FearObjectionResearcher(llm, dfs, profile, cb), plan.fear_objection_queries),
        (IndustryResearcher(llm, dfs, profile, cb), plan.industry_research_queries),
        (ChannelResearcher(llm, dfs, profile, cb), plan.channel_queries),
        (EmotionalLanguageMiner(llm, dfs, profile, cb), plan.emotional_language_queries),
    ]

    # Only add competitor reviewer if there are competitor queries
    if plan.competitor_queries:
        agents_and_queries.append(
            (CompetitorReviewer(llm, dfs, profile, cb), plan.competitor_queries)
        )

    cb(f"Launching {len(agents_and_queries)} research agents in parallel...")

    def _run_agent(agent, queries):
        try:
            return agent.research(agent.get_queries(queries))
        except Exception as e:
            logger.error("Research agent %s failed: %s", agent.dimension, e)
            return []

    # Run all agents concurrently via thread pool
    all_findings: list[ResearchFinding] = []

    with ThreadPoolExecutor(max_workers=len(agents_and_queries)) as executor:
        futures = {
            executor.submit(_run_agent, agent, queries): agent.dimension
            for agent, queries in agents_and_queries
        }

        for future in as_completed(futures):
            dimension = futures[future]
            try:
                findings_list = future.result()
                if isinstance(findings_list, list):
                    all_findings.extend(findings_list)
            except Exception as e:
                logger.error("Agent %s raised: %s", dimension, e)

    cb(f"Research complete — {len(all_findings)} total findings collected")
    return all_findings
