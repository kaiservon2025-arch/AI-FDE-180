import re
import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/153.0.0.0 Safari/537.36"
)


def clean_text(text):
    """
    清理网页正文中的多余空白。
    """

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def scrape_web_page(
    url,
    timeout=20
):
    """
    抓取公开网页正文。

    返回：
    {
        "url": "",
        "title": "",
        "text": "",
        "status_code": 200,
        "success": True,
        "error": ""
    }
    """

    if not url:
        return {
            "url": "",
            "title": "",
            "text": "",
            "status_code": 0,
            "success": False,
            "error": "URL为空"
        }

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True
        )

        status_code = response.status_code

        if status_code != 200:

            return {
                "url": url,
                "title": "",
                "text": "",
                "status_code": status_code,
                "success": False,
                "error": (
                    f"HTTP状态码：{status_code}"
                )
            }

        # 尝试正确识别网页编码
        response.encoding = (
            response.apparent_encoding
            or response.encoding
        )

        html = response.text

        if not html:

            return {
                "url": url,
                "title": "",
                "text": "",
                "status_code": status_code,
                "success": False,
                "error": "网页内容为空"
            }

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # 删除无关标签
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "svg"
            ]
        ):

            tag.decompose()

        # 网页标题
        title = ""

        if soup.title:

            title = clean_text(
                soup.title.get_text(
                    " ",
                    strip=True
                )
            )

        # 优先获取body正文
        if soup.body:

            text = soup.body.get_text(
                " ",
                strip=True
            )

        else:

            text = soup.get_text(
                " ",
                strip=True
            )

        text = clean_text(
            text
        )

        return {
            "url": url,
            "title": title,
            "text": text,
            "status_code": status_code,
            "success": True,
            "error": ""
        }

    except requests.exceptions.Timeout:

        return {
            "url": url,
            "title": "",
            "text": "",
            "status_code": 0,
            "success": False,
            "error": "网页访问超时"
        }

    except requests.exceptions.RequestException as e:

        return {
            "url": url,
            "title": "",
            "text": "",
            "status_code": 0,
            "success": False,
            "error": str(e)
        }

    except Exception as e:

        return {
            "url": url,
            "title": "",
            "text": "",
            "status_code": 0,
            "success": False,
            "error": str(e)
        }


def scrape_pages(
    pages_df,
    max_pages=None
):
    """
    批量抓取公开网页。

    pages_df必须包含：
    网址

    max_pages：
    测试时可以限制网页数量。
    """

    if pages_df is None:

        raise ValueError(
            "网页数据为空。"
        )

    if len(pages_df) == 0:

        return pages_df.copy()

    if "网址" not in pages_df.columns:

        raise ValueError(
            "数据中缺少“网址”字段。"
        )

    working_df = pages_df.copy()

    if max_pages is not None:

        working_df = working_df.head(
            max_pages
        )

    records = []

    total = len(
        working_df
    )

    print()
    print("================================")
    print("开始抓取公开网页正文")
    print("================================")
    print()

    for index, row in working_df.iterrows():

        url = str(
            row.get(
                "网址",
                ""
            )
        ).strip()

        print(
            f"[{index + 1}/{total}] "
            f"{url}"
        )

        page = scrape_web_page(
            url
        )

        record = row.to_dict()

        record["网页抓取成功"] = (
            page["success"]
        )

        record["网页HTTP状态"] = (
            page["status_code"]
        )

        record["网页标题"] = (
            page["title"]
        )

        record["网页正文"] = (
            page["text"]
        )

        record["抓取错误"] = (
            page["error"]
        )

        records.append(
            record
        )

        if page["success"]:

            print(
                "  → 抓取成功，正文字符数："
                + str(
                    len(
                        page["text"]
                    )
                )
            )

        else:

            print(
                "  → 抓取失败："
                + page["error"]
            )

    result_df = __import__(
        "pandas"
    ).DataFrame(
        records
    )

    success_count = (
        result_df["网页抓取成功"]
        .sum()
    )

    print()
    print("================================")
    print("网页抓取完成")
    print("================================")
    print()

    print(
        f"尝试抓取：{len(result_df)} 个网页"
    )

    print(
        f"成功：{success_count} 个"
    )

    print(
        f"失败：{len(result_df) - success_count} 个"
    )

    return result_df