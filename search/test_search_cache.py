from search.search_cache import SearchCache


cache = SearchCache()

query = "industrial automation Germany Munich"

results = [
    {
        "title": "Example Automation GmbH",
        "url": "https://example.com",
        "description": "Industrial automation company in Munich"
    }
]

print("========== 第一次搜索 ==========")

cached_results = cache.get(query)

if cached_results is None:
    print("没有缓存，模拟搜索结果...")
    cache.save(query, results)
else:
    print("直接使用缓存结果：")
    print(cached_results)


print("\n========== 第二次搜索 ==========")

cached_results = cache.get(query)

if cached_results is not None:
    print("成功从缓存读取：")
    print(cached_results)