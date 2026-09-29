import os
import re
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


TAVILY_URL = "https://api.tavily.com/search"


def normalize_list(value):
    """
    将逗号、中文逗号、换行分隔的内容统一成列表。
    """
    if value is None:
        return []

    if isinstance(value, str):
        parts = re.split(r"[,，;\n\r]+", value)
    else:
        parts = value

    result = []

    for item in parts:
        item = str(item).strip()

        if item and item not in result:
            result.append(item)

    return result


def normalize_text(value):
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_company_name(name):
    """
    对企业名称进行基础清洗。
    不进行过度猜测，避免把网页正文误识别成公司名称。
    """
    if not name:
        return ""

    name = normalize_text(name)

    # 去掉常见网页标题尾部
    name = re.sub(
        r"\s*[-_|｜]\s*(官网|首页|招聘|招聘信息|企业信息|公司信息|新闻|资讯|联系我们|联系|About|Contact).*$",
        "",
        name,
        flags=re.I,
    )

    name = re.sub(r"^(首页|官网|招聘|企业信息|公司信息)[：:\s-]*", "", name)

    # 常见中国企业名称
    patterns = [
        r"[\u4e00-\u9fa5A-Za-z0-9（）()·&\-.]{2,80}(?:有限公司|股份有限公司|集团有限公司|集团|有限责任公司)",
        r"[\u4e00-\u9fa5A-Za-z0-9（）()·&\-.]{2,80}(?:公司|企业)",
    ]

    for pattern in patterns:
        match = re.search(pattern, name)

        if match:
            candidate = match.group(0).strip()

            if 3 <= len(candidate) <= 100:
                return candidate

    # 如果整个标题过长，不把整段标题当公司名称
    if len(name) > 80:
        return ""

    # 没有明显企业后缀时，不强行识别
    return ""


def extract_employee_count(text):
    """
    从公开搜索结果中尽可能提取员工数量。

    返回：
    {
        "员工数量": int 或 None,
        "员工数量原文": str
    }
    """
    text = normalize_text(text)

    patterns = [
        r"(?:员工|人员|职工|雇员|从业人员)[^\d]{0,15}(\d+(?:\.\d+)?)\s*(?:人|名)?",
        r"(?:员工人数|员工数量|人员规模|公司规模|企业规模)[^\d]{0,15}(\d+(?:\.\d+)?)\s*(?:人|名)?",
        r"(\d+(?:\.\d+)?)\s*[-~至到]\s*(\d+(?:\.\d+)?)\s*人",
        r"(\d+(?:\.\d+)?)\s*人以上",
        r"(\d+(?:\.\d+)?)\s*人左右",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)

        if not match:
            continue

        try:
            if len(match.groups()) >= 2:
                value1 = float(match.group(1))
                value2 = float(match.group(2))

                value = int((value1 + value2) / 2)

                return {
                    "员工数量": value,
                    "员工数量原文": match.group(0),
                }

            value = int(float(match.group(1)))

            return {
                "员工数量": value,
                "员工数量原文": match.group(0),
            }

        except Exception:
            continue

    return {
        "员工数量": None,
        "员工数量原文": "",
    }


def detect_source_type(url, title="", content=""):
    """
    判断公开信息来源类型。
    """
    text = f"{url} {title} {content}".lower()

    if "mp.weixin.qq.com" in text or "微信公众号" in text:
        return "微信公众号"

    if any(
        x in text
        for x in [
            "zhipin.com",
            "liepin.com",
            "51job.com",
            "zhaopin.com",
            "lagou.com",
            "boss直聘",
            "猎聘",
            "前程无忧",
            "智联招聘",
        ]
    ):
        return "招聘网站"

    if any(
        x in text
        for x in [
            "linkedin.com",
            "领英",
        ]
    ):
        return "职业社交"

    if any(
        x in text
        for x in [
            "gov.cn",
            "政府",
            "产业园",
            "开发区",
            "商会",
            "协会",
        ]
    ):
        return "政府/协会/产业园"

    if any(
        x in text
        for x in [
            "tender",
            "招标",
            "采购",
            "中标",
            "bid",
        ]
    ):
        return "招投标/采购"

    if any(
        x in text
        for x in [
            "展会",
            "expo",
            "exhibition",
            "conference",
            "博览会",
        ]
    ):
        return "展会/会议"

    if any(
        x in text
        for x in [
            "news",
            "新闻",
            "资讯",
            "媒体",
            "新浪",
            "搜狐",
            "网易",
            "腾讯",
        ]
    ):
        return "新闻/媒体"

    if any(
        x in text
        for x in [
            "知乎",
            "zhihu.com",
            "blog",
            "博客",
            "论坛",
            "社区",
        ]
    ):
        return "社区/博客"

    if any(
        x in text
        for x in [
            ".pdf",
            "白皮书",
            "产品目录",
            "catalog",
            "brochure",
        ]
    ):
        return "PDF/公开资料"

    return "其他公开网页"


