
import hashlib
import json
import time
from pathlib import Path


class SearchCache:
    def __init__(self, cache_dir="search/cache", ttl_seconds=86400):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _get_cache_file(self, query, limit=None):
        # 不同搜索条数使用不同缓存文件
        cache_key = json.dumps(
            {"query": query, "limit": limit},
            ensure_ascii=False,
            sort_keys=True,
        )
        query_hash = hashlib.sha256(
            cache_key.encode("utf-8")
        ).hexdigest()
        return self.cache_dir / f"{query_hash}.json"

    def save(self, query, results, limit=None):
        cache_file = self._get_cache_file(query, limit)
        data = {
            "query": query,
            "limit": limit,
            "results": results,
            "saved_at": time.time(),
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"缓存已保存：{cache_file}")
    
    def get(self, query, limit=None):
        cache_file = self._get_cache_file(query, limit)

        if not cache_file.exists():
            print("没有找到缓存。")
            return None

        try:
            # 使用文件修改时间判断缓存是否过期
            age_seconds = time.time() - cache_file.stat().st_mtime

            if age_seconds >= self.ttl_seconds:
                print("缓存已过期，需要重新搜索。")
                return None

            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            results = data.get("results")

            if not isinstance(results, list):
                print("缓存数据格式异常，需要重新搜索。")
                return None

            print(f"命中缓存：{cache_file}")
            return results

        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            print(f"缓存读取失败，将重新搜索：{exc}")
            return None
