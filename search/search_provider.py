from search.search_results import SearchResult


class SearchProvider:
    """
    搜索服务的统一接口。
    后续可以接入不同的搜索服务。
    """

    def search(self, query, limit=10):
        raise NotImplementedError("搜索服务尚未实现")


class MockSearchProvider(SearchProvider):
    """
    本地模拟搜索服务。
    暂时不连接任何外部 API。
    """

    def search(self, query, limit=10):
        results = [
            SearchResult(
                title="Example Automation GmbH",
                url="https://example.com",
                description=f"模拟搜索结果：{query}",
                source="mock"
            )
        ]

        return results[:limit]