def tavily_search(
    query: str,
    max_results: int = 10,
    search_depth: str = "advanced",
):
    """
    直接调用 Tavily HTTP API。
    不使用 tavily-python SDK，避免 SDK 编码兼容问题。
    """
    api_key = os.getenv("TAVILY_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "没有找到 TAVILY_API_KEY，请检查 .env 文件。"
        )

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }

    response = requests.post(
        TAVILY_URL,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("results", [])


def build_enterprise_queries(
    province="",
    city="",
    industry="",
    search_keywords=None,
):
    """
    企业基础搜索。

    注意：
    这里绝对不加入 demand_keywords。

    企业搜索和需求搜索完全独立。
    """
    search_keywords = normalize_list(search_keywords)

    location_parts = []

    if province:
        location_parts.append(str(province).strip())

    if city:
        location_parts.append(str(city).strip())

    location = " ".join(location_parts).strip()

    queries = []

    # 第一组：行业搜索
    if location and industry:
        queries.append(
            f"{location} {industry} 企业 公司"
        )

    elif industry:
        queries.append(
            f"{industry} 企业 公司"
        )

    elif location:
        queries.append(
            f"{location} 制造企业 公司"
        )

    # 第二组：企业关键词搜索
    for keyword in search_keywords:

        if location and industry:
            queries.append(
                f"{location} {industry} {keyword} 企业 公司"
            )

        elif location:
            queries.append(
                f"{location} {keyword} 企业 公司"
            )

        elif industry:
            queries.append(
                f"{industry} {keyword} 企业 公司"
            )

        else:
            queries.append(
                f"{keyword} 企业 公司"
            )

    # 第三组：企业官网/企业信息
    if location and industry:
        queries.append(
            f"{location} {industry} 企业 官网 联系方式"
        )

    elif location:
        queries.append(
            f"{location} 企业 官网 联系方式"
        )

    elif industry:
        queries.append(
            f"{industry} 企业 官网 联系方式"
        )

    # 去重
    final_queries = []

    for query in queries:
        query = normalize_text(query)

        if query and query not in final_queries:
            final_queries.append(query)

    return final_queries


def build_demand_queries(
    demand_keywords=None,
    province="",
    city="",
):
    """
    需求关键词独立搜索。

    注意：
    这里不要求企业先满足行业、员工数量等条件。

    因此：
    即使企业不属于用户设置的企业筛选范围，
    只要被需求关键词搜索发现，也可以进入候选企业池。
    """
    demand_keywords = normalize_list(demand_keywords)

    location_parts = []

    if province:
        location_parts.append(str(province).strip())

    if city:
        location_parts.append(str(city).strip())

    location = " ".join(location_parts).strip()

    queries = []

    for keyword in demand_keywords:

        if location:
            queries.append(
                f"{location} {keyword} 企业"
            )

            queries.append(
                f"{location} {keyword} 招聘"
            )

            queries.append(
                f"{location} {keyword} 人事"
            )

            queries.append(
                f"{location} {keyword} 数字化"
            )

        else:
            queries.append(
                f"{keyword} 企业"
            )

            queries.append(
                f"{keyword} 招聘"
            )

            queries.append(
                f"{keyword} 人事"
            )

    final_queries = []

    for query in queries:
        query = normalize_text(query)

        if query and query not in final_queries:
            final_queries.append(query)

    return final_queries


def result_to_lead(
    result: Dict,
    search_mode="enterprise",
    matched_keyword="",
):
    """
    将 Tavily 单条结果转换为统一企业线索记录。
    """
    title = normalize_text(result.get("title", ""))
    content = normalize_text(
        result.get("content", "")
    )
    url = normalize_text(
        result.get("url", "")
    )

    company = normalize_company_name(
        f"{title} {content}"
    )

    employee_info = extract_employee_count(
        f"{title} {content}"
    )

    source_type = detect_source_type(
        url=url,
        title=title,
        content=content,
    )

    return {
        "公司": company,
        "省份": "",
        "城市": "",
        "行业": "",
        "员工数量": employee_info["员工数量"],
        "员工数量原文": employee_info["员工数量原文"],
        "联系人": "",
        "职位": "",
        "邮箱": "",
        "电话": "",
        "企业官网": "",
        "搜索模式": search_mode,
        "企业条件命中": False,
        "企业关键词命中": False,
        "需求关键词命中": False,
        "需求关键词": matched_keyword,
        "需求原文": content if search_mode == "demand" else "",
        "搜索关键词": matched_keyword,
        "来源": title,
        "来源类型": source_type,
        "来源网址": url,
        "网页摘要": content,
        "信息日期": "",
        "抓取时间": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "状态": "新线索",
    }


def deduplicate_results(results):
    """
    企业级去重。

    优先按照：
    公司名称
    ↓
    来源网址
    ↓
    标题+网址

    同一家企业的不同公开来源全部保留。
    """
    company_map = {}

    final_results = []

    for item in results:

        company = normalize_company_name(
            item.get("公司", "")
        )

        url = normalize_text(
            item.get("来源网址", "")
        )

        title = normalize_text(
            item.get("来源", "")
        )

        item["公司"] = company

        if company:
            key = company.lower()

            if key not in company_map:
                company_map[key] = item
                final_results.append(item)
            else:
                existing = company_map[key]

                # 合并需求关键词
                old_kw = normalize_list(
                    existing.get("需求关键词", "")
                )

                new_kw = normalize_list(
                    item.get("需求关键词", "")
                )

                merged_kw = old_kw[:]

                for kw in new_kw:
                    if kw not in merged_kw:
                        merged_kw.append(kw)

                existing["需求关键词"] = "、".join(
                    merged_kw
                )

                # 需求命中
                if item.get("需求关键词命中"):
                    existing["需求关键词命中"] = True

                # 企业条件命中
                if item.get("企业条件命中"):
                    existing["企业条件命中"] = True

                # 企业关键词命中
                if item.get("企业关键词命中"):
                    existing["企业关键词命中"] = True

                # 需求原文
                if (
                    item.get("需求原文")
                    and item.get("需求原文")
                    not in str(existing.get("需求原文", ""))
                ):
                    old_text = str(
                        existing.get("需求原文", "")
                    )

                    if old_text:
                        existing["需求原文"] = (
                            old_text
                            + "\n\n"
                            + item["需求原文"]
                        )
                    else:
                        existing["需求原文"] = item[
                            "需求原文"
                        ]

                # 员工数量
                if (
                    not existing.get("员工数量")
                    and item.get("员工数量")
                ):
                    existing["员工数量"] = item[
                        "员工数量"
                    ]

                if (
                    not existing.get("员工数量原文")
                    and item.get("员工数量原文")
                ):
                    existing["员工数量原文"] = item[
                        "员工数量原文"
                    ]

                # 不覆盖已有来源
                existing_url = existing.get(
                    "来源网址",
                    "",
                )

                if url and url != existing_url:
                    existing["补充来源网址"] = (
                        str(
                            existing.get(
                                "补充来源网址",
                                "",
                            )
                        )
                        + ("\n" if existing.get(
                            "补充来源网址",
                            "",
                        ) else "")
                        + url
                    )

        else:
            # 没有可靠企业名称的结果也暂时保留。
            # 后续联系方式/企业名称解析阶段再处理。
            key = f"{title}|{url}"

            if key not in [
                f"{x.get('来源', '')}|{x.get('来源网址', '')}"
                for x in final_results
            ]:
                final_results.append(item)

    return final_results


def search_enterprises(
    province="",
    city="",
    industry="",
    search_keywords=None,
    exclude_keywords=None,
    limit=20,
):
    """
    第一条独立搜索链：

    企业条件 + 企业关键词

    不包含需求关键词。
    """
    exclude_keywords = normalize_list(
        exclude_keywords
    )

    queries = build_enterprise_queries(
        province=province,
        city=city,
        industry=industry,
        search_keywords=search_keywords,
    )

    results = []

    max_results_per_query = max(
        5,
        min(10, limit),
    )

    for query in queries:

        try:
            search_results = tavily_search(
                query=query,
                max_results=max_results_per_query,
            )

        except Exception as e:
            print(
                f"[企业搜索失败] {query} -> {e}"
            )
            continue

        for result in search_results:

            title = normalize_text(
                result.get("title", "")
            )

            content = normalize_text(
                result.get("content", "")
            )

            combined = f"{title} {content}"

            # 排除关键词
            excluded = False

            for keyword in exclude_keywords:
                if keyword.lower() in combined.lower():
                    excluded = True
                    break

            if excluded:
                continue

            lead = result_to_lead(
                result=result,
                search_mode="enterprise",
            )

            lead["省份"] = province
            lead["城市"] = city
            lead["行业"] = industry

            # 企业条件命中
            lead["企业条件命中"] = True

            # 企业关键词命中
            for keyword in normalize_list(
                search_keywords
            ):
                if keyword.lower() in combined.lower():
                    lead["企业关键词命中"] = True

                    if not lead.get("搜索关键词"):
                        lead["搜索关键词"] = keyword

                    break

            results.append(lead)

            if len(results) >= limit * 3:
                break

        if len(results) >= limit * 3:
            break

    results = deduplicate_results(results)

    return results[:limit]


def search_demand_signals(
    demand_keywords=None,
    province="",
    city="",
    limit=50,
):
    """
    第二条独立搜索链：

    只负责需求关键词。

    不要求企业满足：
    - 行业
    - 员工数量
    - 企业关键词

    因此可以发现筛选条件之外的企业。
    """
    demand_keywords = normalize_list(
        demand_keywords
    )

    if not demand_keywords:
        return []

    queries = build_demand_queries(
        demand_keywords=demand_keywords,
        province=province,
        city=city,
    )

    results = []

    for query in queries:

        try:
            search_results = tavily_search(
                query=query,
                max_results=min(10, limit),
            )

        except Exception as e:
            print(
                f"[需求搜索失败] {query} -> {e}"
            )
            continue

        for result in search_results:

            title = normalize_text(
                result.get("title", "")
            )

            content = normalize_text(
                result.get("content", "")
            )

            combined = f"{title} {content}"

            matched_keyword = ""

            for keyword in demand_keywords:
                if keyword.lower() in combined.lower():
                    matched_keyword = keyword
                    break

            if not matched_keyword:
                continue

            lead = result_to_lead(
                result=result,
                search_mode="demand",
                matched_keyword=matched_keyword,
            )

            lead["省份"] = province
            lead["城市"] = city

            lead["需求关键词命中"] = True
            lead["需求关键词"] = matched_keyword
            lead["需求原文"] = content

            results.append(lead)

            if len(results) >= limit:
                break

        if len(results) >= limit:
            break

    return deduplicate_results(results)


def merge_enterprise_and_demand(
    enterprise_results,
    demand_results,
):
    """
    将两条完全独立的搜索链合并。

    重点：
    demand_results 不会因为不符合 enterprise 条件而被删除。
    """
    all_results = []

    for item in enterprise_results:
        all_results.append(item)

    for item in demand_results:
        all_results.append(item)

    return deduplicate_results(all_results)


def search_manufacturing_leads(
    province="",
    city="",
    industry="",
    search_keywords=None,
    exclude_keywords=None,
    demand_keywords=None,
    limit=20,
    search_recruitment=True,
    search_news=True,
    search_industry=True,
    search_wechat=True,
    search_demand=False,
):
    """
    保留旧函数名称，避免旧代码调用时报错。

    新逻辑：

    企业搜索
        ↓
    需求搜索（可选）
        ↓
    合并
        ↓
    去重

    demand_keywords 不会自动参与企业搜索。
    只有 search_demand=True 时才执行需求搜索。
    """

    enterprise_results = search_enterprises(
        province=province,
        city=city,
        industry=industry,
        search_keywords=search_keywords,
        exclude_keywords=exclude_keywords,
        limit=limit,
    )

    demand_results = []

    if search_demand:
        demand_results = search_demand_signals(
            demand_keywords=demand_keywords,
            province=province,
            city=city,
            limit=limit,
        )

    merged = merge_enterprise_and_demand(
        enterprise_results=enterprise_results,
        demand_results=demand_results,
    )

    return merged[:limit]


if __name__ == "__main__":

    print("=" * 60)
    print("测试：企业搜索")
    print("=" * 60)

    enterprise_results = search_enterprises(
        province="广东",
        city="东莞",
        industry="电子制造",
        search_keywords=[
            "连接器",
            "精密制造",
        ],
        limit=10,
    )

    print(
        f"企业搜索结果：{len(enterprise_results)} 条"
    )

    for item in enterprise_results[:5]:
        print(
            item.get("公司"),
            "|",
            item.get("企业条件命中"),
            "|",
            item.get("企业关键词命中"),
        )

    print("\n" + "=" * 60)
    print("测试：需求关键词独立搜索")
    print("=" * 60)

    demand_results = search_demand_signals(
        demand_keywords=[
            "EHR",
            "HRIS",
            "HR系统",
        ],
        province="广东",
        city="东莞",
        limit=10,
    )

    print(
        f"需求搜索结果：{len(demand_results)} 条"
    )

    for item in demand_results[:5]:
        print(
            item.get("公司"),
            "|",
            item.get("需求关键词"),
            "|",
            item.get("需求关键词命中"),
        )

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)