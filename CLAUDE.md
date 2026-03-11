# ICP Generator — Claude Code Guidelines

## Project Overview

Multi-agent Streamlit app that generates deep psychographic ICPs using OpenRouter + DataForSEO.

## Architecture

- **app.py** — Streamlit entry point with form, progress tracking, and results display
- **agents/** — Pipeline stages: business_analyzer → research_orchestrator → research_synthesizer → icp_generator
- **agents/researchers/** — 7 specialized research agents (pain points, buying triggers, fears, industry data, channels, competitor reviews, emotional language)
- **services/** — API clients for OpenRouter and DataForSEO
- **config/** — Settings (from st.secrets) and all LLM prompt templates
- **models/** — Dataclasses for BusinessProfile, ResearchFinding, ICPSegment, SynthesizedResearch

## Key Files

- `config/prompts.py` — All LLM prompts. Edit here to change research or report quality.
- `config/settings.py` — Model IDs, research parameters, rate limits.
- `agents/researchers/base_researcher.py` — Shared research logic (SERP → parse → extract).

## Deployment

- Deployed on Streamlit Cloud
- Secrets configured in Streamlit Cloud Secrets tab
- GitHub repo: https://github.com/SEOptimize-LLC/ICP-Generator

## Priority

The psychographic depth is the core value — pain points, triggers, motivations, objections. Always prioritize research quality over speed.
