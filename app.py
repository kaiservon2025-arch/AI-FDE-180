import streamlit as st
import pandas as pd
from datetime import datetime, date

import lead_search
import lead_contact_search


# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="亦行 AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    .brand {
        font-size: 25px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .brand-sub {
        color: #6b7280;
        font-size: 13px;
        margin-bottom: 20px;
    }

    .page-title {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .page-desc {
        color: #6b7280;
        margin-bottom: 20px;
    }

    .kpi-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px;
        min-height: 110px;
    }

    .kpi-title {
        color: #6b7280;
        font-size: 13px;
    }

    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        margin-top: 8px;
    }

    .empty-box {
        border: 1px dashed #d1d5db;
        border-radius: 12px;
        padding: 45px;
        text-align: center;
        color: #6b7280;
        margin-top: 20px;
    }

    .source-box {
        background: #f8fafc;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Session State
# ============================================================

if "leads_df" not in st.session_state:
    st.session_state.leads_df = pd.DataFrame()

if "selected_company" not in st.session_state:
    st.session_state.selected_company = ""

if "search_history" not in st.session_state:
    st.session_state.search_history = []

if "saved_tasks" not in st.session_state:
    st.session_state.saved_tasks = []

if "page" not in st.session_state:
    st.session_state.page = "工作台"


# ============================================================
# 基础工具
# ============================================================

def text(value):
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_company_name(value):
    return text(value)


def clean_df(df):
    """
    统一 DataFrame。

    核心修复：
    lead_search.py 返回的是：
        公司

    系统内部统一使用：
        企业名称
    """

    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            return pd.DataFrame()

    if df.empty:
        return df.copy()

    df = df.copy()

    # --------------------------------------------------------
    # 企业名称字段统一
    # --------------------------------------------------------

    company_aliases = [
        "企业名称",
        "公司",
        "公司名称",
        "企业",
        "company",
        "company_name",
    ]

    if "企业名称" not in df.columns:

        source_column = None

        for column in company_aliases:
            if column in df.columns:
                source_column = column
                break

        if source_column:
            df = df.rename(
                columns={
                    source_column: "企业名称"
                }
            )

    else:

        # 如果企业名称存在，但为空，则尝试从其他字段补充
        for column in company_aliases:

            if column == "企业名称":
                continue

            if column not in df.columns:
                continue

            empty_mask = (
                df["企业名称"]
                .fillna("")
                .astype(str)
                .str.strip()
                .eq("")
            )

            df.loc[
                empty_mask,
                "企业名称"
            ] = df.loc[
                empty_mask,
                column
            ]

    # --------------------------------------------------------
    # 删除重复企业名称字段
    # --------------------------------------------------------

    for column in [
        "公司",
        "公司名称",
        "企业",
        "company",
        "company_name",
    ]:
        if column in df.columns and column != "企业名称":
            df = df.drop(
                columns=[column]
            )

    # --------------------------------------------------------
    # 常用字段补齐
    # --------------------------------------------------------

    default_columns = [
        "省份",
        "城市",
        "行业",
        "员工数量",
        "员工数量原文",
        "联系人",
        "职位",
        "邮箱",
        "电话",
        "企业官网",
        "搜索模式",
        "企业条件命中",
        "企业关键词命中",
        "需求关键词命中",
        "需求关键词",
        "需求原文",
        "搜索关键词",
        "来源",
        "来源类型",
        "来源网址",
        "网页摘要",
        "信息日期",
        "抓取时间",
        "状态",
        "企业匹配状态",
        "联系方式状态",
        "联系方式归属依据",
        "匹配依据",
    ]

    for column in default_columns:
        if column not in df.columns:
            df[column] = ""

    # --------------------------------------------------------
    # 企业名称清洗
    # --------------------------------------------------------

    if "企业名称" in df.columns:
        df["企业名称"] = (
            df["企业名称"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    return df


def company_column(df):
    if df is None or df.empty:
        return None

    for column in [
        "企业名称",
        "公司",
        "公司名称",
        "企业",
        "company",
        "company_name",
    ]:
        if column in df.columns:
            return column

    return None


def get_value(row, names):
    for name in names:
        if name in row.index:
            value = row.get(name)

            if value is not None:
                if not pd.isna(value):
                    value = str(value).strip()

                    if value:
                        return value

    return ""


def has_contact(row):
    email = get_value(
        row,
        ["邮箱", "email"]
    )

    phone = get_value(
        row,
        ["电话", "手机", "phone"]
    )

    return bool(email or phone)


def has_demand(row):
    keyword = get_value(
        row,
        ["需求关键词"]
    )

    hit = get_value(
        row,
        ["需求关键词命中"]
    )

    return bool(
        keyword
        or str(hit).lower() in [
            "true",
            "1",
            "yes",
            "是",
        ]
    )


def safe_int(value, default=0):
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


# ============================================================
# 搜索
# ============================================================

def run_enterprise_search(
    province,
    city,
    industry,
    search_keywords,
    exclude_keywords,
    max_results,
    search_demand,
    demand_keywords,
):
    """
    调用 lead_search.py。

    lead_search.py 的真实接口：
    search_manufacturing_leads(...)
    """

    try:

        result = lead_search.search_manufacturing_leads(
            province=province,
            city=city,
            industry=industry,
            search_keywords=search_keywords,
            exclude_keywords=exclude_keywords,
            demand_keywords=demand_keywords,
            limit=max_results,
            search_demand=search_demand,
        )

        df = clean_df(result)

        return df, None

    except Exception as e:

        return (
            pd.DataFrame(),
            f"企业搜索失败：{type(e).__name__}: {e}",
        )


def run_demand_search(
    province,
    city,
    demand_keywords,
    max_results,
):
    try:

        result = lead_search.search_demand_signals(
            demand_keywords=demand_keywords,
            province=province,
            city=city,
            limit=max_results,
        )

        return clean_df(result), None

    except Exception as e:

        return (
            pd.DataFrame(),
            f"需求搜索失败：{type(e).__name__}: {e}",
        )


def merge_demand(
    enterprise_df,
    demand_df,
):
    """
    将需求信息合并到企业数据。

    不删除企业数据。
    """

    enterprise_df = clean_df(
        enterprise_df
    )

    demand_df = clean_df(
        demand_df
    )

    if enterprise_df.empty:
        return enterprise_df

    if demand_df.empty:
        return enterprise_df

    if "企业名称" not in enterprise_df.columns:
        return enterprise_df

    if "企业名称" not in demand_df.columns:
        return enterprise_df

    # 建立需求映射
    demand_map = {}

    for _, row in demand_df.iterrows():

        company = text(
            row.get("企业名称", "")
        )

        if not company:
            continue

        key = company.lower()

        if key not in demand_map:
            demand_map[key] = {
                "需求关键词": [],
                "需求原文": [],
                "需求来源": [],
                "需求来源网址": [],
            }

        keyword = text(
            row.get("需求关键词", "")
        )

        demand_text = text(
            row.get("需求原文", "")
        )

        source = text(
            row.get("来源", "")
        )

        url = text(
            row.get("来源网址", "")
        )

        if keyword and keyword not in demand_map[key]["需求关键词"]:
            demand_map[key]["需求关键词"].append(
                keyword
            )

        if demand_text and demand_text not in demand_map[key]["需求原文"]:
            demand_map[key]["需求原文"].append(
                demand_text
            )

        if source and source not in demand_map[key]["需求来源"]:
            demand_map[key]["需求来源"].append(
                source
            )

        if url and url not in demand_map[key]["需求来源网址"]:
            demand_map[key]["需求来源网址"].append(
                url
            )

    result = enterprise_df.copy()

    if "需求关键词" not in result.columns:
        result["需求关键词"] = ""

    if "需求原文" not in result.columns:
        result["需求原文"] = ""

    if "需求关键词命中" not in result.columns:
        result["需求关键词命中"] = False

    for index, row in result.iterrows():

        company = text(
            row.get("企业名称", "")
        )

        key = company.lower()

        if key not in demand_map:
            continue

        info = demand_map[key]

        if info["需求关键词"]:

            result.at[
                index,
                "需求关键词"
            ] = "、".join(
                info["需求关键词"]
            )

            result.at[
                index,
                "需求关键词命中"
            ] = True

        if info["需求原文"]:

            result.at[
                index,
                "需求原文"
            ] = "\n\n".join(
                info["需求原文"]
            )

    return clean_df(result)


# ============================================================
# 联系方式搜索
# ============================================================

def run_contact_search(
    leads_df,
    max_results,
):
    """
    关键修复：

    lead_contact_search.py 的真实函数：

    search_contacts_for_leads(
        leads,
        max_results_per_query=5
    )

    不能再传：
        max_results=

    """

    if leads_df is None or leads_df.empty:
        return pd.DataFrame(), None

    try:

        result = (
            lead_contact_search
            .search_contacts_for_leads(
                leads=leads_df,
                max_results_per_query=5,
            )
        )

        df = clean_df(result)

        return df, None

    except Exception as e:

        return (
            pd.DataFrame(),
            f"联系方式搜索失败：{type(e).__name__}: {e}",
        )


def merge_contacts(
    leads_df,
    contacts_df,
):
    """
    将联系方式搜索结果合并回企业线索。

    一个企业可以对应多个联系人。
    """

    leads_df = clean_df(
        leads_df
    )

    contacts_df = clean_df(
        contacts_df
    )

    if leads_df.empty:
        return leads_df

    if contacts_df.empty:
        return leads_df

    if "企业名称" not in leads_df.columns:
        return leads_df

    if "企业名称" not in contacts_df.columns:
        return leads_df

    # --------------------------------------------------------
    # 联系方式映射
    # --------------------------------------------------------

    contact_map = {}

    for _, row in contacts_df.iterrows():

        company = text(
            row.get("企业名称", "")
        )

        if not company:
            continue

        key = company.lower()

        if key not in contact_map:
            contact_map[key] = []

        contact_map[key].append(
            row.to_dict()
        )

    final_rows = []

    # --------------------------------------------------------
    # 合并
    # --------------------------------------------------------

    for _, lead_row in leads_df.iterrows():

        lead = lead_row.to_dict()

        company = text(
            lead.get("企业名称", "")
        )

        key = company.lower()

        contacts = contact_map.get(
            key,
            []
        )

        if not contacts:
            final_rows.append(
                lead
            )
            continue

        for contact in contacts:

            merged = dict(lead)

            for field in [
                "联系人",
                "职位",
                "邮箱",
                "电话",
                "企业匹配状态",
                "联系方式状态",
                "联系方式归属依据",
                "匹配依据",
                "来源类型",
                "来源",
                "网址",
                "信息日期",
            ]:

                value = text(
                    contact.get(
                        field,
                        ""
                    )
                )

                if value:
                    merged[field] = value

            if contact.get("网址"):
                merged["联系方式来源网址"] = contact.get(
                    "网址"
                )

            final_rows.append(
                merged
            )

    return clean_df(
        pd.DataFrame(final_rows)
    )


# ============================================================
# 最终清洗
# ============================================================

def final_clean(
    df,
    employee_min,
    employee_max,
    require_contact,
):
    df = clean_df(df)

    if df.empty:
        return df

    # 企业名称为空的结果删除
    if "企业名称" in df.columns:

        df = df[
            df["企业名称"]
            .fillna("")
            .astype(str)
            .str.strip()
            .ne("")
        ]

    # --------------------------------------------------------
    # 员工数量筛选
    # --------------------------------------------------------

    if "员工数量" in df.columns:

        employee_series = pd.to_numeric(
            df["员工数量"],
            errors="coerce",
        )

        # 只有识别出员工数量的才严格过滤
        known_mask = employee_series.notna()

        if employee_min > 0:
            df = df[
                (~known_mask)
                | (employee_series >= employee_min)
            ]

        if employee_max > 0:
            df = df[
                (~known_mask)
                | (employee_series <= employee_max)
            ]

    # --------------------------------------------------------
    # 联系方式筛选
    # --------------------------------------------------------

    if require_contact:

        contact_mask = df.apply(
            has_contact,
            axis=1,
        )

        df = df[
            contact_mask
        ]

    # --------------------------------------------------------
    # 企业去重
    # --------------------------------------------------------

    if "企业名称" in df.columns:

        df["_company_key"] = (
            df["企业名称"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        df = df.drop_duplicates(
            subset=["_company_key"],
            keep="first",
        )

        df = df.drop(
            columns=["_company_key"],
            errors="ignore",
        )

    return df.reset_index(
        drop=True
    )


# ============================================================
# 状态
# ============================================================

def add_status(df):

    df = clean_df(df)

    if df.empty:
        return df

    if "状态" not in df.columns:
        df["状态"] = "新线索"

    df["状态"] = (
        df["状态"]
        .fillna("新线索")
        .replace("", "新线索")
    )

    return df


def get_status_counts(df):

    if df is None or df.empty:
        return {}

    if "状态" not in df.columns:
        return {}

    return (
        df["状态"]
        .fillna("新线索")
        .value_counts()
        .to_dict()
    )


# ============================================================
# 公司详情
# ============================================================

def show_company_detail(
    company_name,
    df,
):
    if not company_name:
        return

    if df is None or df.empty:
        return

    company_df = df[
        df["企业名称"].astype(str).str.strip()
        == company_name
    ]

    if company_df.empty:
        return

    row = company_df.iloc[0]

    st.markdown("---")
    st.subheader(company_name)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "城市",
            text(row.get("城市", "")) or "-",
        )

    with c2:
        st.metric(
            "行业",
            text(row.get("行业", "")) or "-",
        )

    with c3:
        employee = row.get(
            "员工数量",
            "",
        )

        st.metric(
            "员工数量",
            text(employee) or "-",
        )

    with c4:
        st.metric(
            "状态",
            text(row.get("状态", "新线索"))
            or "新线索",
        )

    st.markdown("### 联系方式")

    contact_col1, contact_col2, contact_col3 = st.columns(3)

    with contact_col1:
        st.write(
            "**联系人**"
        )
        st.write(
            text(row.get("联系人", ""))
            or "暂无"
        )

    with contact_col2:
        st.write(
            "**职位**"
        )
        st.write(
            text(row.get("职位", ""))
            or "暂无"
        )

    with contact_col3:
        st.write(
            "**邮箱**"
        )
        st.write(
            text(row.get("邮箱", ""))
            or "暂无"
        )

    st.write(
        "**电话：**",
        text(row.get("电话", ""))
        or "暂无",
    )

    st.markdown("### 需求信号")

    demand = text(
        row.get(
            "需求关键词",
            "",
        )
    )

    if demand:
        st.success(
            f"需求关键词：{demand}"
        )
    else:
        st.info(
            "暂未发现明确需求关键词"
        )

    demand_text = text(
        row.get(
            "需求原文",
            "",
        )
    )

    if demand_text:
        with st.expander(
            "查看需求原文"
        ):
            st.write(
                demand_text
            )

    st.markdown("### 来源")

    source = text(
        row.get(
            "来源",
            "",
        )
    )

    source_type = text(
        row.get(
            "来源类型",
            "",
        )
    )

    source_url = text(
        row.get(
            "来源网址",
            "",
        )
    )

    st.write(
        f"来源类型：{source_type or '未知'}"
    )

    st.write(
        f"来源标题：{source or '未知'}"
    )

    if source_url:
        st.link_button(
            "打开来源网页",
            source_url,
        )

    st.markdown("### 操作")

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        if st.button(
            "生成开发邮件",
            key=f"email_{company_name}",
            use_container_width=True,
        ):
            st.session_state.page = "触达"
            st.session_state.selected_company = company_name
            st.rerun()

    with a2:
        if st.button(
            "记录跟进",
            key=f"follow_{company_name}",
            use_container_width=True,
        ):
            st.session_state.page = "跟进"
            st.session_state.selected_company = company_name
            st.rerun()

    with a3:
        if st.button(
            "标记已联系",
            key=f"contacted_{company_name}",
            use_container_width=True,
        ):
            mask = (
                st.session_state.leads_df[
                    "企业名称"
                ].astype(str)
                == company_name
            )

            st.session_state.leads_df.loc[
                mask,
                "状态"
            ] = "已联系"

            st.success(
                "已标记为已联系"
            )

    with a4:
        if st.button(
            "关闭详情",
            key=f"close_{company_name}",
            use_container_width=True,
        ):
            st.session_state.selected_company = ""
            st.rerun()


# ============================================================
# 侧边栏
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="brand">🎯 亦行 AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="brand-sub">AI B2B 获客与销售线索系统</div>',
        unsafe_allow_html=True,
    )

    pages = [
        "工作台",
        "找客户",
        "线索",
        "触达",
        "跟进",
        "数据",
    ]

    current_page = st.session_state.page

    for page_name in pages:

        if st.button(
            page_name,
            key=f"nav_{page_name}",
            use_container_width=True,
        ):
            st.session_state.page = page_name
            st.rerun()


# ============================================================
# 工作台
# ============================================================

if st.session_state.page == "工作台":

    st.markdown(
        '<div class="page-title">工作台</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">查看当前获客和销售线索情况</div>',
        unsafe_allow_html=True,
    )

    df = clean_df(
        st.session_state.leads_df
    )

    total = len(df)

    contact_count = 0
    demand_count = 0
    contacted_count = 0

    if not df.empty:

        contact_count = int(
            df.apply(
                has_contact,
                axis=1,
            ).sum()
        )

        demand_count = int(
            df.apply(
                has_demand,
                axis=1,
            ).sum()
        )

        if "状态" in df.columns:
            contacted_count = int(
                (
                    df["状态"]
                    .astype(str)
                    .isin(
                        [
                            "已联系",
                            "跟进中",
                            "已成交",
                        ]
                    )
                ).sum()
            )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">企业线索</div>
                <div class="kpi-value">{total}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">有联系方式</div>
                <div class="kpi-value">{contact_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">有需求信号</div>
                <div class="kpi-value">{demand_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">已触达</div>
                <div class="kpi-value">{contacted_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 快速开始")

    q1, q2, q3 = st.columns(3)

    with q1:
        if st.button(
            "🔎 开始找客户",
            use_container_width=True,
        ):
            st.session_state.page = "找客户"
            st.rerun()

    with q2:
        if st.button(
            "📋 查看线索",
            use_container_width=True,
        ):
            st.session_state.page = "线索"
            st.rerun()

    with q3:
        if st.button(
            "✉️ 开始触达",
            use_container_width=True,
        ):
            st.session_state.page = "触达"
            st.rerun()

    if df.empty:

        st.markdown(
            """
            <div class="empty-box">
                目前还没有客户线索。<br>
                点击「开始找客户」开始第一次搜索。
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown("### 最近线索")

        display_columns = [
            "企业名称",
            "城市",
            "行业",
            "员工数量",
            "联系人",
            "职位",
            "邮箱",
            "电话",
            "需求关键词",
            "状态",
        ]

        display_columns = [
            x
            for x in display_columns
            if x in df.columns
        ]

        st.dataframe(
            df[
                display_columns
            ].head(10),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 找客户
# ============================================================

elif st.session_state.page == "找客户":

    st.markdown(
        '<div class="page-title">找客户</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">通过公开网页搜索制造业企业、需求信号和联系方式</div>',
        unsafe_allow_html=True,
    )

    natural_query = st.text_input(
        "你想找什么客户？",
        placeholder="例如：东莞 电子制造 100-1000人 有HR数字化需求的企业",
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        province = st.text_input(
            "省份",
            value="广东",
        )

    with col2:

        city = st.text_input(
            "城市",
            value="东莞",
        )

    with col3:

        industry = st.text_input(
            "行业",
            value="电子制造",
        )

    st.markdown("### 企业条件")

    col1, col2 = st.columns(2)

    with col1:

        search_keywords_text = st.text_input(
            "企业关键词",
            value="连接器、电子制造、精密制造、线束",
            help="多个关键词用逗号或中文顿号分隔",
        )

    with col2:

        exclude_keywords_text = st.text_input(
            "排除关键词",
            value="",
            help="例如：学校、医院、政府",
        )

    col1, col2 = st.columns(2)

    with col1:

        employee_min = st.number_input(
            "员工人数下限",
            min_value=0,
            value=50,
            step=10,
        )

    with col2:

        employee_max = st.number_input(
            "员工人数上限",
            min_value=0,
            value=5000,
            step=100,
        )

    st.markdown("### 需求信号")

    search_demand = st.checkbox(
        "同时搜索 HR / EHR / HRIS 等需求信号",
        value=True,
    )

    demand_keywords_text = st.text_input(
        "需求关键词",
        value="EHR、HRIS、HR系统、人力资源系统、数字化HR",
    )

    st.markdown("### 搜索设置")

    col1, col2 = st.columns(2)

    with col1:

        require_contact = st.checkbox(
            "只保留有联系方式的企业",
            value=False,
        )

    with col2:

        max_results = st.slider(
            "最多企业数量",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
        )

    st.markdown("")

    search_button = st.button(
        "🔎 开始搜索客户",
        type="primary",
        use_container_width=True,
    )

    if search_button:

        search_keywords = lead_search.normalize_list(
            search_keywords_text
        )

        exclude_keywords = lead_search.normalize_list(
            exclude_keywords_text
        )

        demand_keywords = lead_search.normalize_list(
            demand_keywords_text
        )

        if not province and not city and not industry:
            st.warning(
                "至少填写省份、城市或行业中的一项。"
            )

        else:

            progress = st.progress(
                0
            )

            status_box = st.empty()

            # ------------------------------------------------
            # 第一阶段：企业搜索
            # ------------------------------------------------

            status_box.info(
                "① 正在搜索企业..."
            )

            progress.progress(
                20
            )

            enterprise_df, error = run_enterprise_search(
                province=province,
                city=city,
                industry=industry,
                search_keywords=search_keywords,
                exclude_keywords=exclude_keywords,
                max_results=max_results,
                search_demand=False,
                demand_keywords=demand_keywords,
            )

            if error:

                status_box.error(
                    error
                )

            # ------------------------------------------------
            # 第二阶段：需求搜索
            # ------------------------------------------------

            demand_df = pd.DataFrame()

            if search_demand:

                status_box.info(
                    "② 正在搜索需求信号..."
                )

                progress.progress(
                    45
                )

                demand_df, demand_error = run_demand_search(
                    province=province,
                    city=city,
                    demand_keywords=demand_keywords,
                    max_results=max_results,
                )

                if demand_error:
                    st.warning(
                        demand_error
                    )

            # ------------------------------------------------
            # 第三阶段：合并需求
            # ------------------------------------------------

            status_box.info(
                "③ 正在合并企业与需求数据..."
            )

            progress.progress(
                60
            )

            merged_df = merge_demand(
                enterprise_df,
                demand_df,
            )

            # ------------------------------------------------
            # 检查企业名称
            # ------------------------------------------------

            merged_df = clean_df(
                merged_df
            )

            if (
                not merged_df.empty
                and "企业名称"
                not in merged_df.columns
            ):

                status_box.error(
                    "搜索成功，但没有识别到企业名称字段。"
                )

                st.write(
                    "当前返回字段：",
                    list(
                        merged_df.columns
                    ),
                )

            else:

                # ------------------------------------------------
                # 第四阶段：联系方式
                # ------------------------------------------------

                status_box.info(
                    "④ 正在搜索企业联系方式..."
                )

                progress.progress(
                    75
                )

                contacts_df = pd.DataFrame()

                if not merged_df.empty:

                    contacts_df, contact_error = run_contact_search(
                        merged_df,
                        max_results,
                    )

                    if contact_error:

                        st.warning(
                            contact_error
                        )

                # ------------------------------------------------
                # 第五阶段：合并联系方式
                # ------------------------------------------------

                status_box.info(
                    "⑤ 正在整理最终线索..."
                )

                progress.progress(
                    90
                )

                if not contacts_df.empty:

                    final_df = merge_contacts(
                        merged_df,
                        contacts_df,
                    )

                    # 如果要求联系方式，
                    # 没联系方式的企业过滤掉
                    if require_contact:

                        final_df = final_clean(
                            final_df,
                            employee_min,
                            employee_max,
                            True,
                        )

                    else:

                        final_df = final_clean(
                            final_df,
                            employee_min,
                            employee_max,
                            False,
                        )

                else:

                    final_df = final_clean(
                        merged_df,
                        employee_min,
                        employee_max,
                        require_contact,
                    )

                final_df = add_status(
                    final_df
                )

                progress.progress(
                    100
                )

                status_box.success(
                    f"搜索完成，共获得 {len(final_df)} 条企业线索。"
                )

                # ------------------------------------------------
                # 保存
                # ------------------------------------------------

                st.session_state.leads_df = final_df

                st.session_state.search_history.insert(
                    0,
                    {
                        "时间": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "省份": province,
                        "城市": city,
                        "行业": industry,
                        "企业关键词": search_keywords_text,
                        "需求关键词": demand_keywords_text
                        if search_demand
                        else "",
                        "结果数量": len(final_df),
                    },
                )

                if len(
                    st.session_state.search_history
                ) > 20:

                    st.session_state.search_history = (
                        st.session_state.search_history[
                            :20
                        ]
                    )

                st.session_state.saved_tasks.append(
                    {
                        "时间": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "任务": "客户搜索",
                        "条件": (
                            f"{province} {city} "
                            f"{industry}"
                        ),
                        "数量": len(final_df),
                    }
                )

                st.rerun()


# ============================================================
# 线索
# ============================================================

elif st.session_state.page == "线索":

    st.markdown(
        '<div class="page-title">线索</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">查看和管理已经发现的企业客户</div>',
        unsafe_allow_html=True,
    )

    df = clean_df(
        st.session_state.leads_df
    )

    if df.empty:

        st.markdown(
            """
            <div class="empty-box">
                暂无线索。<br>
                请先进入「找客户」搜索企业。
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        # ----------------------------------------------------
        # 筛选
        # ----------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            search_text = st.text_input(
                "搜索企业",
                placeholder="输入企业名称",
            )

        with c2:

            status_options = [
                "全部"
            ]

            if "状态" in df.columns:
                status_options += sorted(
                    [
                        x
                        for x in df["状态"]
                        .dropna()
                        .astype(str)
                        .unique()
                        if x
                    ]
                )

            status_filter = st.selectbox(
                "状态",
                status_options,
            )

        with c3:

            contact_filter = st.selectbox(
                "联系方式",
                [
                    "全部",
                    "有联系方式",
                    "无联系方式",
                ],
            )

        with c4:

            demand_filter = st.selectbox(
                "需求",
                [
                    "全部",
                    "有需求",
                    "无需求",
                ],
            )

        filtered_df = df.copy()

        if search_text:

            filtered_df = filtered_df[
                filtered_df["企业名称"]
                .astype(str)
                .str.contains(
                    search_text,
                    case=False,
                    na=False,
                )
            ]

        if status_filter != "全部":

            filtered_df = filtered_df[
                filtered_df["状态"].astype(str)
                == status_filter
            ]

        if contact_filter == "有联系方式":

            filtered_df = filtered_df[
                filtered_df.apply(
                    has_contact,
                    axis=1,
                )
            ]

        elif contact_filter == "无联系方式":

            filtered_df = filtered_df[
                ~filtered_df.apply(
                    has_contact,
                    axis=1,
                )
            ]

        if demand_filter == "有需求":

            filtered_df = filtered_df[
                filtered_df.apply(
                    has_demand,
                    axis=1,
                )
            ]

        elif demand_filter == "无需求":

            filtered_df = filtered_df[
                ~filtered_df.apply(
                    has_demand,
                    axis=1,
                )
            ]

        st.write(
            f"当前 {len(filtered_df)} 条线索"
        )

        display_columns = [
            "企业名称",
            "省份",
            "城市",
            "行业",
            "员工数量",
            "联系人",
            "职位",
            "邮箱",
            "电话",
            "需求关键词",
            "来源类型",
            "状态",
        ]

        display_columns = [
            x
            for x in display_columns
            if x in filtered_df.columns
        ]

        st.dataframe(
            filtered_df[
                display_columns
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### 查看企业")

        company_options = [
            x
            for x in filtered_df["企业名称"]
            .astype(str)
            .tolist()
            if x
        ]

        if company_options:

            selected = st.selectbox(
                "选择企业",
                company_options,
            )

            st.session_state.selected_company = selected

            show_company_detail(
                selected,
                df,
            )


# ============================================================
# 触达
# ============================================================

elif st.session_state.page == "触达":

    st.markdown(
        '<div class="page-title">触达</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">准备开发邮件和客户首次触达内容</div>',
        unsafe_allow_html=True,
    )

    df = clean_df(
        st.session_state.leads_df
    )

    if df.empty:

        st.info(
            "目前没有企业线索，请先去「找客户」。"
        )

    else:

        companies = [
            x
            for x in df["企业名称"]
            .astype(str)
            .tolist()
            if x
        ]

        selected_default = (
            st.session_state.selected_company
            if st.session_state.selected_company
            in companies
            else companies[0]
        )

        selected_company = st.selectbox(
            "选择企业",
            companies,
            index=companies.index(
                selected_default
            ),
        )

        row_df = df[
            df["企业名称"].astype(str)
            == selected_company
        ]

        if not row_df.empty:

            row = row_df.iloc[0]

            contact_name = text(
                row.get(
                    "联系人",
                    "",
                )
            )

            email = text(
                row.get(
                    "邮箱",
                    "",
                )
            )

            demand = text(
                row.get(
                    "需求关键词",
                    "",
                )
            )

            st.markdown("### 客户信息")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.write(
                    f"**联系人：** {contact_name or '暂无'}"
                )

            with c2:
                st.write(
                    f"**职位：** {text(row.get('职位', '')) or '暂无'}"
                )

            with c3:
                st.write(
                    f"**邮箱：** {email or '暂无'}"
                )

            st.markdown("### 开发邮件")

            subject = st.text_input(
                "邮件主题",
                value=f"{selected_company}｜HR数字化交流",
            )

            body = st.text_area(
                "邮件正文",
                height=320,
                value=(
                    f"{contact_name or '您好'}，\n\n"
                    f"我们主要为制造企业提供HR数字化解决方案，"
                    f"帮助企业提升人力资源管理效率。\n\n"
                    f"了解到贵司在{demand or '企业管理与人力资源'}方面"
                    f"可能存在相关需求，希望有机会和您简单交流一下。\n\n"
                    f"如果方便，我可以根据贵司目前的人员规模和管理模式，"
                    f"提供一份针对性的方案参考。\n\n"
                    f"谢谢！"
                ),
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(
                    "保存邮件草稿",
                    use_container_width=True,
                ):

                    st.session_state.saved_tasks.append(
                        {
                            "时间": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "任务": "邮件草稿",
                            "企业": selected_company,
                            "主题": subject,
                        }
                    )

                    st.success(
                        "邮件草稿已保存。"
                    )

            with c2:

                if st.button(
                    "标记为待触达",
                    use_container_width=True,
                ):

                    mask = (
                        st.session_state.leads_df[
                            "企业名称"
                        ].astype(str)
                        == selected_company
                    )

                    st.session_state.leads_df.loc[
                        mask,
                        "状态"
                    ] = "待触达"

                    st.success(
                        "已标记为待触达。"
                    )


# ============================================================
# 跟进
# ============================================================

elif st.session_state.page == "跟进":

    st.markdown(
        '<div class="page-title">跟进</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">记录客户沟通和下一步行动</div>',
        unsafe_allow_html=True,
    )

    df = clean_df(
        st.session_state.leads_df
    )

    if df.empty:

        st.info(
            "目前没有企业线索。"
        )

    else:

        companies = [
            x
            for x in df["企业名称"]
            .astype(str)
            .tolist()
            if x
        ]

        selected_default = (
            st.session_state.selected_company
            if st.session_state.selected_company
            in companies
            else companies[0]
        )

        selected_company = st.selectbox(
            "企业",
            companies,
            index=companies.index(
                selected_default
            ),
        )

        follow_status = st.selectbox(
            "跟进状态",
            [
                "新线索",
                "待触达",
                "已联系",
                "跟进中",
                "已成交",
                "暂不考虑",
                "关闭",
            ],
        )

        next_date = st.date_input(
            "下次跟进日期",
            value=date.today(),
        )

        note = st.text_area(
            "跟进记录",
            height=180,
            placeholder="记录本次沟通情况、客户需求、下一步动作...",
        )

        if st.button(
            "保存跟进记录",
            type="primary",
            use_container_width=True,
        ):

            mask = (
                st.session_state.leads_df[
                    "企业名称"
                ].astype(str)
                == selected_company
            )

            st.session_state.leads_df.loc[
                mask,
                "状态"
            ] = follow_status

            st.session_state.saved_tasks.append(
                {
                    "时间": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "任务": "客户跟进",
                    "企业": selected_company,
                    "状态": follow_status,
                    "下次跟进": str(next_date),
                    "备注": note,
                }
            )

            st.success(
                "跟进记录已保存。"
            )


# ============================================================
# 数据
# ============================================================

elif st.session_state.page == "数据":

    st.markdown(
        '<div class="page-title">数据</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">查看线索、联系方式和搜索任务数据</div>',
        unsafe_allow_html=True,
    )

    df = clean_df(
        st.session_state.leads_df
    )

    total = len(df)

    contact_count = 0

    email_count = 0

    phone_count = 0

    demand_count = 0

    if not df.empty:

        contact_count = int(
            df.apply(
                has_contact,
                axis=1,
            ).sum()
        )

        if "邮箱" in df.columns:

            email_count = int(
                df["邮箱"]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )

        if "电话" in df.columns:

            phone_count = int(
                df["电话"]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )

        demand_count = int(
            df.apply(
                has_demand,
                axis=1,
            ).sum()
        )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "企业",
            total,
        )

    with c2:
        st.metric(
            "联系方式",
            contact_count,
        )

    with c3:
        st.metric(
            "邮箱",
            email_count,
        )

    with c4:
        st.metric(
            "电话",
            phone_count,
        )

    with c5:
        st.metric(
            "需求信号",
            demand_count,
        )

    st.markdown("### 搜索历史")

    if st.session_state.search_history:

        history_df = pd.DataFrame(
            st.session_state.search_history
        )

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "暂无搜索历史。"
        )

    st.markdown("### 已保存任务")

    if st.session_state.saved_tasks:

        tasks_df = pd.DataFrame(
            st.session_state.saved_tasks
        )

        st.dataframe(
            tasks_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "暂无任务记录。"
        )

    st.markdown("### 导出数据")

    if not df.empty:

        csv_data = df.to_csv(
            index=False,
            encoding="utf-8-sig",
        )

        st.download_button(
            "⬇️ 下载全部线索 CSV",
            data=csv_data,
            file_name=(
                f"亦行AI_客户线索_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )