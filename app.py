"""ICP Generator — Streamlit App.

Multi-agent psychographic ICP generator powered by OpenRouter + DataForSEO.
"""

import asyncio
import logging
from datetime import date

import nest_asyncio
import streamlit as st

from agents.business_analyzer import analyze_business
from agents.research_orchestrator import run_research
from agents.research_synthesizer import synthesize_research
from agents.icp_generator import generate_icp_report
from services.openrouter_client import OpenRouterClient
from services.dataforseo_client import DataForSEOClient
from utils.markdown_writer import clean_markdown, format_report_filename

# Allow nested event loops (required for Streamlit)
nest_asyncio.apply()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Page Config ---
st.set_page_config(
    page_title="ICP Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
with st.sidebar:
    st.title("ICP Generator")
    st.caption("Deep psychographic profiling powered by AI")
    st.divider()

    # API Status
    st.subheader("API Status")
    try:
        from config.settings import get_openrouter_key, get_dataforseo_credentials

        or_key = get_openrouter_key()
        dfs_login, dfs_pass = get_dataforseo_credentials()

        if or_key:
            st.success("OpenRouter: Connected", icon="✅")
        else:
            st.error("OpenRouter: No API key", icon="❌")

        if dfs_login and dfs_pass:
            st.success("DataForSEO: Connected", icon="✅")
        else:
            st.error("DataForSEO: No credentials", icon="❌")

        apis_ready = bool(or_key and dfs_login and dfs_pass)
    except Exception:
        st.error("Missing secrets configuration", icon="❌")
        apis_ready = False

    st.divider()
    st.markdown(
        "**How it works:**\n"
        "1. Enter business details\n"
        "2. AI analyzes the business\n"
        "3. 7 research agents search the web\n"
        "4. Findings are synthesized into ICP segments\n"
        "5. Deep psychographic profiles are generated"
    )
    st.divider()
    st.markdown(
        "**Estimated per report:**\n"
        "- Cost: $2-5\n"
        "- Time: 3-5 minutes\n"
        "- Sources: 50-200+ web pages"
    )

# --- Main Area ---
st.header("Generate Ideal Customer Profile")

# --- Input Form ---
if "report" not in st.session_state:
    st.session_state.report = None
if "logs" not in st.session_state:
    st.session_state.logs = []
if "running" not in st.session_state:
    st.session_state.running = False

with st.form("business_form"):
    col1, col2 = st.columns(2)

    with col1:
        business_name = st.text_input(
            "Business Name *",
            placeholder="e.g., Beehive Plumbing",
        )
        industry = st.text_input(
            "Industry / Vertical *",
            placeholder="e.g., Residential Plumbing, SaaS ERP, Functional Medicine",
        )
        website = st.text_input(
            "Website URL",
            placeholder="e.g., https://beehiveplumbing.com",
        )
        target_market = st.text_input(
            "Target Market",
            placeholder="e.g., Homeowners in Salt Lake City, Mid-market manufacturers",
        )

    with col2:
        description = st.text_area(
            "Business Description & USP",
            placeholder="What does the business do? What makes them different from competitors?",
            height=100,
        )
        services = st.text_area(
            "Products / Services",
            placeholder="List the main products or services offered",
            height=68,
        )
        competitors = st.text_area(
            "Known Competitors",
            placeholder="List any known competitors (one per line)",
            height=68,
        )

    additional = st.text_area(
        "Additional Context",
        placeholder="Any other relevant information — pricing tier, years in business, unique certifications, etc.",
        height=68,
    )

    submitted = st.form_submit_button(
        "Generate ICP",
        type="primary",
        use_container_width=True,
        disabled=not apis_ready,
    )

# --- Validation ---
if submitted:
    if not business_name or not industry:
        st.error("Business Name and Industry are required.")
    else:
        st.session_state.running = True
        st.session_state.report = None
        st.session_state.logs = []

# --- Pipeline Execution ---
if st.session_state.running:
    # Build the input text from form fields
    parts = [f"Business Name: {business_name}"]
    parts.append(f"Industry: {industry}")
    if website:
        parts.append(f"Website: {website}")
    if target_market:
        parts.append(f"Target Market: {target_market}")
    if description:
        parts.append(f"Description & USP: {description}")
    if services:
        parts.append(f"Products/Services: {services}")
    if competitors:
        parts.append(f"Competitors: {competitors}")
    if additional:
        parts.append(f"Additional Context: {additional}")

    business_input = "\n".join(parts)

    # Progress display
    progress_bar = st.progress(0, text="Starting ICP generation...")
    status_container = st.container()
    log_expander = st.expander("Live Research Log", expanded=True)
    log_placeholder = log_expander.empty()

    def update_status(msg: str):
        st.session_state.logs.append(msg)
        log_placeholder.markdown(
            "\n".join(f"- {log}" for log in st.session_state.logs[-20:])
        )

    async def run_pipeline():
        llm = OpenRouterClient()
        dfs = DataForSEOClient()

        try:
            # Phase 1: Business Analysis
            progress_bar.progress(5, text="Phase 1/4: Analyzing business...")
            update_status("Analyzing business profile and generating research plan...")

            profile, plan = await analyze_business(llm, business_input)
            update_status(
                f"Business analyzed: {profile.name} ({profile.industry} / {profile.vertical})"
            )
            total_queries = sum(
                len(getattr(plan, f)) for f in plan.__dataclass_fields__
            )
            update_status(f"Research plan generated: {total_queries} search queries")
            progress_bar.progress(15, text="Phase 2/4: Researching...")

            # Phase 2: Parallel Research
            update_status("Launching research agents...")
            findings = await run_research(llm, dfs, profile, plan, update_status)
            progress_bar.progress(65, text="Phase 3/4: Synthesizing research...")

            # Phase 3: Synthesis
            update_status("Synthesizing research findings...")
            synthesis = await synthesize_research(llm, profile, findings, update_status)
            progress_bar.progress(80, text="Phase 4/4: Generating ICP report...")

            # Phase 4: Report Generation
            update_status("Generating deep psychographic profiles...")
            report = await generate_icp_report(llm, synthesis, update_status)
            report = clean_markdown(report)

            progress_bar.progress(100, text="Complete!")
            update_status(
                f"Done! Tokens used: {llm.total_tokens_used:,} | "
                f"DataForSEO calls: {dfs.total_api_calls}"
            )

            return report, synthesis

        finally:
            await llm.close()
            await dfs.close()

    # Run the async pipeline (ensure_future wraps in a Task, required by aiohttp timeouts)
    try:
        loop = asyncio.get_event_loop()
        report, synthesis = loop.run_until_complete(
            asyncio.ensure_future(run_pipeline())
        )
        st.session_state.report = report
        st.session_state.synthesis = synthesis
        st.session_state.running = False
    except Exception as e:
        progress_bar.progress(0, text="Error occurred")
        st.error(f"Pipeline error: {str(e)}")
        logger.exception("Pipeline failed")
        st.session_state.running = False

# --- Results Display ---
if st.session_state.report:
    st.divider()
    st.header("ICP Report")

    synthesis = st.session_state.get("synthesis")
    segments = synthesis.segments if synthesis else []

    if segments:
        tab_names = [seg.name for seg in segments] + ["Full Report"]
        tabs = st.tabs(tab_names)

        # Split report into segments for tabbed view
        report_text = st.session_state.report
        segment_sections = report_text.split("---\n\n# Segment ")

        for i, seg in enumerate(segments):
            with tabs[i]:
                if i + 1 < len(segment_sections):
                    section = segment_sections[i + 1]
                    # Remove the "N — Detailed Profile" header line
                    lines = section.split("\n", 2)
                    if len(lines) > 2:
                        st.markdown(lines[2])
                    else:
                        st.markdown(section)
                else:
                    st.info(f"Profile for {seg.name} — see Full Report tab")

        # Full report tab
        with tabs[-1]:
            st.markdown(report_text)

    else:
        st.markdown(st.session_state.report)

    # Download button
    filename = format_report_filename(
        business_name or "Unknown",
        date.today().isoformat(),
    )
    st.download_button(
        label="Download ICP Report (Markdown)",
        data=st.session_state.report,
        file_name=filename,
        mime="text/markdown",
        type="primary",
    )
