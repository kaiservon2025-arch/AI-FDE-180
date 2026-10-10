from urllib.parse import urlparse


class SearchResultCleaner:
    """
    对搜索结果进行基础清洗。

    第一版只做确定性的规则：

    1. URL 去重
    2. 排除 Wikipedia
    3. 排除明显新闻/博客/文章页面
    4. 排除明显排行榜/聚合页面
    5. 排除 PDF / Office / 压缩包等文档文件
    6. 对无法确定的结果保持保留
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

    EXCLUDED_FILE_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".zip",
        ".rar",
        ".7z",
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

            # URL 去重
            if normalized_url in seen_urls:
                continue

            # 排除不需要的搜索结果
            if self._is_excluded(result):
                continue

            # 同一企业域名只保留一个搜索结果
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
        domain = parsed.netloc.lower()
        path = parsed.path.lower()

        # ==============================
        # 1. 排除 Wikipedia
        # ==============================

        if domain in self.EXCLUDED_DOMAINS:
            return True

        # ==============================
        # 2. 排除新闻 / 博客 / 文章页面
        # ==============================

        for keyword in self.EXCLUDED_PATH_KEYWORDS:
            if keyword in path:
                return True

        # ==============================
        # 3. 排除排行榜 / 聚合页面
        # ==============================

        for keyword in self.EXCLUDED_TITLE_KEYWORDS:
            if keyword in title:
                return True

        # ==============================
        # 4. 排除 PDF / Office / 压缩包
        #
        # 例如：
        #
        # https://example.com/catalog.pdf
        #
        # 这种页面不是企业官网，
        # 不应该进入企业官网采集流程。
        # ==============================

        for extension in self.EXCLUDED_FILE_EXTENSIONS:
            if path.endswith(extension):
                return True

        # ==============================
        # 5. 排除明显的文档路径
        # ==============================

        document_path_keywords = {
            "/fileadmin/",
            "/documents/",
            "/document/",
            "/downloads/",
            "/download/",
            "/assets/documents/",
        }

        for keyword in document_path_keywords:
            if keyword in path:
                return True

        return False
