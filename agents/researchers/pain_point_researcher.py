"""Pain Point Researcher — finds complaints, frustrations, and problems."""

from agents.researchers.base_researcher import BaseResearcher


class PainPointResearcher(BaseResearcher):
    dimension = "pain_point"

    def get_queries(self, query_list: list[str]) -> list[str]:
        return query_list
