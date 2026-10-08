from search.search_config import SearchConfig
from search.keyword_search import KeywordSearch
from search.search_engine import SearchEngine
from search.searxng_provider import SearXNGSearchProvider
from search.search_cache import SearchCache


config = SearchConfig(
    keyword="industrial automation",
    country="Germany",
    industry="Industrial Equipment",
    city="Munich",
    company_size="50-500"
)

provider = SearXNGSearchProvider()

cache = SearchCache()

engine = SearchEngine(
    provider=provider,
    cache=cache
)

search = KeywordSearch(
    config=config,
    search_engine=engine
)

search.show_search_query()

print("\n========== 开始真实搜索 ==========")

results = search.search(limit=5)

print("\n========== 真实搜索结果 ==========")

for result in results:
    print(f"企业：{result['title']}")
    print(f"网址：{result['url']}")
    print(f"描述：{result['description']}")
    print(f"来源：{result['source']}")
    print("------------------------------")
