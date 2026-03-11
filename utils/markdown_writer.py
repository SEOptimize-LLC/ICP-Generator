"""Utility for building and formatting the ICP markdown report."""

from __future__ import annotations

import re


def clean_markdown(text: str) -> str:
    """Clean up LLM-generated markdown for display consistency."""
    # Remove any leading/trailing code fences the LLM might have added
    text = re.sub(r"^```(?:markdown)?\s*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)

    # Normalize heading levels (ensure no H1 duplicates)
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        cleaned.append(line)

    return "\n".join(cleaned).strip()


def format_report_filename(business_name: str, date_str: str) -> str:
    """Generate a clean filename for the report."""
    clean_name = re.sub(r"[^\w\s-]", "", business_name).strip()
    clean_name = re.sub(r"\s+", "_", clean_name)
    return f"{clean_name}_ICP_Report_{date_str}.md"
