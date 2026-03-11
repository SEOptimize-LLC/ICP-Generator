"""Industry & Market Intelligence Researcher — finds published studies and data."""

from agents.researchers.base_researcher import BaseResearcher


class IndustryResearcher(BaseResearcher):
    dimension = "industry_research"

    def get_queries(self, query_list: list[str]) -> list[str]:
        return query_list
