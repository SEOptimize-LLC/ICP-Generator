"""Competitor Review Miner — mines competitor reviews for sentiment patterns."""

from agents.researchers.base_researcher import BaseResearcher


class CompetitorReviewer(BaseResearcher):
    dimension = "competitor_review"

    def get_queries(self, query_list: list[str]) -> list[str]:
        return query_list
