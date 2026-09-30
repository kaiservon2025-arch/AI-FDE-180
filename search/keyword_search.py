from search.search_config import SearchConfig


class KeywordSearch:
    def __init__(self, config: SearchConfig):
        self.config = config

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

    def show_search_query(self):
        query = self.build_query()

        print("========== 企业搜索 ==========")
        print(f"搜索关键词：{query}")
        print("==============================")


if __name__ == "__main__":
    config = SearchConfig(
        keyword="industrial automation",
        country="Germany",
        industry="Industrial Equipment",
        city="Munich",
        company_size="50-500"
    )

    search = KeywordSearch(config)
    search.show_search_query()