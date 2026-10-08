import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class CompanyEnricher:
    """
    企业信息采集器。

    第一阶段：
    1. 访问企业首页
    2. 获取 HTML
    3. 提取页面链接
    4. 识别 Contact / Impressum / Careers / News 等相关页面
    """

    PAGE_KEYWORDS = {
        "contact": [
            "contact",
            "contact-us",
            "kontakt",
            "impressum"
        ],
        "jobs": [
            "career",
            "careers",
            "jobs",
            "karriere",
            "stellenangebote"
        ],
        "news": [
            "news",
            "newsroom",
            "press-release",
            "press-releases",
            "presse",
            "pressemitteilungen"
        ]
    }

    def __init__(self, timeout=20):
        self.timeout = timeout

    def fetch_homepage(self, url):
        response = requests.get(
            url,
            timeout=self.timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/154.0 Safari/537.36"
                )
            }
        )

        response.raise_for_status()

        return response.text

    def discover_links(self, base_url, html):
        soup = BeautifulSoup(html, "html.parser")

        links = []

        for tag in soup.find_all("a", href=True):
            href = tag.get("href", "").strip()

            if not href:
                continue

            absolute_url = urljoin(base_url, href)

            if self._is_same_domain(base_url, absolute_url):
                links.append({
                    "text": tag.get_text(" ", strip=True),
                    "url": absolute_url
                })

        return links

    def classify_links(self, links):
        classified = {
            "contact_page": "",
            "jobs_page": "",
            "news_page": ""
        }

        for link in links:
            text = link["text"].strip().lower()
            url = link["url"].strip().lower()

            if not classified["contact_page"]:
                if self._matches_page(
                    text,
                    url,
                    self.PAGE_KEYWORDS["contact"]
                ):
                    classified["contact_page"] = link["url"]
                    continue

            if not classified["jobs_page"]:
                if self._matches_page(
                    text,
                    url,
                    self.PAGE_KEYWORDS["jobs"]
                ):
                    classified["jobs_page"] = link["url"]
                    continue

            if not classified["news_page"]:
                if self._matches_page(
                    text,
                    url,
                    self.PAGE_KEYWORDS["news"]
                ):
                    classified["news_page"] = link["url"]
                    continue

        return classified

    def _matches_page(self, text, url, keywords):
        """
        判断链接是否属于指定页面类型。

        规则：
        1. 网站首页不能仅因为导航文字匹配而被识别成目标页面。
        2. URL 路径优先判断。
        3. URL 没有明显关键词时，再参考链接文字。
        4. 使用完整路径片段匹配，避免 press -> pressure 的误判。
        """

        parsed = urlparse(url)

        path = parsed.path.lower().strip()

        # 网站首页不能因为导航文字而被误判
        if path in ("", "/"):
            return False

        url_parts = self._split_url(url)
        text_parts = self._split_text(text)

        # 第一优先级：URL 路径
        for keyword in keywords:
            keyword = keyword.lower()

            if keyword in url_parts:
                return True

        # 第二优先级：链接文字
        for keyword in keywords:
            keyword = keyword.lower()

            if keyword in text_parts:
                return True

        return False

    def _split_text(self, text):
        separators = [
            " ",
            "-",
            "_",
            "/",
            "|",
            ">",
            ":"
        ]

        normalized = text.lower()

        for separator in separators:
            normalized = normalized.replace(
                separator,
                " "
            )

        return set(normalized.split())

    def _split_url(self, url):
        parsed = urlparse(url)

        path = parsed.path.lower()

        separators = [
            "/",
            "-",
            "_",
            "."
        ]

        for separator in separators:
            path = path.replace(
                separator,
                " "
            )

        return set(path.split())

    def _is_same_domain(self, base_url, target_url):
        base_domain = urlparse(base_url).netloc.lower()
        target_domain = urlparse(target_url).netloc.lower()

        return base_domain == target_domain