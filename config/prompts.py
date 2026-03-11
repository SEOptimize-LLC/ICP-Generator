"""All LLM prompt templates for the ICP Generator pipeline."""

# =============================================================================
# PHASE 1: BUSINESS ANALYZER
# =============================================================================

BUSINESS_ANALYZER_SYSTEM = """You are an expert business analyst. Given information about a business, you must:
1. Extract and structure the business profile
2. Generate a comprehensive research plan with search queries for psychographic audience research

You MUST respond with valid JSON only. No markdown, no explanation."""

BUSINESS_ANALYZER_USER = """Analyze this business and generate a research plan.

BUSINESS INFORMATION:
{business_input}

Return a JSON object with this exact structure:
{{
  "profile": {{
    "name": "Business name",
    "industry": "Primary industry (e.g., plumbing, SaaS, fitness)",
    "vertical": "Specific vertical (e.g., residential plumbing, ERP consulting, functional medicine)",
    "business_model": "B2C or B2B or B2B2C or DTC",
    "services": ["service 1", "service 2"],
    "geographic_scope": "local or regional or national or global",
    "service_area": "Specific area if local/regional, empty string otherwise",
    "price_positioning": "budget or mid-market or premium",
    "competitors": ["competitor 1", "competitor 2"],
    "target_audience_hints": ["hint about who their customers are"],
    "usp": "Unique selling proposition"
  }},
  "research_plan": {{
    "pain_point_queries": [
      "8-10 search queries designed to find customer pain points, complaints, and frustrations. Include queries targeting Reddit, review sites, forums, BBB. Use the specific industry terms and service types."
    ],
    "buying_trigger_queries": [
      "8-10 queries to find what triggers the buying decision. Include 'how to choose', 'signs you need', 'when to hire', buying guide queries."
    ],
    "fear_objection_queries": [
      "8-10 queries about what stops people from buying. Include scam warnings, 'is it worth it', hidden cost, red flag queries."
    ],
    "industry_research_queries": [
      "8-10 queries for published studies, surveys, market research, demographic data about this industry's customers."
    ],
    "channel_queries": [
      "6-8 queries about how this target audience finds and evaluates solutions, media consumption, information sources."
    ],
    "competitor_queries": [
      "6-8 queries mining competitor reviews for sentiment patterns. Only if competitors were identified."
    ],
    "emotional_language_queries": [
      "6-8 queries to find emotionally charged testimonials, stories, complaints with raw emotional language."
    ]
  }}
}}

IMPORTANT GUIDELINES FOR QUERY GENERATION:
- Make queries specific to this exact industry and service type, not generic
- Include site-specific queries (site:reddit.com, site:quora.com) for pain points
- Use the language that real customers would use, not industry jargon
- For local businesses, include geographic terms where relevant
- Include queries that target both positive (testimonials) and negative (complaints) experiences
- Include current year (2025/2026) in some industry research queries for recency
- For B2B: focus on business buyer pain points, ROI concerns, implementation fears
- For B2C: focus on consumer frustrations, trust issues, value concerns"""

# =============================================================================
# PHASE 2: RESEARCH EXTRACTION
# =============================================================================

RESEARCH_EXTRACTION_SYSTEM = """You are a psychographic research analyst. Your job is to extract actionable audience insights from web content.

Focus on:
- Pain points, frustrations, complaints
- Emotional language and sentiment
- Decision-making triggers and patterns
- Trust and credibility signals
- Objections and barriers to purchase

You MUST respond with valid JSON only."""

RESEARCH_EXTRACTION_USER = """Extract psychographic insights from this content.

RESEARCH DIMENSION: {dimension}
INDUSTRY CONTEXT: {industry} ({vertical})
BUSINESS MODEL: {business_model}

SOURCE URL: {source_url}
CONTENT:
{content}

Return a JSON object:
{{
  "insights": [
    {{
      "insight": "Specific, actionable insight extracted from the content",
      "evidence": "Direct quote or paraphrase from the content supporting this insight",
      "category": "pain_point | buying_trigger | fear | objection | emotional_language | channel_preference | demographic",
      "intensity": "high | medium | low"
    }}
  ],
  "source_type": "reddit | forum | review_site | industry_report | blog | news | academic | q_and_a | other",
  "relevance_score": 0.0-1.0,
  "notable_quotes": ["Exact verbatim quotes from real people that reveal emotional language or pain points"]
}}

RULES:
- Only extract insights that are DIRECTLY supported by the content
- Prefer verbatim quotes over paraphrases
- Score relevance based on how directly the content addresses the target audience's psychology
- Mark intensity based on emotional weight (high = deeply emotional, low = passing mention)
- If the content has no relevant insights, return empty insights array with relevance_score 0.0"""

# =============================================================================
# PHASE 3: RESEARCH SYNTHESIS
# =============================================================================

SYNTHESIS_CATEGORIZE_SYSTEM = """You are a research data analyst. Your job is to deduplicate and categorize raw research findings into structured buckets.

You MUST respond with valid JSON only."""

