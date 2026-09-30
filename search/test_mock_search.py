from search.search_provider import MockSearchProvider


provider = MockSearchProvider()

results = provider.search(
    "industrial automation Germany",
    limit=5
)

print("========== 模拟搜索 ==========")

for result in results:
    result.show()