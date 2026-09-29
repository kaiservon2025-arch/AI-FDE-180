import re
import pandas as pd


def normalize_keywords(keywords):
    """
    将关键词转换成列表并去重。
    支持：
    EHR,HRIS,HR系统
    EHR，HRIS、HR系统
    """

    if keywords is None:
        return []

    if isinstance(keywords, str):
        keywords = re.split(
            r"[,，、;\n\r]+",
            keywords
        )

    result = []
    seen = set()

    for keyword in keywords:

        keyword = str(keyword).strip()

        if not keyword:
            continue

        key = keyword.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(keyword)

    return result


def normalize_text(text):
    """
    标准化文本，方便关键词匹配。
    """

    if text is None:
        return ""

    text = str(text)

    text = text.replace(
        "\n",
        " "
    ).replace(
        "\r",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip().lower()


def normalize_company_name(company_name):
    """
    标准化企业名称，用于企业去重。
    """

    if not company_name:
        return ""

    name = str(
        company_name
    ).strip()

    name = re.sub(
        r"\s+",
        "",
        name
    )

    name = name.replace(
        "（",
        "("
    ).replace(
        "）",
        ")"
    )

    name = name.replace(
        "，",
        ""
    ).replace(
        ",",
        ""
    ).replace(
        "。",
        ""
    )

    return name.lower()


def row_text(row):
    """
    将一条搜索结果的重要字段合并成文本。
    用于关键词匹配。
    """

    fields = [
        "公司",
        "搜索标题",
        "网页摘要",
        "来源网址",
        "行业",
        "联系人",
        "职位",
        "需求关键词"
    ]

    values = []

    for field in fields:

        value = row.get(
            field,
            ""
        )

        if value:
            values.append(
                str(value)
            )

    return normalize_text(
        " ".join(values)
    )


def contains_keyword(
    text,
    keywords
):
    """
    判断文本是否包含任意关键词。
    """

    if not keywords:
        return False

    normalized_text = normalize_text(
        text
    )

    for keyword in keywords:

        keyword = normalize_text(
            keyword
        )

        if not keyword:
            continue

        if keyword in normalized_text:
            return True

    return False


def matched_keywords(
    text,
    keywords
):
    """
    返回文本中实际匹配到的关键词。
    """

    if not keywords:
        return []

    normalized_text = normalize_text(
        text
    )

    matches = []

    for keyword in keywords:

        normalized_keyword = normalize_text(
            keyword
        )

        if not normalized_keyword:
            continue

        if normalized_keyword in normalized_text:

            matches.append(
                keyword
            )

    return matches


def filter_by_location(
    row,
    province="",
    city=""
):
    """
    根据用户设置的省份和城市进行客观过滤。
    """

    if province:

        row_province = normalize_text(
            row.get(
                "省份",
                ""
            )
        )

        target_province = normalize_text(
            province
        )

        if (
            row_province
            and target_province
            not in row_province
        ):
            return False

    if city:

        row_city = normalize_text(
            row.get(
                "城市",
                ""
            )
        )

        target_city = normalize_text(
            city
        )

        if (
            row_city
            and target_city
            not in row_city
        ):
            return False

    return True


def filter_by_industry(
    row,
    industry=""
):
    """
    根据行业条件进行客观文本匹配。
    """

    if not industry:
        return True

    industry_keywords = normalize_keywords(
        industry
    )

    if not industry_keywords:
        return True

    text = row_text(
        row
    )

    return contains_keyword(
        text,
        industry_keywords
    )


def filter_by_search_keywords(
    row,
    search_keywords=None
):
    """
    根据企业搜索关键词进行客观匹配。

    例如：
    连接器
    精密制造
    电子制造
    """

    search_keywords = normalize_keywords(
        search_keywords
    )

    if not search_keywords:
        return True

    text = row_text(
        row
    )

    return contains_keyword(
        text,
        search_keywords
    )


def filter_by_demand_keywords(
    row,
    demand_keywords=None,
    require_demand_keyword=False
):
    """
    根据需求关键词进行客观匹配。

    例如：
    EHR
    HRIS
    HR系统
    人力资源系统
    数字化HR

    如果require_demand_keyword=True，
    则必须至少命中一个需求关键词。
    """

    demand_keywords = normalize_keywords(
        demand_keywords
    )

    if not demand_keywords:
        return True

    text = row_text(
        row
    )

    matches = matched_keywords(
        text,
        demand_keywords
    )

    if matches:

        return True

    if require_demand_keyword:
        return False

    return True


def apply_exclude_keywords(
    row,
    exclude_keywords=None
):
    """
    排除包含指定关键词的结果。
    """

    exclude_keywords = normalize_keywords(
        exclude_keywords
    )

    if not exclude_keywords:
        return True

    text = row_text(
        row
    )

    if contains_keyword(
        text,
        exclude_keywords
    ):
        return False

    return True


def filter_by_source_type(
    row,
    source_types=None
):
    """
    根据来源类型进行过滤。

    例如：
    招聘网站
    新闻
    微信公众号
    行业网站
    其他公开网页
    """

    source_types = normalize_keywords(
        source_types
    )

    if not source_types:
        return True

    source_type = str(
        row.get(
            "来源类型",
            ""
        )
    ).strip()

    if not source_type:
        return False

    return source_type in source_types


def add_filter_evidence(
    row,
    demand_keywords=None
):
    """
    为结果增加实际命中的需求关键词。
    """

    text = row_text(
        row
    )

    matches = matched_keywords(
        text,
        demand_keywords
    )

    row["命中需求关键词"] = "、".join(
        matches
    )

    return row


def deduplicate_companies(
    df
):
    """
    同一家企业只保留一条主记录。

    需求证据不会在这里删除，
    后续由 demand_keyword.py 单独保存。
    """

    if df is None:
        return pd.DataFrame()

    if df.empty:
        return df.copy()

    result = df.copy()

    result["_企业标准名称"] = result[
        "公司"
    ].apply(
        normalize_company_name
    )

    result = result[
        result["_企业标准名称"] != ""
    ]

    result = result.drop_duplicates(
        subset=[
            "_企业标准名称"
        ],
        keep="first"
    )

    result = result.drop(
        columns=[
            "_企业标准名称"
        ],
        errors="ignore"
    )

    return result.reset_index(
        drop=True
    )


def filter_target_companies(
    leads_df,
    province="",
    city="",
    industry="",
    search_keywords=None,
    exclude_keywords=None,
    demand_keywords=None,
    require_demand_keyword=False,
    source_types=None,
    deduplicate=True
):
    """
    根据用户设置的客观条件筛选企业。

    注意：

    本模块不再使用AI判断客户价值。

    只做：

    地区
    行业
    企业搜索关键词
    排除关键词
    需求关键词
    信息来源
    企业去重

    最终判断客户是否值得跟进，
    由用户自己决定。
    """

    if leads_df is None:
        raise ValueError(
            "搜索结果为空。"
        )

    if not isinstance(
        leads_df,
        pd.DataFrame
    ):
        leads_df = pd.DataFrame(
            leads_df
        )

    if leads_df.empty:
        return leads_df.copy()

    search_keywords = normalize_keywords(
        search_keywords
    )

    exclude_keywords = normalize_keywords(
        exclude_keywords
    )

    demand_keywords = normalize_keywords(
        demand_keywords
    )

    source_types = normalize_keywords(
        source_types
    )

    print()
    print("================================")
    print("开始按用户条件筛选企业")
    print("================================")
    print()

    print(
        f"原始搜索结果：{len(leads_df)} 条"
    )

    print(
        f"省份：{province}"
    )

    print(
        f"城市：{city}"
    )

    print(
        f"行业：{industry}"
    )

    print(
        f"企业搜索关键词：{search_keywords}"
    )

    print(
        f"排除关键词：{exclude_keywords}"
    )

    print(
        f"需求关键词：{demand_keywords}"
    )

    print(
        f"必须包含需求关键词：{require_demand_keyword}"
    )

    print(
        f"来源类型：{source_types}"
    )

    print()

    filtered_rows = []

    location_removed = 0
    industry_removed = 0
    search_keyword_removed = 0
    exclude_removed = 0
    demand_removed = 0
    source_removed = 0

    for index, row in leads_df.iterrows():

        row = row.copy()

        # 1. 地区
        if not filter_by_location(
            row,
            province=province,
            city=city
        ):
            location_removed += 1
            continue

        # 2. 行业
        if not filter_by_industry(
            row,
            industry=industry
        ):
            industry_removed += 1
            continue

        # 3. 企业搜索关键词
        if not filter_by_search_keywords(
            row,
            search_keywords=search_keywords
        ):
            search_keyword_removed += 1
            continue

        # 4. 排除关键词
        if not apply_exclude_keywords(
            row,
            exclude_keywords=exclude_keywords
        ):
            exclude_removed += 1
            continue

        # 5. 需求关键词
        if not filter_by_demand_keywords(
            row,
            demand_keywords=demand_keywords,
            require_demand_keyword=require_demand_keyword
        ):
            demand_removed += 1
            continue

        # 6. 来源类型
        if not filter_by_source_type(
            row,
            source_types=source_types
        ):
            source_removed += 1
            continue

        # 7. 保存实际命中的需求关键词
        row = add_filter_evidence(
            row,
            demand_keywords=demand_keywords
        )

        filtered_rows.append(
            row
        )

    result_df = pd.DataFrame(
        filtered_rows
    )

    print("筛选结果：")
    print()

    print(
        f"地区不符合：{location_removed}"
    )

    print(
        f"行业不符合：{industry_removed}"
    )

    print(
        f"企业关键词不符合：{search_keyword_removed}"
    )

    print(
        f"包含排除关键词：{exclude_removed}"
    )

    print(
        f"没有需求关键词：{demand_removed}"
    )

    print(
        f"来源类型不符合：{source_removed}"
    )

    print()

    if deduplicate:

        before_dedup = len(
            result_df
        )

        result_df = deduplicate_companies(
            result_df
        )

        after_dedup = len(
            result_df
        )

        print(
            f"企业去重：{before_dedup} → {after_dedup}"
        )

    print()

    print("================================")
    print("企业条件筛选完成")
    print("================================")
    print()

    print(
        f"原始搜索结果：{len(leads_df)} 条"
    )

    print(
        f"最终企业线索：{len(result_df)} 家"
    )

    return result_df


if __name__ == "__main__":

    sample_data = pd.DataFrame([
        {
            "公司": "广东XX精密制造有限公司",
            "国家": "中国",
            "省份": "广东",
            "城市": "东莞",
            "行业": "精密制造",
            "搜索标题": "广东XX精密制造有限公司招聘EHR经理",
            "网页摘要": "公司正在招聘EHR经理，负责HR系统建设和数字化HR项目。",
            "来源类型": "招聘网站",
            "来源网址": "https://example.com/1"
        },
        {
            "公司": "广东XX贸易有限公司",
            "国家": "中国",
            "省份": "广东",
            "城市": "东莞",
            "行业": "贸易",
            "搜索标题": "广东XX贸易有限公司招聘",
            "网页摘要": "电子产品贸易业务。",
            "来源类型": "招聘网站",
            "来源网址": "https://example.com/2"
        },
        {
            "公司": "广东YY电子有限公司",
            "国家": "中国",
            "省份": "广东",
            "城市": "深圳",
            "行业": "电子制造",
            "搜索标题": "广东YY电子有限公司",
            "网页摘要": "电子制造企业。",
            "来源类型": "新闻",
            "来源网址": "https://example.com/3"
        }
    ])

    result = filter_target_companies(
        leads_df=sample_data,
        province="广东",
        city="东莞",
        industry="制造",
        search_keywords=[
            "精密制造",
            "电子制造"
        ],
        exclude_keywords=[
            "贸易公司",
            "个体户"
        ],
        demand_keywords=[
            "EHR",
            "HRIS",
            "HR系统",
            "人力资源系统",
            "数字化HR"
        ],
        require_demand_keyword=True,
        source_types=[
            "招聘网站",
            "新闻",
            "微信公众号"
        ]
    )

    print()
    print("最终结果：")
    print()

    if result.empty:
        print("没有符合条件的企业。")
    else:
        print(
            result.to_string(
                index=False
            )
        )