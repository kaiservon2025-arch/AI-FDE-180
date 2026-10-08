import requests

from search.search_results import SearchResult
from search.search_provider import SearchProvider


class SearXNGSearchProvider(SearchProvider):
    """
    使用本地 SearXNG 提供真实互联网搜索。
    """

    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url.rstrip("/")

    def search(self, query, limit=10):
        response = requests.get(
            f"{self.base_url}/search",
            params={
                "q": query,
                "format": "json"
            },
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get("results", [])[:limit]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    description=item.get("content", ""),
                    source=item.get("engine", "searxng")
                )
            )

        return results
