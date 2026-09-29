import re
import pandas as pd


def normalize_keywords(keywords):
    """
    将用户输入的关键词转换成干净的关键词列表。
    支持：
    EHR, HRIS, HR系统
    EHR、HRIS、HR系统
    EHR\nHRIS\nHR系统
    """

    if not keywords:
        return []

    if isinstance(keywords, str):
        keywords = re.split(r"[,，、;\n\r]+", keywords)

    result = []

    for keyword in keywords:
        keyword = str(keyword).strip()

        if keyword and keyword not in result:
            result.append(keyword)

    return result


def split_into_paragraphs(text):
    """
    将网页正文拆分成段落。

    优先按照空行、网页常见换行进行拆分。
    如果网页没有明显段落，则进一步按照句号、问号、感叹号等
    中文/英文标点进行较大粒度切分。
    """

    if not text:
        return []

    text = str(text)

    # 统一换行
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # 去除连续空格，但保留换行
    text = re.sub(r"[ \t]+", " ", text)

    # 按空行或者明显换行拆分
    raw_paragraphs = re.split(r"\n\s*\n+|\n+", text)

    paragraphs = []

    for paragraph in raw_paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # 去掉过短的网页碎片
        if len(paragraph) < 5:
            continue

        paragraphs.append(paragraph)

    # 如果网页没有明显段落，尝试按照句号等进行切分
    if len(paragraphs) <= 1 and paragraphs:
        text = paragraphs[0]

        sentence_parts = re.split(
            r"(?<=[。！？；.!?;])\s*",
            text
        )

        sentence_parts = [
            part.strip()
            for part in sentence_parts
            if part.strip()
        ]

        # 如果句子数量合理，则使用句子作为段落
        if len(sentence_parts) > 1:
            paragraphs = sentence_parts

    return paragraphs


def find_keyword_matches(text, keywords):
    """
    在网页正文中寻找关键词。

    返回每个关键词所在的完整段落。
    """

    if not text:
        return []

    keywords = normalize_keywords(keywords)

    if not keywords:
        return []

    paragraphs = split_into_paragraphs(text)

    matches = []

    for paragraph in paragraphs:

        for keyword in keywords:

            if not keyword:
                continue

            # 中文不需要忽略大小写，但英文关键词需要
            pattern = re.escape(keyword)

            if re.search(pattern, paragraph, re.IGNORECASE):

                matches.append({
                    "需求关键词": keyword,
                    "需求原文": paragraph
                })

    return matches


def extract_demand_evidence(
    text,
    keywords,
    title="",
    source_url="",
    information_date=""
):
    """
    从单个网页中提取需求关键词及完整原文。

    参数：
    text              网页正文
    keywords          用户设置的需求关键词
    title             网页标题
    source_url        来源网址
    information_date  信息日期
    """

    matches = find_keyword_matches(
        text=text,
        keywords=keywords
    )

    records = []

    scrape_time = pd.Timestamp.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    for match in matches:

        records.append({
            "需求关键词": match["需求关键词"],
            "需求原文": match["需求原文"],
            "网页标题": title,
            "来源网址": source_url,
            "信息日期": information_date,
            "抓取时间": scrape_time
        })

    return records


def extract_demand_from_pages(
    pages,
    keywords
):
    """
    批量处理网页。

    pages 可以是：

    1. list[dict]

    或者：

    2. pandas.DataFrame

    支持字段：

    网页标题 / title
    网页正文 / text
    来源网址 / source_url / url
    信息日期 / information_date / published_date
    """

    keywords = normalize_keywords(keywords)

    if not keywords:
        print("没有设置需求关键词。")
        return pd.DataFrame()

    if pages is None:
        return pd.DataFrame()

    if isinstance(pages, pd.DataFrame):
        page_records = pages.to_dict("records")
    elif isinstance(pages, list):
        page_records = pages
    else:
        raise TypeError(
            "pages必须是pandas DataFrame或者list。"
        )

    all_records = []

    print()
    print("================================")
    print("需求关键词证据提取")
    print("================================")
    print()

    print("当前需求关键词：")
    print("、".join(keywords))
    print()

    for index, page in enumerate(page_records, start=1):

        if not isinstance(page, dict):
            continue

        text = (
            page.get("网页正文")
            or page.get("text")
            or page.get("content")
            or ""
        )

        title = (
            page.get("网页标题")
            or page.get("title")
            or ""
        )

        source_url = (
            page.get("来源网址")
            or page.get("source_url")
            or page.get("url")
            or ""
        )

        information_date = (
            page.get("信息日期")
            or page.get("information_date")
            or page.get("published_date")
            or ""
        )

        if not text:
            continue

        records = extract_demand_evidence(
            text=text,
            keywords=keywords,
            title=title,
            source_url=source_url,
            information_date=information_date
        )

        all_records.extend(records)

        if records:
            print(
                f"[{index}/{len(page_records)}] "
                f"发现 {len(records)} 条需求证据"
            )

    if not all_records:
        print("没有找到匹配的需求关键词。")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # 同一个网页、同一个关键词、同一段原文去重
    df = df.drop_duplicates(
        subset=[
            "需求关键词",
            "需求原文",
            "来源网址"
        ]
    ).reset_index(drop=True)

    print()
    print(f"需求证据总数：{len(df)}")

    return df


def extract_demand_from_dataframe(
    df,
    keywords
):
    """
    方便直接处理已有DataFrame。

    自动识别：

    网页正文
    网页摘要
    来源网址
    网页标题
    信息日期
    """

    if df is None or df.empty:
        return pd.DataFrame()

    pages = []

    for _, row in df.iterrows():

        pages.append({
            "网页正文": (
                row.get("网页正文", "")
                or row.get("网页摘要", "")
            ),
            "网页标题": row.get(
                "网页标题",
                row.get("搜索标题", "")
            ),
            "来源网址": row.get(
                "来源网址",
                row.get("url", "")
            ),
            "信息日期": row.get(
                "信息日期",
                ""
            )
        })

    return extract_demand_from_pages(
        pages=pages,
        keywords=keywords
    )


if __name__ == "__main__":

    test_text = """
公司简介

广东某某电子科技有限公司成立于2015年，主要从事精密电子制造。

因公司业务快速发展，现招聘EHR经理1名，负责集团人力资源信息化系统建设、维护及优化。

岗位要求：
1. 熟悉HRIS系统。
2. 有人力资源数字化项目经验。
3. 负责HR系统日常管理。

联系电话：0769-12345678
"""

    test_keywords = [
        "EHR",
        "HRIS",
        "HR系统",
        "数字化HR"
    ]

    result = extract_demand_evidence(
        text=test_text,
        keywords=test_keywords,
        title="某电子公司招聘EHR经理",
        source_url="https://example.com",
        information_date="2026-09-29"
    )

    print()
    print("测试结果")
    print("================================")

    for item in result:
        print()
        print("关键词：", item["需求关键词"])
        print("原文：", item["需求原文"])
        print("来源：", item["来源网址"])