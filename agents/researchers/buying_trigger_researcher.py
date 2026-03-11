"""Buying Trigger Researcher — finds what starts the buying process."""

from agents.researchers.base_researcher import BaseResearcher


class BuyingTriggerResearcher(BaseResearcher):
    dimension = "buying_trigger"

    def get_queries(self, query_list: list[str]) -> list[str]:
        return query_list
