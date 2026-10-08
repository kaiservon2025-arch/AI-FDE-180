from urllib.parse import urlparse


class SearchResultCleaner:
    """
    对搜索结果进行基础清洗。

    第一版只做确定性的规则：
    1. URL 去重
    2. 排除 Wikipedia
    3. 排除明显新闻/博客/文章页面
    4. 排除明显排行榜/聚合页面
    5. 对无法确定的结果保持保留
    """

    EXCLUDED_DOMAINS = {
        "wikipedia.org",
        "www.wikipedia.org",
        "de.wikipedia.org",
        "en.wikipedia.org",
    }

    EXCLUDED_PATH_KEYWORDS = {
        "/news/",
        "/blog/",
        "/article/",
        "/articles/",
    }

    EXCLUDED_TITLE_KEYWORDS = {
        "top 10",
        "top 15",
        "top 20",
        "top 50",
        "top 100",
        "ranking",
        "rankings",
        "排行榜",
    }

    def clean(self, results):
        cleaned_results = []
        seen_urls = set()
        seen_domains = set()

        for result in results:
            url = result.get("url", "").strip()
            title = result.get("title", "").strip()

            if not url:
                continue

            normalized_url = self._normalize_url(url)
            domain = urlparse(url).netloc.lower()

            if normalized_url in seen_urls:
                continue

            if self._is_excluded(result):
                continue

            if domain in seen_domains:
                continue

            seen_urls.add(normalized_url)
            seen_domains.add(domain)
            cleaned_results.append(result)

        return cleaned_results

    def _normalize_url(self, url):
        parsed = urlparse(url)

        return (
            f"{parsed.scheme.lower()}://"
            f"{parsed.netloc.lower()}"
            f"{parsed.path.rstrip('/')}"
        )

    def _is_excluded(self, result):
        url = result.get("url", "").strip().lower()
        title = result.get("title", "").strip().lower()

        parsed = urlparse(url)
        domain = parsed.netloc

        if domain in self.EXCLUDED_DOMAINS:
            return True

        for keyword in self.EXCLUDED_PATH_KEYWORDS:
            if keyword in parsed.path:
                return True

        for keyword in self.EXCLUDED_TITLE_KEYWORDS:
            if keyword in title:
                return True

        return False
