"""Phase 2: Research Orchestrator.

Spawns all research agents in parallel and collects their findings.
"""

from __future__ import annotations

import asyncio
import logging
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


async def run_research(
    llm: OpenRouterClient,
    dfs: DataForSEOClient,
    profile: BusinessProfile,
    plan: ResearchPlan,
    status_callback: Callable[[str], None] | None = None,
) -> list[ResearchFinding]:
    """Run all research agents in parallel and return combined findings.

    Args:
        llm: OpenRouter client (shared across agents).
        dfs: DataForSEO client (shared, rate-limited).
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

    async def _run_agent(agent, queries):
        try:
            return await agent.research(agent.get_queries(queries))
        except Exception as e:
            logger.error("Research agent %s failed: %s", agent.dimension, e)
            return []

    # Run all agents concurrently
    results = await asyncio.gather(
        *[_run_agent(agent, queries) for agent, queries in agents_and_queries],
        return_exceptions=False,
    )

    # Flatten results
    all_findings: list[ResearchFinding] = []
    for findings_list in results:
        if isinstance(findings_list, list):
            all_findings.extend(findings_list)

    cb(f"Research complete — {len(all_findings)} total findings collected")
    return all_findings
