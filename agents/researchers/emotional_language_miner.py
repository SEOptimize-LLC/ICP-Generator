"""Emotional Language Miner — captures verbatim emotional language patterns."""

from agents.researchers.base_researcher import BaseResearcher


class EmotionalLanguageMiner(BaseResearcher):
    dimension = "emotional_language"

    def get_queries(self, query_list: list[str]) -> list[str]:
        return query_list
