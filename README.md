# ICP Generator

A multi-agent Streamlit app that generates deep psychographic Ideal Customer Profiles (ICPs) using AI-powered internet research.

## What It Does

Enter basic business information and the system:

1. **Analyzes the business** to understand industry, vertical, and market positioning
2. **Deploys 7 research agents in parallel** that search the web for audience psychology data
3. **Synthesizes findings** and identifies distinct customer segments
4. **Generates deep psychographic profiles** with pain points, emotional triggers, buying motivations, objections, and communication blueprints

## Key Features

- **Deep psychographic focus** — pain point taxonomy (primary, secondary, latent), emotional trigger mapping, decision-making psychology
- **Evidence-based** — all insights grounded in real web research with confidence ratings
- **Multi-segment** — automatically identifies 1-5 distinct ICP segments
- **Voice of Customer** — captures verbatim quotes and emotional language patterns
- **Actionable output** — communication blueprints with specific vocabulary, tone, and channel recommendations

## Tech Stack

- **Streamlit** — web interface
- **OpenRouter** — AI models (Gemini 2.0 Flash for research, Claude Sonnet 4 for analysis)
- **DataForSEO** — SERP search and content parsing for internet research

## Setup on Streamlit Cloud

1. Fork or connect this repo to Streamlit Cloud
2. In the app's **Secrets** tab, add:

```toml
[openrouter]
api_key = "sk-or-v1-your-key-here"

[dataforseo]
login = "your-email@example.com"
password = "your-api-password"
```

3. Deploy

## Cost Per Report

- DataForSEO: ~$1-2 (SERP queries + content parsing)
- OpenRouter: ~$1-3 (LLM tokens)
- **Total: ~$2-5 per ICP report**

## Research Agents

| Agent | What It Finds |
|-------|--------------|
| Pain Point Researcher | Complaints, frustrations from Reddit, reviews, forums |
| Buying Trigger Researcher | What starts the buying process, decision criteria |
| Fear & Objection Researcher | What stops purchases, scam fears, price concerns |
| Industry Researcher | Published studies, surveys, market data |
| Channel Researcher | How audiences discover and evaluate solutions |
| Competitor Reviewer | Sentiment patterns in competitor reviews |
| Emotional Language Miner | Verbatim emotional language from testimonials/complaints |

## Report Structure

Each ICP segment includes:

1. **Demographic Snapshot**
2. **Pain Point Taxonomy** (primary, secondary, latent + emotional impact)
3. **Emotional Trigger Map** (anxiety, aspiration, social, trust)
4. **Decision-Making Psychology**
5. **Buying Motivations** (rational, emotional, social, fear-based)
6. **Objections & Barriers**
7. **Communication Blueprint** (language, tone, channels, content formats)
8. **Voice of Customer Evidence** (verbatim quotes with sources)

Plus: Executive Summary, Cross-Segment Analysis, Strategic Recommendations, Research Confidence Assessment.
