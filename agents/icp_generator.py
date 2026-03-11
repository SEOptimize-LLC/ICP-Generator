"""Phase 4: ICP Report Generator.

Generates deep psychographic profiles for each segment and the executive summary.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Callable

from config.prompts import (
    ICP_SEGMENT_SYSTEM,
    ICP_SEGMENT_USER,
    ICP_EXECUTIVE_SUMMARY_SYSTEM,
    ICP_EXECUTIVE_SUMMARY_USER,
)
from config.settings import MODEL_REASONING
from models.data_models import SynthesizedResearch
from services.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)


def generate_icp_report(
    llm: OpenRouterClient,
    research: SynthesizedResearch,
    status_callback: Callable[[str], None] | None = None,
) -> str:
    """Generate the full ICP markdown report.

    Args:
        llm: OpenRouter client.
        research: Synthesized research with segments.
        status_callback: Optional progress callback.

    Returns:
        Complete markdown report string.
    """
    cb = status_callback or (lambda _: None)
    profile = research.business_profile
    categorized_json = json.dumps(research.categorized_findings, indent=1)
    confidence_json = json.dumps(research.research_quality, indent=1)

    # Collect notable quotes
    notable_quotes = research.categorized_findings.get("notable_quotes", [])
    quotes_text = "\n".join(f'- "{q}"' for q in notable_quotes[:15])

    # --- Generate each segment profile ---
    segment_markdowns: list[str] = []

    for i, segment in enumerate(research.segments):
        cb(f"Generating ICP for segment {i+1}/{len(research.segments)}: {segment.name}...")

        segment_md = llm.analyze(
            system_prompt=ICP_SEGMENT_SYSTEM,
            user_prompt=ICP_SEGMENT_USER.format(
                business_name=profile.name,
                industry=profile.industry,
                vertical=profile.vertical,
                business_model=profile.business_model,
                usp=profile.usp or "Not specified",
                segment_name=segment.name,
                segment_description=segment.description,
                categorized_json=categorized_json,
                primary_pain_points=json.dumps(segment.pain_points.get("primary", [])),
                primary_motivations=json.dumps(segment.buying_motivations.get("primary", [])),
                key_objections=json.dumps(segment.objections.get("primary", [])),
                urgency_level=segment.demographics.get("urgency_level", "medium"),
                price_sensitivity=segment.demographics.get("price_sensitivity", "medium"),
                decision_style=segment.demographics.get("decision_style", "balanced"),
                confidence_json=confidence_json,
                notable_quotes=quotes_text,
            ),
            model=MODEL_REASONING,
            max_tokens=6000,
        )

        segment_markdowns.append(segment_md)

    # --- Generate executive summary ---
    cb("Generating executive summary and cross-segment analysis...")

    segments_summary = "\n\n".join(
        f"**Segment {i+1}: {seg.name}**\n{seg.description}\n"
        f"- Pain Points: {json.dumps(seg.pain_points.get('primary', []))}\n"
        f"- Motivations: {json.dumps(seg.buying_motivations.get('primary', []))}\n"
        f"- Objections: {json.dumps(seg.objections.get('primary', []))}"
        for i, seg in enumerate(research.segments)
    )

    exec_summary = llm.analyze(
        system_prompt=ICP_EXECUTIVE_SUMMARY_SYSTEM,
        user_prompt=ICP_EXECUTIVE_SUMMARY_USER.format(
            business_name=profile.name,
            industry=profile.industry,
            vertical=profile.vertical,
            business_model=profile.business_model,
            num_segments=len(research.segments),
            segments_summary=segments_summary,
            confidence_json=confidence_json,
            data_gaps=json.dumps(research.data_gaps),
            date=date.today().isoformat(),
        ),
        model=MODEL_REASONING,
        max_tokens=4000,
    )

    # --- Assemble full report ---
    report_parts = [exec_summary]

    for i, seg_md in enumerate(segment_markdowns):
        report_parts.append(f"\n\n---\n\n# Segment {i+1} — Detailed Profile\n\n{seg_md}")

    full_report = "\n".join(report_parts)

    cb("ICP report generation complete!")
    return full_report
