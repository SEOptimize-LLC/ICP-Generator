"""Data models shared across all agents."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class BusinessProfile:
    name: str
    industry: str
    vertical: str = ""
    business_model: str = ""  # B2C, B2B, B2B2C, DTC
    services: list[str] = field(default_factory=list)
    geographic_scope: str = ""  # local, regional, national, global
    service_area: str = ""
    price_positioning: str = ""  # budget, mid-market, premium
    competitors: list[str] = field(default_factory=list)
    target_audience_hints: list[str] = field(default_factory=list)
    website: str = ""
    usp: str = ""
    additional_context: str = ""


@dataclass
class ResearchPlan:
    """Search queries grouped by research dimension."""
    pain_point_queries: list[str] = field(default_factory=list)
    buying_trigger_queries: list[str] = field(default_factory=list)
    fear_objection_queries: list[str] = field(default_factory=list)
    industry_research_queries: list[str] = field(default_factory=list)
    channel_queries: list[str] = field(default_factory=list)
    competitor_queries: list[str] = field(default_factory=list)
    emotional_language_queries: list[str] = field(default_factory=list)


@dataclass
class ResearchFinding:
    dimension: str  # pain_point, buying_trigger, fear_objection, etc.
    source_url: str
    source_type: str  # reddit, review_site, industry_report, forum, etc.
    content_snippet: str
    extracted_insights: list[str] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class ICPSegment:
    segment_id: int
    name: str
    description: str
    evidence_count: int = 0
    demographics: dict = field(default_factory=dict)
    pain_points: dict = field(default_factory=dict)
    emotional_triggers: dict = field(default_factory=dict)
    decision_making: dict = field(default_factory=dict)
    buying_motivations: dict = field(default_factory=dict)
    objections: dict = field(default_factory=dict)
    communication_blueprint: dict = field(default_factory=dict)
    voice_of_customer: list[dict] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class SynthesizedResearch:
    business_profile: BusinessProfile
    segments: list[ICPSegment] = field(default_factory=list)
    all_findings: list[ResearchFinding] = field(default_factory=list)
    categorized_findings: dict = field(default_factory=dict)
    research_quality: dict = field(default_factory=dict)
    data_gaps: list[str] = field(default_factory=list)
