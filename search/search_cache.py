import json
import hashlib
from pathlib import Path


class SearchCache:
    def __init__(self, cache_dir="search/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_file(self, query):
        query_hash = hashlib.md5(
            query.encode("utf-8")
        ).hexdigest()

        return self.cache_dir / f"{query_hash}.json"

    def save(self, query, results):
        cache_file = self._get_cache_file(query)

        data = {
            "query": query,
            "results": results
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        print(f"缓存已保存：{cache_file}")

    def get(self, query):
        cache_file = self._get_cache_file(query)

        if not cache_file.exists():
            print("没有找到缓存。")
            return None

        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"命中缓存：{cache_file}")

        return data["results"]