from search.search_config import SearchConfig
from search.search_engine import SearchEngine


class KeywordSearch:
    def __init__(
        self,
        config: SearchConfig,
        search_engine: SearchEngine
    ):
        self.config = config
        self.search_engine = search_engine

    def build_query(self):
        parts = []

        if self.config.keyword:
            parts.append(self.config.keyword)

        if self.config.industry:
            parts.append(self.config.industry)

        if self.config.country:
            parts.append(self.config.country)

        if self.config.city:
            parts.append(self.config.city)

        if self.config.company_size:
            parts.append(self.config.company_size)

        return " ".join(parts)

    def search(self, limit=10):
        query = self.build_query()

        return self.search_engine.search(
            query,
            limit=limit
        )

    def show_search_query(self):
        query = self.build_query()

        print("========== 企业搜索 ==========")
        print(f"搜索关键词：{query}")
        print("==============================")