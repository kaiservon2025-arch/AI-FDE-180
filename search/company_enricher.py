import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from search.company_contact_extractor import CompanyContactExtractor
from search.company_record import CompanyRecord


class CompanyEnricher:
    """
    企业信息采集器。

    第一阶段目标：

    1. 访问企业官网首页
    2. 提取首页联系方式
    3. 发现 Contact / Impressum / Careers / News 页面
    4. 访问 Contact 页面补充联系方式
    5. 生成 CompanyRecord

    不使用 AI 判断客户价值。
    """

    PAGE_KEYWORDS = {
        "contact": [
            "contact",
            "contact-us",
            "kontakt",
            "impressum",
            "contact-us",
            "get-in-touch",
        ],
        "jobs": [
            "career",
            "careers",
            "jobs",
            "karriere",
            "stellenangebote",
            "vacancies",
            "employment",
        ],
        "news": [
            "news",
            "newsroom",
            "press-release",
            "press-releases",
            "presse",
            "pressemitteilungen",
            "media",
        ]
    }

    def __init__(self, timeout=20):
        self.timeout = timeout
        self.contact_extractor = CompanyContactExtractor()

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/154.0 Safari/537.36"
            )
        }

    # ======================================================
    # HTTP
    # ======================================================

    def fetch_homepage(self, url):
        response = requests.get(
            url,
            timeout=self.timeout,
            headers=self.headers,
            allow_redirects=True
        )

        response.raise_for_status()

        return response.text

    # ======================================================
    # 首页链接发现
    # ======================================================

    def discover_links(self, base_url, html):
        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        links = []

        seen_urls = set()

        for tag in soup.find_all(
            "a",
            href=True
        ):

            href = tag.get(
                "href",
                ""
            ).strip()

            if not href:
                continue

            # 排除 javascript / mailto / tel
            if href.lower().startswith(
                (
                    "javascript:",
                    "mailto:",
                    "tel:",
                    "#"
                )
            ):
                continue

            absolute_url = urljoin(
                base_url,
                href
            )

            if not self._is_http_url(
                absolute_url
            ):
                continue

            if not self._is_same_domain(
                base_url,
                absolute_url
            ):
                continue

            normalized_url = (
                self._normalize_url(
                    absolute_url
                )
            )

            if normalized_url in seen_urls:
                continue

            seen_urls.add(
                normalized_url
            )

            links.append(
                {
                    "text": tag.get_text(
                        " ",
                        strip=True
                    ),
                    "url": absolute_url
                }
            )

        return links

    # ======================================================
    # 页面分类
    # ======================================================

    def classify_links(self, links):

        classified = {
            "contact_page": "",
            "jobs_page": "",
            "news_page": ""
        }

        for link in links:

            text = link.get(
                "text",
                ""
            ).strip().lower()

            url = link.get(
                "url",
                ""
            ).strip().lower()

            parsed_url = urlparse(url)

            path_parts = [
                part
                for part in (
                    parsed_url.path
                    .strip("/")
                    .split("/")
                )
                if part
            ]

            # 排除首页和语言首页
            if len(path_parts) == 0:
                continue

            if (
                len(path_parts) == 1
                and len(path_parts[0]) <= 5
            ):
                continue

            # Contact
            if not classified[
                "contact_page"
            ]:

                if self._matches_page(
                    text,
                    url,
                    self.PAGE_KEYWORDS[
                        "contact"
                    ]
                ):
                    classified[
                        "contact_page"
                    ] = link["url"]

                    continue

            # Jobs
            if not classified[
                "jobs_page"
            ]:

                if self._matches_page(
                    text,
                    url,
                    self.PAGE_KEYWORDS[
                        "jobs"
                    ]
                ):
                    classified[
                        "jobs_page"
                    ] = link["url"]

                    continue

            # News
            if not classified[
                "news_page"
            ]:

                if self._matches_page(
                    text,
                    url,
                    self.PAGE_KEYWORDS[
                        "news"
                    ]
                ):
                    classified[
                        "news_page"
                    ] = link["url"]

                    continue

        return classified

    # ======================================================
    # 页面关键词匹配
    # ======================================================

    def _matches_page(
        self,
        text,
        url,
        keywords
    ):

        parsed = urlparse(url)

        path = (
            parsed.path
            .lower()
            .strip()
        )

        if path in (
            "",
            "/"
        ):
            return False

        url_parts = self._split_url(
            url
        )

        text_parts = self._split_text(
            text
        )

        # URL 优先
        for keyword in keywords:

            keyword = keyword.lower()

            if keyword in url_parts:
                return True

        # 链接文字
        for keyword in keywords:

            keyword = keyword.lower()

            if keyword in text_parts:
                return True

        return False

    # ======================================================
    # 文本切分
    # ======================================================

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

        normalized = (
            text.lower()
        )

        for separator in separators:

            normalized = (
                normalized.replace(
                    separator,
                    " "
                )
            )

        return set(
            normalized.split()
        )

    # ======================================================
    # URL 切分
    # ======================================================

    def _split_url(self, url):

        parsed = urlparse(url)

        path = (
            parsed.path
            .lower()
        )

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

        return set(
            path.split()
        )

    # ======================================================
    # 域名判断
    # ======================================================

    def _is_same_domain(
        self,
        base_url,
        target_url
    ):

        base_domain = (
            urlparse(
                base_url
            ).netloc
            .lower()
            .split(":")[0]
        )

        target_domain = (
            urlparse(
                target_url
            ).netloc
            .lower()
            .split(":")[0]
        )

        if base_domain.startswith(
            "www."
        ):
            base_domain = (
                base_domain[4:]
            )

        if target_domain.startswith(
            "www."
        ):
            target_domain = (
                target_domain[4:]
            )

        return (
            base_domain
            == target_domain
        )

    # ======================================================
    # URL 判断
    # ======================================================

    def _is_http_url(self, url):

        parsed = urlparse(url)

        return parsed.scheme in (
            "http",
            "https"
        )

    def _normalize_url(self, url):

        parsed = urlparse(url)

        scheme = (
            parsed.scheme
            .lower()
        )

        domain = (
            parsed.netloc
            .lower()
            .split(":")[0]
        )

        if domain.startswith(
            "www."
        ):
            domain = domain[4:]

        path = (
            parsed.path
            .rstrip("/")
        )

        return (
            f"{scheme}://"
            f"{domain}"
            f"{path}"
        )

    # ======================================================
    # 合并联系方式
    # ======================================================

    def _merge_contact_data(
        self,
        current,
        new_data
    ):

        fields = [
            "email",
            "phone",
            "address",
            "contact"
        ]

        for field in fields:

            current_value = (
                current.get(
                    field,
                    ""
                )
            )

            new_value = (
                new_data.get(
                    field,
                    ""
                )
            )

            if (
                not current_value
                and new_value
            ):
                current[field] = (
                    new_value
                )

        return current

    # ======================================================
    # 企业信息补全
    # ======================================================

    def enrich(
        self,
        company_name,
        url,
        source=""
    ):
        """
        从企业官网生成企业记录。

        流程：

        官网首页
            ↓
        首页联系方式
            ↓
        首页链接发现
            ↓
        Contact 页面
            ↓
        补充联系方式
            ↓
        CompanyRecord
        """

        homepage_html = (
            self.fetch_homepage(
                url
            )
        )

        # --------------------------------------------------
        # 1. 先从首页提取联系方式
        # --------------------------------------------------

        contact_data = {
            "email": "",
            "phone": "",
            "address": "",
            "contact": ""
        }

        try:

            homepage_contact = (
                self.contact_extractor.extract(
                    homepage_html
                )
            )

            contact_data = (
                self._merge_contact_data(
                    contact_data,
                    homepage_contact
                )
            )

        except Exception:
            pass

        # --------------------------------------------------
        # 2. 发现首页链接
        # --------------------------------------------------

        links = self.discover_links(
            url,
            homepage_html
        )

        # --------------------------------------------------
        # 3. 分类页面
        # --------------------------------------------------

        pages = self.classify_links(
            links
        )

        # --------------------------------------------------
        # 4. 访问 Contact 页面
        # --------------------------------------------------

        contact_page = (
            pages["contact_page"]
        )

        if contact_page:

            try:

                contact_html = (
                    self.fetch_homepage(
                        contact_page
                    )
                )

                contact_page_data = (
                    self.contact_extractor.extract(
                        contact_html
                    )
                )

                contact_data = (
                    self._merge_contact_data(
                        contact_data,
                        contact_page_data
                    )
                )

            except requests.RequestException:
                pass

            except Exception:
                pass

        # --------------------------------------------------
        # 5. 生成 CRM 企业记录
        # --------------------------------------------------

        return CompanyRecord(
            company_name=company_name,

            contact=contact_data[
                "contact"
            ],

            phone=contact_data[
                "phone"
            ],

            email=contact_data[
                "email"
            ],

            address=contact_data[
                "address"
            ],

            contact_page=contact_page,

            jobs_page=pages[
                "jobs_page"
            ],

            news=pages[
                "news_page"
            ],

            source=source
        )