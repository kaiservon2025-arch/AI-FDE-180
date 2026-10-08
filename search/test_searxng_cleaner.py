from search.search_config import SearchConfig
from search.keyword_search import KeywordSearch
from search.search_engine import SearchEngine
from search.searxng_provider import SearXNGSearchProvider
from search.search_cache import SearchCache
from search.search_result_cleaner import SearchResultCleaner


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

print("\n========== 搜索真实结果 ==========")

results = search.search(limit=10)

print(f"原始结果数量：{len(results)}")

cleaner = SearchResultCleaner()

cleaned_results = cleaner.clean(results)

print(f"清洗后数量：{len(cleaned_results)}")

print("\n========== 清洗后结果 ==========")

for result in cleaned_results:
    print(f"标题：{result['title']}")
    print(f"网址：{result['url']}")
    print(f"描述：{result['description']}")
    print(f"来源：{result['source']}")
    print("------------------------------")
