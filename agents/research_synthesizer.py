"""Phase 3: Research Synthesizer.

Two-pass approach: Gemini Flash for categorization, Claude Sonnet for segmentation.
"""

from __future__ import annotations

import json
import logging
from typing import Callable

from config.prompts import (
    SYNTHESIS_CATEGORIZE_SYSTEM,
    SYNTHESIS_CATEGORIZE_USER,
    SYNTHESIS_SEGMENT_SYSTEM,
    SYNTHESIS_SEGMENT_USER,
)
from config.settings import (
    MODEL_FAST,
    MODEL_REASONING,
    MIN_ICP_SEGMENTS,
    MAX_ICP_SEGMENTS,
    MIN_EVIDENCE_PER_SEGMENT,
)
from models.data_models import (
    BusinessProfile,
    ICPSegment,
    ResearchFinding,
    SynthesizedResearch,
)
from services.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)


async def synthesize_research(
    llm: OpenRouterClient,
    profile: BusinessProfile,
    findings: list[ResearchFinding],
    status_callback: Callable[[str], None] | None = None,
) -> SynthesizedResearch:
    """Synthesize raw findings into categorized data and ICP segments.

    Args:
        llm: OpenRouter client.
        profile: Business profile from Phase 1.
        findings: All research findings from Phase 2.
        status_callback: Optional progress callback.

    Returns:
        SynthesizedResearch with categorized data and segment definitions.
    """
    cb = status_callback or (lambda _: None)

    # --- Pass 1: Categorize with Gemini Flash ---
    cb("Synthesizing research — Pass 1: Categorizing findings...")

    findings_json = json.dumps(
        [
            {
                "dimension": f.dimension,
                "source_type": f.source_type,
                "source_url": f.source_url,
                "insights": f.extracted_insights,
                "relevance": f.relevance_score,
                "snippet": f.content_snippet[:300],
            }
            for f in findings
        ],
        indent=1,
    )

    categorized = await llm.analyze_json(
        system_prompt=SYNTHESIS_CATEGORIZE_SYSTEM,
        user_prompt=SYNTHESIS_CATEGORIZE_USER.format(
            business_name=profile.name,
            industry=profile.industry,
            vertical=profile.vertical,
            business_model=profile.business_model,
            findings_json=findings_json,
        ),
        model=MODEL_FAST,
        max_tokens=8192,
    )

    cb(
        f"Categorization complete — {categorized.get('total_unique_insights', '?')} unique insights"
    )

    # --- Pass 2: Identify segments with Claude Sonnet ---
    cb("Synthesizing research — Pass 2: Identifying ICP segments...")

    segmentation = await llm.analyze_json(
        system_prompt=SYNTHESIS_SEGMENT_SYSTEM,
        user_prompt=SYNTHESIS_SEGMENT_USER.format(
            business_name=profile.name,
            industry=profile.industry,
            vertical=profile.vertical,
            business_model=profile.business_model,
            geographic_scope=profile.geographic_scope,
            categorized_json=json.dumps(categorized, indent=1),
            min_segments=MIN_ICP_SEGMENTS,
            max_segments=MAX_ICP_SEGMENTS,
            min_evidence=MIN_EVIDENCE_PER_SEGMENT,
        ),
        model=MODEL_REASONING,
        max_tokens=4096,
    )

    # Build ICPSegment objects
    segments: list[ICPSegment] = []
    for seg_data in segmentation.get("segments", []):
        segment = ICPSegment(
            segment_id=seg_data.get("segment_id", len(segments) + 1),
            name=seg_data.get("name", f"Segment {len(segments) + 1}"),
            description=seg_data.get("description", ""),
            evidence_count=seg_data.get("evidence_count", 0),
            pain_points={"primary": seg_data.get("primary_pain_points", [])},
            buying_motivations={"primary": seg_data.get("primary_motivations", [])},
            objections={"primary": seg_data.get("key_objections", [])},
        )
        segments.append(segment)

    confidence = segmentation.get("confidence_assessment", {})
    data_gaps = segmentation.get("data_gaps", [])

    cb(f"Identified {len(segments)} ICP segments")

    return SynthesizedResearch(
        business_profile=profile,
        segments=segments,
        all_findings=findings,
        categorized_findings=categorized,
        research_quality=confidence,
        data_gaps=data_gaps,
    )
