from search.search_engine import SearchEngine
from search.search_provider import MockSearchProvider
from search.search_cache import SearchCache


provider = MockSearchProvider()
cache = SearchCache()

engine = SearchEngine(
    provider=provider,
    cache=cache
)

query = "industrial automation Germany"

print("========== 第一次搜索 ==========")

results = engine.search(
    query,
    limit=5
)

print("搜索结果：")
print(results)


print("\n========== 第二次搜索 ==========")

results = engine.search(
    query,
    limit=5
)

print("搜索结果：")
print(results)