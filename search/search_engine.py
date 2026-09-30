from search.search_cache import SearchCache
from search.search_provider import SearchProvider


class SearchEngine:
    def __init__(
        self,
        provider: SearchProvider,
        cache: SearchCache
    ):
        self.provider = provider
        self.cache = cache

    def search(self, query, limit=10):
        # 先检查缓存
        cached_results = self.cache.get(query)

        if cached_results is not None:
            return cached_results

        # 没有缓存，再调用搜索服务
        results = self.provider.search(
            query,
            limit=limit
        )

        # 转换成字典，方便缓存保存
        results_data = [
            result.to_dict()
            for result in results
        ]

        # 保存缓存
        self.cache.save(
            query,
            results_data
        )

        return results_data