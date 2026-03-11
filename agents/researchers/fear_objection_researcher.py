"""Fear & Objection Researcher — finds what stops people from buying."""

from agents.researchers.base_researcher import BaseResearcher


class FearObjectionResearcher(BaseResearcher):
    dimension = "fear_objection"

    def get_queries(self, query_list: list[str]) -> list[str]:
        return query_list
