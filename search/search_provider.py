from search.search_results import SearchResult


class SearchProvider:
    """
    搜索服务统一接口
    """

    def search(
        self,
        query,
        limit=10
    ):
        raise NotImplementedError(
            "搜索服务尚未实现"
        )


class MockSearchProvider(SearchProvider):
    """
    本地模拟搜索服务
    """

    def search(
        self,
        query,
        limit=10
    ):

        results = [
            SearchResult(
                title="Example Automation GmbH",
                url="https://example.com",
                description=f"模拟搜索结果：{query}",
                source="mock"
            )
        ]

        return results[:limit]