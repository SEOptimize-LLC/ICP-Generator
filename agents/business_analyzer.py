"""Phase 1: Business Analyzer Agent.

Parses user input and generates a structured business profile + research plan.
"""

from __future__ import annotations

import logging

from config.prompts import BUSINESS_ANALYZER_SYSTEM, BUSINESS_ANALYZER_USER
from config.settings import MODEL_FAST
from models.data_models import BusinessProfile, ResearchPlan
from services.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)


def analyze_business(
    llm: OpenRouterClient,
    business_input: str,
) -> tuple[BusinessProfile, ResearchPlan]:
    """Analyze business info and produce a profile + research plan.

    Args:
        llm: OpenRouter client instance.
        business_input: Raw text with business information from the form.

    Returns:
        Tuple of (BusinessProfile, ResearchPlan).
    """
    user_prompt = BUSINESS_ANALYZER_USER.format(business_input=business_input)

    data = llm.analyze_json(
        system_prompt=BUSINESS_ANALYZER_SYSTEM,
        user_prompt=user_prompt,
        model=MODEL_FAST,
        max_tokens=4096,
    )

    profile_data = data.get("profile", {})
    plan_data = data.get("research_plan", {})

    profile = BusinessProfile(
        name=profile_data.get("name", "Unknown"),
        industry=profile_data.get("industry", "Unknown"),
        vertical=profile_data.get("vertical", ""),
        business_model=profile_data.get("business_model", "B2C"),
        services=profile_data.get("services", []),
        geographic_scope=profile_data.get("geographic_scope", ""),
        service_area=profile_data.get("service_area", ""),
        price_positioning=profile_data.get("price_positioning", ""),
        competitors=profile_data.get("competitors", []),
        target_audience_hints=profile_data.get("target_audience_hints", []),
        usp=profile_data.get("usp", ""),
    )

    research_plan = ResearchPlan(
        pain_point_queries=plan_data.get("pain_point_queries", []),
        buying_trigger_queries=plan_data.get("buying_trigger_queries", []),
        fear_objection_queries=plan_data.get("fear_objection_queries", []),
        industry_research_queries=plan_data.get("industry_research_queries", []),
        channel_queries=plan_data.get("channel_queries", []),
        competitor_queries=plan_data.get("competitor_queries", []),
        emotional_language_queries=plan_data.get("emotional_language_queries", []),
    )

    logger.info(
        "Business analyzed: %s (%s / %s) — %d total queries generated",
        profile.name,
        profile.industry,
        profile.vertical,
        sum(
            len(getattr(research_plan, f))
            for f in research_plan.__dataclass_fields__
        ),
    )

    return profile, research_plan
