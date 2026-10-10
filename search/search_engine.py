
from search.search_cache import SearchCache
from search.search_provider import SearchProvider


class SearchEngine:
    def __init__(
        self,
        provider: SearchProvider,
        cache: SearchCache,
    ):
        self.provider = provider
        self.cache = cache

    def search(self, query, limit=10):
        # 搜索条数也参与缓存匹配
        cached_results = self.cache.get(query, limit=limit)

        if cached_results is not None:
            return cached_results

        # 缓存未命中或过期时，执行真实搜索
        results = self.provider.search(query, limit=limit)

        # 保持原有返回格式：字典列表
        results_data = [
            result.to_dict() for result in results
        ]

        self.cache.save(
            query,
            results_data,
            limit=limit,
        )

        return results_data
