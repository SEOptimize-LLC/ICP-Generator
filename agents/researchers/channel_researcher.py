"""Channel & Communication Researcher — finds how audiences discover and evaluate solutions."""

from agents.researchers.base_researcher import BaseResearcher


class ChannelResearcher(BaseResearcher):
    dimension = "channel_preference"

    def get_queries(self, query_list: list[str]) -> list[str]:
        return query_list