SYNTHESIS_CATEGORIZE_USER = """Deduplicate and categorize these research findings.

BUSINESS: {business_name} ({industry}, {vertical})
BUSINESS MODEL: {business_model}

RAW FINDINGS:
{findings_json}

Return a JSON object organizing all unique insights into categories:
{{
  "pain_points": {{
    "primary": ["Top pain points mentioned most frequently or with highest intensity"],
    "secondary": ["Less frequent but still significant pain points"],
    "latent": ["Implied or emerging pain points that customers may not explicitly state"]
  }},
  "buying_triggers": {{
    "events": ["Specific events that trigger the buying process"],
    "internal": ["Internal realizations or emotional states"],
    "external": ["External circumstances or pressures"]
  }},
  "fears_and_objections": {{
    "price_related": ["Price and value concerns"],
    "trust_related": ["Trust, credibility, scam fears"],
    "timing_related": ["Procrastination, timing concerns"],
    "switching_related": ["Costs of changing providers"]
  }},
  "emotional_patterns": {{
    "anxiety_language": ["Words and phrases expressing worry or stress"],
    "aspiration_language": ["Words expressing hopes and desires"],
    "frustration_language": ["Words expressing anger or annoyance"],
    "relief_language": ["Words expressing relief after purchase"]
  }},
  "channel_preferences": {{
    "discovery": ["How they first learn about solutions"],
    "validation": ["How they verify and compare options"],
    "decision": ["Final decision-making channels"]
  }},
  "demographic_signals": {{
    "age_indicators": ["Any age-related patterns"],
    "income_indicators": ["Income and spending patterns"],
    "role_indicators": ["Professional roles or life stages"]
  }},
  "notable_quotes": ["Top 10-15 verbatim quotes that best capture customer psychology"],
  "total_unique_insights": 0,
  "total_sources": 0
}}

RULES:
- Deduplicate similar insights — merge into the strongest version
- Rank within each category by frequency and intensity
- Preserve exact quotes without modification
- If a category has no data, use empty arrays"""

SYNTHESIS_SEGMENT_SYSTEM = """You are a market segmentation expert with deep expertise in psychographic profiling and buyer psychology. Your task is to identify distinct customer segments from categorized research data.

You MUST respond with valid JSON only."""

SYNTHESIS_SEGMENT_USER = """Identify distinct ICP segments from this categorized research data.

BUSINESS: {business_name}
INDUSTRY: {industry} ({vertical})
BUSINESS MODEL: {business_model}
GEOGRAPHIC SCOPE: {geographic_scope}

CATEGORIZED RESEARCH DATA:
{categorized_json}

Identify between {min_segments} and {max_segments} distinct customer segments. Each segment must:
- Be supported by at least {min_evidence} distinct research findings
- Differ from other segments on at least 2 of these axes: urgency, price sensitivity, decision-making style, buying role, life/business stage
- Represent a meaningfully different buyer psychology

Return a JSON object:
{{
  "segments": [
    {{
      "segment_id": 1,
      "name": "Short memorable name (e.g., 'The Emergency Homeowner', 'The Research-Driven IT Director')",
      "description": "2-3 sentence description of who this person is and why they're a distinct segment",
      "differentiation_axes": ["axis 1", "axis 2"],
      "evidence_summary": "Brief summary of what research data supports this segment",
      "evidence_count": 0,
      "estimated_market_share": "Rough percentage of total addressable audience",
      "urgency_level": "high | medium | low",
      "price_sensitivity": "high | medium | low",
      "decision_style": "impulsive | balanced | research-heavy",
      "primary_pain_points": ["Top 3 pain points for this segment"],
      "primary_motivations": ["Top 3 buying motivations"],
      "key_objections": ["Top 3 objections"]
    }}
  ],
  "segmentation_rationale": "Why these segments were chosen and how they differ",
  "confidence_assessment": {{
    "overall": "high | medium | low",
    "pain_points": "high | medium | low",
    "buying_triggers": "high | medium | low",
    "fears_objections": "high | medium | low",
    "emotional_language": "high | medium | low",
    "channel_data": "high | medium | low",
    "demographics": "high | medium | low"
  }},
  "data_gaps": ["List any areas where research data was insufficient"]
}}"""

# =============================================================================
# PHASE 4: ICP REPORT GENERATION
# =============================================================================

ICP_SEGMENT_SYSTEM = """You are an expert psychographic profiler and buyer psychology specialist. Your task is to create a deep, detailed Ideal Customer Profile for a specific market segment.

Write in a professional analytical style. Ground every claim in the research evidence provided. When evidence is limited, explicitly note it as a hypothesis.

Output in clean, well-structured markdown."""

