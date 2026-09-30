from search.search_provider import SearchProvider


provider = SearchProvider()

try:
    provider.search("industrial automation Germany")
except NotImplementedError as e:
    print("搜索接口测试成功：")
    print(e)