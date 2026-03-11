"""Configuration settings loaded from Streamlit secrets."""

import streamlit as st

# --- API Credentials ---
def get_openrouter_key() -> str:
    return st.secrets["openrouter"]["api_key"]

def get_dataforseo_credentials() -> tuple[str, str]:
    return st.secrets["dataforseo"]["login"], st.secrets["dataforseo"]["password"]

# --- API Endpoints ---
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DATAFORSEO_BASE_URL = "https://api.dataforseo.com/v3"

# --- Model IDs ---
MODEL_FAST = "google/gemini-2.0-flash-001"
MODEL_REASONING = "anthropic/claude-sonnet-4"

# --- Research Parameters ---
MAX_SERP_QUERIES_PER_DIMENSION = 8
MAX_SERP_RESULTS_PER_QUERY = 10
MAX_PAGES_TO_PARSE_PER_QUERY = 3
MAX_CONCURRENT_API_CALLS = 3
MIN_API_DELAY_SECONDS = 1.0
MAX_CONTENT_LENGTH = 5000

# --- Segment Limits ---
MIN_ICP_SEGMENTS = 1
MAX_ICP_SEGMENTS = 5
MIN_EVIDENCE_PER_SEGMENT = 3