ICP_SEGMENT_USER = """Generate a deep psychographic ICP for this segment.

BUSINESS: {business_name}
INDUSTRY: {industry} ({vertical})
BUSINESS MODEL: {business_model}
USP: {usp}

SEGMENT: {segment_name}
SEGMENT DESCRIPTION: {segment_description}

FULL CATEGORIZED RESEARCH DATA:
{categorized_json}

SEGMENT-SPECIFIC DATA:
- Primary Pain Points: {primary_pain_points}
- Primary Motivations: {primary_motivations}
- Key Objections: {key_objections}
- Urgency Level: {urgency_level}
- Price Sensitivity: {price_sensitivity}
- Decision Style: {decision_style}

CONFIDENCE ASSESSMENT:
{confidence_json}

NOTABLE QUOTES FROM RESEARCH:
{notable_quotes}

Generate a COMPLETE ICP profile with these exact sections:

## {segment_name}

### 1. Demographic Snapshot
Age range, income bracket, location profile, household/company characteristics, role or life stage, where they spend time online.

### 2. Pain Point Taxonomy

#### Primary Pain Points (Active, Top-of-Mind)
For each: describe the pain point, how it manifests in daily life, and the emotional impact. Support with evidence.

#### Secondary Pain Points (Recognized but Lower Priority)
Related frustrations and their compounding effects.

#### Latent Pain Points (Not Yet Articulated)
Problems they have but haven't named. Future pain points based on trajectory.

### 3. Emotional Trigger Map

#### Anxiety Triggers
What creates urgency or fear that pushes them toward action.

#### Aspiration Triggers
What they dream about achieving — the ideal outcome.

#### Social Triggers
Peer pressure, status, keeping up, social proof dynamics.

#### Trust Triggers
What makes them feel safe choosing a provider — credibility signals.

### 4. Decision-Making Psychology
- How they research solutions (channels, depth, duration)
- Who influences their decision (people, platforms, content)
- What information they need before committing
- Their typical decision timeline
- Deal-breakers that eliminate options immediately

### 5. Buying Motivations

#### Rational Motivations
Cost savings, efficiency, compliance, risk reduction, measurable outcomes.

#### Emotional Motivations
Peace of mind, relief from stress, pride, excitement, confidence.

#### Social Motivations
Peer approval, status, reputation, belonging, recommendations to give.

#### Fear-Based Motivations
What happens if they do NOT act — consequences of inaction.

### 6. Objections & Barriers

#### Price Objections
Specific concerns and the psychology behind them.

#### Trust Objections
Skepticism patterns, what creates doubt, past bad experiences.

#### Timing Objections
Why they delay, rationalizations for waiting.

#### Switching Objections
What keeps them with current provider (if applicable).

### 7. Communication Blueprint

#### Language Patterns
Exact words and phrases this segment uses to describe their problems. Include specific vocabulary.

#### Vocabulary to Use (and Avoid)
Words that resonate vs. words that trigger skepticism or disengagement.

#### Tone Preferences
Formal vs. casual, data-driven vs. story-driven, urgent vs. reassuring.

#### Channel Preferences
Where they discover solutions, where they validate, where they convert.

#### Content Format Preferences
Video vs. text, long-form vs. short, testimonials vs. data, comparison tools vs. guides.

### 8. Voice of Customer Evidence
Include 3-5 representative verbatim quotes from the research that capture this segment's psychology. Attribute each quote to its source type (e.g., "Reddit user", "Google review", "Industry survey respondent").

IMPORTANT RULES:
- Be SPECIFIC, not generic. No filler like "they want a good experience"
- Ground claims in the actual research data provided
- Where data is limited, label as "[Hypothesis based on limited data]"
- Use concrete examples relevant to THIS industry
- Include the emotional dimension for every pain point and motivation
- The Communication Blueprint should give actionable copy guidance"""

ICP_EXECUTIVE_SUMMARY_SYSTEM = """You are a strategic marketing consultant. Generate an executive summary and cross-segment analysis for an ICP report.

Output in clean, well-structured markdown."""

ICP_EXECUTIVE_SUMMARY_USER = """Generate the executive summary and cross-segment analysis.

BUSINESS: {business_name}
INDUSTRY: {industry} ({vertical})
NUMBER OF SEGMENTS: {num_segments}

SEGMENT SUMMARIES:
{segments_summary}

CONFIDENCE ASSESSMENT:
{confidence_json}

DATA GAPS:
{data_gaps}

Generate these sections in markdown:

# ICP Report: {business_name}

**Generated:** {date}
**Industry:** {industry} ({vertical})
**Business Model:** {business_model}

---

## Executive Summary
- Number of ICP segments identified and why
- Top 3-5 key insights across all segments
- Research confidence assessment (which dimensions had strong data vs. limited)

## Cross-Segment Analysis
- Key differences between segments (table format if helpful)
- Shared pain points across all segments
- Priority ranking of segments by addressable opportunity and urgency

## Strategic Recommendations
- Which segment to target first and why
- Messaging hierarchy for each segment (primary hook, supporting proof, call to action angle)
- Quick-win opportunities identified in the research
- Content strategy suggestions per segment

## Research Methodology & Confidence
- Research dimensions covered
- Confidence rating per dimension (high/medium/low) with brief explanation
- Data gaps and recommended follow-up research
- Number of sources consulted"""
