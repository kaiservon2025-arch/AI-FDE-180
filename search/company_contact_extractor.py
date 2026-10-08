import re

from bs4 import BeautifulSoup


class CompanyContactExtractor:
    """
    企业公开联系方式提取器。

    负责从真实网页中提取：
    - email
    - phone
    - address
    - contact

    不进行 AI 客户价值判断。
    """

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    PHONE_PATTERN = re.compile(
        r"(?<!\w)(?:\+|00)?[0-9][0-9\s()./-]{7,}[0-9](?!\w)"
    )

    def extract(self, html):
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        return {
            "email": self.extract_email(soup),
            "phone": self.extract_phone(soup),
            "address": self.extract_address(soup),
            "contact": self.extract_contact(soup)
        }

    def extract_email(self, soup):
        # 1. 优先读取 mailto
        for tag in soup.select('a[href^="mailto:"]'):
            email = (
                tag.get("href", "")
                .replace("mailto:", "")
                .split("?")[0]
                .strip()
            )

            if self._valid_email(email):
                return email

        # 2. 再检查正文
        text = soup.get_text(" ", strip=True)

        for email in self.EMAIL_PATTERN.findall(text):
            if self._valid_email(email):
                return email

        return ""

    def extract_phone(self, soup):
        # 1. 优先读取 tel
        for tag in soup.select('a[href^="tel:"]'):
            phone = (
                tag.get("href", "")
                .replace("tel:", "")
                .strip()
            )

            if self._valid_phone(phone):
                return phone

        # 2. 再检查正文
        text = soup.get_text(" ", strip=True)

        for phone in self.PHONE_PATTERN.findall(text):
            if self._valid_phone(phone):
                return self._clean_phone(phone)

        return ""

    def extract_address(self, soup):
        # 标准 HTML address
        for tag in soup.find_all("address"):
            text = tag.get_text(" ", strip=True)

            if len(text) >= 10:
                return text

        return ""

    def extract_contact(self, soup):
        """
        保守提取联系人。

        第一版不猜测姓名。
        只有页面明确出现联系人语义，
        且附近文本不像导航菜单时才返回。
        """

        labels = [
            "contact person",
            "contact-person",
            "ansprechpartner",
            "sales contact"
        ]

        for tag in soup.find_all(
            ["div", "p", "span", "strong", "label", "h2", "h3"]
        ):
            text = tag.get_text(" ", strip=True)

            if not text:
                continue

            lower_text = text.lower()

            if not any(
                label in lower_text
                for label in labels
            ):
                continue

            parent = tag.parent

            if not parent:
                continue

            parent_text = parent.get_text(
                " ",
                strip=True
            )

            if not (5 < len(parent_text) < 300):
                continue

            # 排除明显的导航/菜单内容
            navigation_keywords = [
                "company",
                "career",
                "press",
                "customer portal",
                "digital solutions",
                "industries",
                "sales",
                "service",
                "products",
                "overview"
            ]

            lower_parent = parent_text.lower()

            navigation_hits = sum(
                1
                for keyword in navigation_keywords
                if keyword in lower_parent
            )

            if navigation_hits >= 3:
                continue

            return parent_text

        return ""

    def _valid_email(self, email):
        if not email:
            return False

        lower = email.lower()

        for extension in [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif",
            ".svg"
        ]:
            if lower.endswith(extension):
                return False

        return bool(
            self.EMAIL_PATTERN.fullmatch(email)
        )

    def _valid_phone(self, phone):
        digits = re.sub(r"\D", "", phone)

        return 8 <= len(digits) <= 16

    def _clean_phone(self, phone):
        return re.sub(r"\s+", " ", phone).strip()
