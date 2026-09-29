import inspect
from datetime import datetime

import pandas as pd
import streamlit as st

import lead_search
import lead_contact_search


# =========================================================
# 页面配置
# =========================================================

st.set_page_config(
    page_title="亦行 AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 全局 CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =========================
       Streamlit 顶部区域
       ========================= */

    header[data-testid="stHeader"] {
        background: transparent;
        height: 0;
        min-height: 0;
    }

    div[data-testid="stToolbar"] {
        display: none;
    }

    /* =========================
       页面主体
       ========================= */

    .block-container {
        max-width: 1500px !important;
        padding-top: 2.8rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* =========================
       Sidebar
       ========================= */

    [data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    /* =========================
       隐藏 Streamlit 默认菜单
       ========================= */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    /* =========================
       品牌
       ========================= */

    .brand-title {
        font-size: 25px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 2px;
    }

    .brand-subtitle {
        color: #6b7280;
        font-size: 13px;
    }

    /* =========================
       页面标题
       ========================= */

    .page-title {
        font-size: 27px;
        font-weight: 700;
        color: #111827;
        margin-top: 0.5rem;
        margin-bottom: 4px;
        line-height: 1.4;
    }

    .page-desc {
        color: #6b7280;
        font-size: 14px;
        margin-bottom: 20px;
        line-height: 1.5;
    }

    /* =========================
       区块标题
       ========================= */

    .section-title {
        font-size: 18px;
        font-weight: 650;
        color: #111827;
        margin-top: 10px;
        margin-bottom: 12px;
    }

    /* =========================
       KPI
       ========================= */

    .kpi-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px 20px;
        background: #ffffff;
        min-height: 105px;
    }

    .kpi-label {
        font-size: 13px;
        color: #6b7280;
        margin-bottom: 8px;
    }

    .kpi-number {
        font-size: 28px;
        font-weight: 700;
        color: #111827;
    }

    .kpi-desc {
        font-size: 12px;
        color: #9ca3af;
        margin-top: 4px;
    }

    /* =========================
       企业卡片
       ========================= */

    .company-card {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 14px 16px;
        background: white;
        margin-bottom: 8px;
    }

    .company-name {
        font-weight: 650;
        font-size: 15px;
        color: #111827;
    }

    .company-meta {
        color: #6b7280;
        font-size: 12px;
        margin-top: 4px;
    }

    /* =========================
       标签
       ========================= */

    .tag {
        display: inline-block;
        padding: 3px 8px;
        margin-right: 4px;
        margin-top: 4px;
        border-radius: 12px;
        background: #f3f4f6;
        color: #374151;
        font-size: 11px;
    }

    .tag-demand {
        background: #eef2ff;
        color: #4338ca;
    }

    .tag-contact {
        background: #ecfdf5;
        color: #047857;
    }

    /* =========================
       空状态
       ========================= */

    .empty-box {
        border: 1px dashed #d1d5db;
        border-radius: 12px;
        padding: 50px 30px;
        text-align: center;
        background: #fafafa;
    }

    .empty-title {
        font-size: 18px;
        font-weight: 600;
        color: #374151;
    }

    .empty-text {
        color: #9ca3af;
        font-size: 14px;
        margin-top: 5px;
    }

    /* =========================
       小文字
       ========================= */

    .muted {
        color: #6b7280;
        font-size: 13px;
    }

    /* =========================
       Streamlit 输入框
       ========================= */

    div[data-baseweb="input"] {
        border-radius: 8px;
    }

    div[data-baseweb="select"] {
        border-radius: 8px;
    }

    textarea {
        border-radius: 8px !important;
    }

    /* =========================
       按钮
       ========================= */

    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }

    /* =========================
       DataFrame
       ========================= */

    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Session State
# =========================================================

if "leads_df" not in st.session_state:
    st.session_state.leads_df = pd.DataFrame()

if "selected_company" not in st.session_state:
    st.session_state.selected_company = None

if "search_history" not in st.session_state:
    st.session_state.search_history = []

if "saved_tasks" not in st.session_state:
    st.session_state.saved_tasks = []

if "last_search_config" not in st.session_state:
    st.session_state.last_search_config = {}

if "page" not in st.session_state:
    st.session_state.page = "🏠 工作台"


# =========================================================
# 工具函数
# =========================================================

def clean_df(df):
    if df is None:
        return pd.DataFrame()

    if isinstance(df, pd.DataFrame):
        return df.copy()

    if isinstance(df, list):
        return pd.DataFrame(df)

    return pd.DataFrame(df)


def normalize_text(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def first_column(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None


def get_value(row, candidates, default=""):
    for col in candidates:
        if col in row.index:
            value = normalize_text(row[col])
            if value:
                return value
    return default


def company_column(df):
    return first_column(
        df,
        [
            "企业名称",
            "公司名称",
            "company",
            "company_name",
            "企业",
        ],
    )


def has_contact(row):
    email = get_value(
        row,
        [
            "邮箱",
            "email",
            "Email",
            "企业邮箱",
        ],
    )

    phone = get_value(
        row,
        [
            "电话",
            "手机号",
            "手机",
            "phone",
            "联系电话",
        ],
    )

    return bool(email or phone)


def safe_call(module, names, kwargs):
    function = None

    for name in names:
        candidate = getattr(module, name, None)

        if callable(candidate):
            function = candidate
            break

    if function is None:
        raise AttributeError(
            "找不到函数：" + " / ".join(names)
        )

    try:
        signature = inspect.signature(function)

        filtered = {}

        for key, value in kwargs.items():
            if key in signature.parameters:
                filtered[key] = value

        return function(**filtered)

    except TypeError:
        return function()


def run_enterprise_search(
    province,
    city,
    industry,
    search_keywords,
    exclude_keywords,
    source_types,
    max_results,
):

    kwargs = {
        "province": province,
        "city": city,
        "industry": industry,
        "search_keywords": search_keywords,
        "exclude_keywords": exclude_keywords,
        "source_types": source_types,
        "max_results": max_results,
        "limit": max_results,
        "search_count": max_results,
    }

    result = safe_call(
        lead_search,
        [
            "search_enterprises",
            "search_manufacturing_leads",
        ],
        kwargs,
    )

    return clean_df(result)


def run_demand_search(
    demand_keywords,
    max_results,
):

    if not demand_keywords:
        return pd.DataFrame()

    kwargs = {
        "demand_keywords": demand_keywords,
        "keywords": demand_keywords,
        "max_results": max_results,
        "limit": max_results,
        "search_count": max_results,
    }

    try:

        result = safe_call(
            lead_search,
            [
                "search_demand_signals",
            ],
            kwargs,
        )

        return clean_df(result)

    except Exception:
        return pd.DataFrame()


def merge_demand_manually(
    enterprise_df,
    demand_df,
):

    result = enterprise_df.copy()

    if demand_df.empty:
        return result

    company_a = company_column(result)
    company_b = company_column(demand_df)

    if not company_a or not company_b:
        return result

    keyword_col = first_column(
        demand_df,
        [
            "需求关键词",
            "demand_keyword",
            "keyword",
        ],
    )

    text_col = first_column(
        demand_df,
        [
            "需求原文",
            "demand_text",
            "原文",
        ],
    )

    url_col = first_column(
        demand_df,
        [
            "来源网址",
            "来源",
            "url",
            "source_url",
        ],
    )

    date_col = first_column(
        demand_df,
        [
            "信息日期",
            "发布日期",
            "date",
        ],
    )

    demand_map = {}

    for _, row in demand_df.iterrows():

        company = normalize_text(
            row[company_b]
        )

        if not company:
            continue

        if company not in demand_map:

            demand_map[company] = {
                "keywords": set(),
                "texts": [],
                "urls": [],
                "dates": [],
            }

        item = demand_map[company]

        if keyword_col:

            value = normalize_text(
                row[keyword_col]
            )

            if value:
                item["keywords"].add(
                    value
                )

        if text_col:

            value = normalize_text(
                row[text_col]
            )

            if (
                value
                and value not in item["texts"]
            ):
                item["texts"].append(
                    value
                )

        if url_col:

            value = normalize_text(
                row[url_col]
            )

            if (
                value
                and value not in item["urls"]
            ):
                item["urls"].append(
                    value
                )

        if date_col:

            value = normalize_text(
                row[date_col]
            )

            if (
                value
                and value not in item["dates"]
            ):
                item["dates"].append(
                    value
                )

    result["需求关键词"] = ""
    result["需求原文"] = ""
    result["需求来源"] = ""
    result["需求信息日期"] = ""

    for index, row in result.iterrows():

        company = normalize_text(
            row[company_a]
        )

        if company not in demand_map:
            continue

        item = demand_map[company]

        result.at[
            index,
            "需求关键词",
        ] = "、".join(
            sorted(
                item["keywords"]
            )
        )

        result.at[
            index,
            "需求原文",
        ] = "\n\n".join(
            item["texts"]
        )

        result.at[
            index,
            "需求来源",
        ] = "\n".join(
            item["urls"]
        )

        result.at[
            index,
            "需求信息日期",
        ] = "、".join(
            item["dates"]
        )

    return result


def merge_enterprise_demand(
    enterprise_df,
    demand_df,
):

    if enterprise_df.empty:
        return demand_df.copy()

    if demand_df.empty:
        return enterprise_df.copy()

    try:

        result = safe_call(
            lead_search,
            [
                "merge_enterprise_and_demand",
            ],
            {
                "enterprise_df": enterprise_df,
                "demand_df": demand_df,
                "enterprise_results": enterprise_df,
                "demand_results": demand_df,
                "leads_df": enterprise_df,
            },
        )

        result = clean_df(result)

        if not result.empty:
            return result

    except Exception:
        pass

    return merge_demand_manually(
        enterprise_df,
        demand_df,
    )


def run_contact_search(
    leads_df,
    max_results,
):

    if leads_df.empty:
        return pd.DataFrame()

    kwargs = {
        "leads_df": leads_df,
        "lead_df": leads_df,
        "companies_df": leads_df,
        "df": leads_df,
        "max_results": max_results,
        "limit": max_results,
    }

    result = safe_call(
        lead_contact_search,
        [
            "search_contacts_for_leads",
            "search_contacts",
            "batch_search_contacts",
            "find_contacts_for_leads",
        ],
        kwargs,
    )

    return clean_df(result)


def merge_contacts_manually(
    leads_df,
    contacts_df,
):

    result = leads_df.copy()

    if contacts_df.empty:
        return result

    lead_company = company_column(
        result
    )

    contact_company = company_column(
        contacts_df
    )

    if (
        not lead_company
        or not contact_company
    ):
        return result

    contact_map = {}

    for _, row in contacts_df.iterrows():

        company = normalize_text(
            row[contact_company]
        )

        if not company:
            continue

        if company not in contact_map:
            contact_map[company] = (
                row.to_dict()
            )

    contact_fields = [
        "联系人",
        "职位",
        "邮箱",
        "电话",
        "联系方式状态",
        "联系方式归属依据",
        "来源",
        "来源类型",
        "信息日期",
    ]

    for field in contact_fields:

        if field not in result.columns:
            result[field] = ""

    for index, row in result.iterrows():

        company = normalize_text(
            row[lead_company]
        )

        if company not in contact_map:
            continue

        contact = contact_map[
            company
        ]

        for field, value in contact.items():

            if field not in result.columns:
                continue

            if not normalize_text(
                result.at[
                    index,
                    field,
                ]
            ):
                result.at[
                    index,
                    field,
                ] = value

    return result


def merge_contacts(
    leads_df,
    contacts_df,
):

    if leads_df.empty:
        return leads_df

    if contacts_df.empty:
        return leads_df

    try:

        result = safe_call(
            lead_contact_search,
            [
                "merge_contacts_to_leads",
            ],
            {
                "leads_df": leads_df,
                "contacts_df": contacts_df,
                "contact_df": contacts_df,
                "df": leads_df,
            },
        )

        result = clean_df(result)

        if not result.empty:
            return result

    except Exception:
        pass

    return merge_contacts_manually(
        leads_df,
        contacts_df,
    )


def final_clean(
    df,
    require_contact=True,
):

    df = clean_df(df)

    if df.empty:
        return df

    company_col = company_column(
        df
    )

    if company_col:

        df[company_col] = (
            df[company_col]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df = df[
            df[company_col] != ""
        ]

        df["_company_key"] = (
            df[company_col]
            .str.lower()
            .str.replace(
                " ",
                "",
                regex=False,
            )
            .str.replace(
                "　",
                "",
                regex=False,
            )
        )

        df = df.drop_duplicates(
            subset=[
                "_company_key"
            ],
            keep="first",
        )

        df = df.drop(
            columns=[
                "_company_key"
            ]
        )

    if require_contact:

        mask = df.apply(
            has_contact,
            axis=1,
        )

        df = df[mask]

    return df.reset_index(
        drop=True
    )


def get_status_counts(df):

    result = {
        "全部": len(df),
        "新线索": 0,
        "已联系": 0,
        "已回复": 0,
        "跟进中": 0,
    }

    if df.empty:
        return result

    if "状态" in df.columns:

        status = (
            df["状态"]
            .fillna("")
            .astype(str)
        )

        result["新线索"] = int(
            status.str.contains(
                "新线索",
                regex=False,
            ).sum()
        )

        result["已联系"] = int(
            status.str.contains(
                "已联系",
                regex=False,
            ).sum()
        )

        result["已回复"] = int(
            status.str.contains(
                "已回复",
                regex=False,
            ).sum()
        )

        result["跟进中"] = int(
            status.str.contains(
                "跟进",
                regex=False,
            ).sum()
        )

    else:

        result["新线索"] = len(df)

    return result


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand-title">
            亦行 AI
        </div>

        <div class="brand-subtitle">
            B2B 智能获客工作台
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    menu = [
        "🏠 工作台",
        "🔎 找客户",
        "👥 线索",
        "📧 触达",
        "📅 跟进",
        "📊 数据",
    ]

    current_page = st.radio(
        "导航",
        menu,
        index=menu.index(
            st.session_state.page
        ),
        label_visibility="collapsed",
    )

    st.session_state.page = current_page

    st.divider()

    st.caption(
        "AI FDE 180 · Lead Generation"
    )


# =========================================================
# 工作台
# =========================================================

if (
    st.session_state.page
    == "🏠 工作台"
):

    st.markdown(
        '<div class="page-title">工作台</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">今天，从找到客户开始。</div>',
        unsafe_allow_html=True,
    )

    df = st.session_state.leads_df

    counts = get_status_counts(
        df
    )

    c1, c2, c3, c4 = st.columns(
        4
    )

    metrics = [
        (
            c1,
            "销售线索",
            counts["全部"],
            "当前线索库",
        ),
        (
            c2,
            "新线索",
            counts["新线索"],
            "等待联系",
        ),
        (
            c3,
            "已回复",
            counts["已回复"],
            "需要跟进",
        ),
        (
            c4,
            "跟进中",
            counts["跟进中"],
            "正在推进",
        ),
    ]

    for (
        column,
        title,
        value,
        desc,
    ) in metrics:

        with column:

            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">
                        {title}
                    </div>

                    <div class="kpi-number">
                        {value}
                    </div>

                    <div class="kpi-desc">
                        {desc}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    left, right = st.columns(
        [1.6, 1]
    )

    with left:

        st.markdown(
            '<div class="section-title">最近线索</div>',
            unsafe_allow_html=True,
        )

        if df.empty:

            st.markdown(
                """
                <div class="empty-box">
                    <div class="empty-title">
                        还没有销售线索
                    </div>

                    <div class="empty-text">
                        创建第一个获客任务，开始寻找客户
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            if st.button(
                "🔎 创建获客任务",
                type="primary",
            ):

                st.session_state.page = (
                    "🔎 找客户"
                )

                st.rerun()

        else:

            company_col = company_column(
                df
            )

            display_cols = []

            for col in [
                company_col,
                "联系人",
                "职位",
                "需求关键词",
                "邮箱",
                "电话",
                "状态",
            ]:

                if (
                    col
                    and col in df.columns
                ):
                    display_cols.append(
                        col
                    )

            if display_cols:

                st.dataframe(
                    df[
                        display_cols
                    ].head(10),
                    use_container_width=True,
                    hide_index=True,
                )

    with right:

        st.markdown(
            '<div class="section-title">最近获客任务</div>',
            unsafe_allow_html=True,
        )

        if not st.session_state.search_history:

            st.caption(
                "暂无获客任务"
            )

        else:

            for task in reversed(
                st.session_state.search_history[
                    -5:
                ]
            ):

                st.markdown(
                    f"""
                    <div class="company-card">

                        <div class="company-name">
                            {task.get("任务名称", "获客任务")}
                        </div>

                        <div class="company-meta">
                            {task.get("地区", "")}
                            ·
                            {task.get("行业", "")}
                        </div>

                        <div class="company-meta">
                            找到 {task.get("结果", 0)} 条线索
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# =========================================================
# 找客户
# =========================================================

elif (
    st.session_state.page
    == "🔎 找客户"
):

    st.markdown(
        '<div class="page-title">找客户</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">告诉系统你想找什么客户，系统负责寻找公开商机。</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">✨ 用一句话描述你的客户</div>',
        unsafe_allow_html=True,
    )

    natural_query = st.text_area(
        "目标客户",
        placeholder=(
            "例如：找东莞和深圳50到1000人的电子制造企业，"
            "最好正在考虑EHR或者HR系统。"
        ),
        height=90,
        label_visibility="collapsed",
    )

    if natural_query:

        st.info(
            "AI 自然语言条件解析将在下一阶段接入。"
            "当前可以直接使用下面的结构化筛选。"
        )

    st.divider()

    st.markdown(
        '<div class="section-title">目标客户</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:

        province = st.text_input(
            "省份",
            value="广东",
        )

    with c2:

        city = st.text_input(
            "城市",
            value="东莞",
        )

    industry = st.text_input(
        "行业",
        value="电子制造",
        placeholder=(
            "电子制造、精密制造、机械制造……"
        ),
    )

    search_keywords_text = st.text_input(
        "企业关键词",
        value=(
            "连接器、电子制造、精密制造、线束"
        ),
        placeholder=(
            "多个关键词用逗号分隔"
        ),
    )

    search_keywords = [
        x.strip()
        for x in search_keywords_text
        .replace("，", ",")
        .split(",")
        if x.strip()
    ]

    c1, c2 = st.columns(2)

    with c1:

        employee_min = st.number_input(
            "员工人数 ≥",
            min_value=0,
            value=50,
            step=10,
        )

    with c2:

        employee_max = st.number_input(
            "员工人数 ≤",
            min_value=0,
            value=1000,
            step=50,
        )

    st.divider()

    c1, c2 = st.columns(
        [1.5, 1]
    )

    with c1:

        search_demand = st.checkbox(
            "🎯 同时寻找企业需求信号",
            value=True,
        )

        demand_keywords = []

        if search_demand:

            demand_text = st.text_input(
                "需求关键词",
                value=(
                    "EHR、HRIS、HR系统、人力资源系统、数字化HR"
                ),
            )

            demand_keywords = [
                x.strip()
                for x in demand_text
                .replace("，", ",")
                .split(",")
                if x.strip()
            ]

    with c2:

        st.markdown(
            '<div class="muted">高级条件</div>',
            unsafe_allow_html=True,
        )

        with st.expander(
            "展开高级筛选"
        ):

            exclude_text = st.text_input(
                "排除关键词",
                value=(
                    "贸易公司、个体户"
                ),
            )

            exclude_keywords = [
                x.strip()
                for x in exclude_text
                .replace("，", ",")
                .split(",")
                if x.strip()
            ]

            source_options = [
                "企业官网",
                "招聘网站",
                "职业社交",
                "新闻/媒体",
                "政府/协会/产业园",
                "招投标/采购",
                "展会/会议",
                "微信公众号",
                "社区/博客",
                "PDF/公开资料",
                "其他公开网页",
            ]

            source_types = st.multiselect(
                "公开信息来源",
                source_options,
                default=source_options,
            )

            require_contact = st.checkbox(
                "只保留有联系方式的企业",
                value=True,
            )

            max_results = st.slider(
                "搜索数量",
                10,
                100,
                50,
                10,
            )

    st.write("")

    if st.button(
        "🚀 开始寻找客户",
        type="primary",
        use_container_width=True,
    ):

        if employee_max < employee_min:

            st.error(
                "员工人数范围设置错误。"
            )

            st.stop()

        progress = st.progress(0)

        status = st.empty()

        try:

            # =========================================
            # 1. 企业搜索
            # =========================================

            status.info(
                "① 正在寻找目标企业……"
            )

            enterprise_df = run_enterprise_search(
                province,
                city,
                industry,
                search_keywords,
                exclude_keywords,
                source_types,
                max_results,
            )

            progress.progress(20)

            # =========================================
            # 2. 需求搜索
            # =========================================

            demand_df = pd.DataFrame()

            if search_demand:

                status.info(
                    "② 正在寻找企业需求信号……"
                )

                demand_df = run_demand_search(
                    demand_keywords,
                    max_results,
                )

            progress.progress(40)

            # =========================================
            # 3. 企业池合并
            # =========================================

            status.info(
                "③ 正在合并企业线索……"
            )

            merged_df = merge_enterprise_demand(
                enterprise_df,
                demand_df,
            )

            progress.progress(55)

            # =========================================
            # 4. 联系方式
            # =========================================

            status.info(
                "④ 正在寻找公开联系方式……"
            )

            contacts_df = run_contact_search(
                merged_df,
                max_results,
            )

            progress.progress(75)

            # =========================================
            # 5. 联系方式合并
            # =========================================

            status.info(
                "⑤ 正在整理联系方式……"
            )

            final_df = merge_contacts(
                merged_df,
                contacts_df,
            )

            # =========================================
            # 6. 员工数量
            # =========================================

            employee_col = first_column(
                final_df,
                [
                    "员工数量",
                    "员工人数",
                    "employees",
                    "employee_count",
                ],
            )

            if employee_col:

                numbers = pd.to_numeric(
                    final_df[
                        employee_col
                    ],
                    errors="coerce",
                )

                mask = (
                    numbers.isna()
                    |
                    (
                        (numbers >= employee_min)
                        &
                        (numbers <= employee_max)
                    )
                )

                final_df = final_df[
                    mask
                ]

            # =========================================
            # 7. 最终去重
            # =========================================

            final_df = final_clean(
                final_df,
                require_contact,
            )

            # =========================================
            # 8. 状态
            # =========================================

            if not final_df.empty:

                if "状态" not in final_df.columns:

                    final_df["状态"] = (
                        "新线索"
                    )

                else:

                    final_df["状态"] = (
                        final_df["状态"]
                        .fillna("")
                        .replace(
                            "",
                            "新线索",
                        )
                    )

            progress.progress(100)

            # =========================================
            # 保存
            # =========================================

            st.session_state.leads_df = (
                final_df
            )

            config = {
                "省份": province,
                "城市": city,
                "行业": industry,
                "企业关键词": search_keywords,
                "需求关键词": demand_keywords,
                "员工范围": (
                    f"{employee_min}-{employee_max}"
                ),
            }

            st.session_state.last_search_config = (
                config
            )

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )

            task = {
                "任务名称": (
                    f"{city}{industry}获客"
                ),
                "地区": (
                    f"{province} / {city}"
                ),
                "行业": industry,
                "结果": len(final_df),
                "时间": now,
            }

            st.session_state.search_history.append(
                task
            )

            st.session_state.saved_tasks.append(
                {
                    **task,
                    "配置": config,
                }
            )

            status.success(
                f"完成，共找到 {len(final_df)} 条有效线索。"
            )

            st.divider()

            # =========================================
            # 结果
            # =========================================

            if final_df.empty:

                st.warning(
                    "没有找到符合条件并拥有联系方式的企业。"
                )

            else:

                st.markdown(
                    f"""
                    <div class="section-title">
                        找到 {len(final_df)} 条销售线索
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                company_col = company_column(
                    final_df
                )

                display_cols = []

                for col in [
                    company_col,
                    "联系人",
                    "职位",
                    "行业",
                    "城市",
                    "员工数量",
                    "邮箱",
                    "电话",
                    "需求关键词",
                    "状态",
                ]:

                    if (
                        col
                        and col in final_df.columns
                    ):
                        display_cols.append(
                            col
                        )

                if display_cols:

                    st.dataframe(
                        final_df[
                            display_cols
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.dataframe(
                        final_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                csv_data = final_df.to_csv(
                    index=False,
                    encoding="utf-8-sig",
                )

                st.download_button(
                    "⬇️ 导出线索",
                    data=csv_data,
                    file_name=(
                        "亦行AI销售线索.csv"
                    ),
                    mime="text/csv",
                )

        except Exception as e:

            progress.empty()

            status.error(
                "搜索过程中出现错误。"
            )

            st.exception(e)


# =========================================================
# 线索
# =========================================================

elif (
    st.session_state.page
    == "👥 线索"
):

    st.markdown(
        '<div class="page-title">线索</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">统一管理你发现的企业和销售联系人。</div>',
        unsafe_allow_html=True,
    )

    df = st.session_state.leads_df

    if df.empty:

        st.markdown(
            """
            <div class="empty-box">

                <div class="empty-title">
                    还没有线索
                </div>

                <div class="empty-text">
                    去「找客户」创建第一个获客任务
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        company_col = company_column(
            df
        )

        search = st.text_input(
            "搜索",
            placeholder=(
                "企业、联系人、邮箱、电话……"
            ),
        )

        filtered = df.copy()

        if search:

            search_lower = (
                search.lower()
            )

            mask = pd.Series(
                False,
                index=filtered.index,
            )

            for col in filtered.columns:

                mask = (
                    mask
                    |
                    filtered[col]
                    .fillna("")
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        search_lower,
                        regex=False,
                    )
                )

            filtered = filtered[
                mask
            ]

        c1, c2, c3 = st.columns(
            3
        )

        with c1:

            status_filter = st.selectbox(
                "状态",
                [
                    "全部",
                    "新线索",
                    "已联系",
                    "已回复",
                    "跟进中",
                ],
            )

        with c2:

            contact_filter = st.selectbox(
                "联系方式",
                [
                    "全部",
                    "有邮箱",
                    "有电话",
                    "邮箱+电话",
                ],
            )

        with c3:

            demand_filter = st.selectbox(
                "需求信号",
                [
                    "全部",
                    "有需求",
                    "无需求",
                ],
            )

        if (
            status_filter != "全部"
            and "状态" in filtered.columns
        ):

            filtered = filtered[
                filtered["状态"]
                .fillna("")
                .astype(str)
                .str.contains(
                    status_filter,
                    regex=False,
                )
            ]

        if contact_filter != "全部":

            if contact_filter == "有邮箱":

                email_col = first_column(
                    filtered,
                    [
                        "邮箱",
                        "email",
                        "Email",
                    ],
                )

                if email_col:

                    filtered = filtered[
                        filtered[email_col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .ne("")
                    ]

            elif contact_filter == "有电话":

                phone_col = first_column(
                    filtered,
                    [
                        "电话",
                        "手机号",
                        "手机",
                        "phone",
                    ],
                )

                if phone_col:

                    filtered = filtered[
                        filtered[phone_col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .ne("")
                    ]

            elif contact_filter == "邮箱+电话":

                email_col = first_column(
                    filtered,
                    [
                        "邮箱",
                        "email",
                        "Email",
                    ],
                )

                phone_col = first_column(
                    filtered,
                    [
                        "电话",
                        "手机号",
                        "手机",
                        "phone",
                    ],
                )

                if (
                    email_col
                    and phone_col
                ):

                    filtered = filtered[
                        filtered[email_col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .ne("")
                        &
                        filtered[phone_col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .ne("")
                    ]

        if demand_filter != "全部":

            demand_col = first_column(
                filtered,
                [
                    "需求关键词",
                    "demand_keyword",
                ],
            )

            if demand_col:

                if demand_filter == "有需求":

                    filtered = filtered[
                        filtered[demand_col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .ne("")
                    ]

                else:

                    filtered = filtered[
                        filtered[demand_col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .eq("")
                    ]

        st.caption(
            f"当前显示 {len(filtered)} 条线索"
        )

        display_cols = []

        for col in [
            company_col,
            "联系人",
            "职位",
            "行业",
            "城市",
            "员工数量",
            "邮箱",
            "电话",
            "需求关键词",
            "状态",
        ]:

            if (
                col
                and col in filtered.columns
            ):
                display_cols.append(
                    col
                )

        if display_cols:

            event = st.dataframe(
                filtered[
                    display_cols
                ],
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )

            if event.selection.rows:

                selected_index = (
                    event.selection.rows[0]
                )

                selected_row = filtered.iloc[
                    selected_index
                ]

                st.session_state.selected_company = (
                    selected_row.to_dict()
                )

        else:

            st.dataframe(
                filtered,
                use_container_width=True,
                hide_index=True,
            )

        if (
            st.session_state.selected_company
        ):

            row = (
                st.session_state.selected_company
            )

            st.divider()

            st.markdown(
                '<div class="section-title">企业详情</div>',
                unsafe_allow_html=True,
            )

            company_name = get_value(
                row,
                [
                    "企业名称",
                    "公司名称",
                ],
                "未知企业",
            )

            st.subheader(
                company_name
            )

            c1, c2, c3 = st.columns(
                3
            )

            with c1:

                st.caption("联系人")

                st.write(
                    get_value(
                        row,
                        ["联系人"],
                        "暂无",
                    )
                )

                st.caption("职位")

                st.write(
                    get_value(
                        row,
                        ["职位"],
                        "暂无",
                    )
                )

            with c2:

                st.caption("邮箱")

                st.write(
                    get_value(
                        row,
                        [
                            "邮箱",
                            "email",
                            "Email",
                        ],
                        "暂无",
                    )
                )

                st.caption("电话")

                st.write(
                    get_value(
                        row,
                        [
                            "电话",
                            "手机号",
                            "手机",
                        ],
                        "暂无",
                    )
                )

            with c3:

                st.caption("需求信号")

                demand = get_value(
                    row,
                    [
                        "需求关键词",
                    ],
                    "",
                )

                if demand:

                    st.success(
                        demand
                    )

                else:

                    st.write(
                        "暂未发现"
                    )

            demand_text = get_value(
                row,
                ["需求原文"],
            )

            if demand_text:

                st.markdown(
                    "**需求原文**"
                )

                st.info(
                    demand_text
                )

            st.markdown(
                "**公开来源**"
            )

            st.write(
                get_value(
                    row,
                    [
                        "来源",
                        "需求来源",
                        "来源网址",
                    ],
                    "暂无",
                )
            )


# =========================================================
# 触达
# =========================================================

elif (
    st.session_state.page
    == "📧 触达"
):

    st.markdown(
        '<div class="page-title">触达</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">管理开发信、邮件模板和发送记录。</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "邮件发送能力将在下一阶段接入。"
    )

    c1, c2, c3 = st.columns(
        3
    )

    with c1:

        st.metric(
            "待发送",
            0,
        )

    with c2:

        st.metric(
            "已发送",
            0,
        )

    with c3:

        st.metric(
            "已回复",
            0,
        )

    st.divider()

    st.subheader(
        "准备中的功能"
    )

    st.write(
        """
        - AI 自动生成开发信
        - 自定义邮件模板
        - AI 辅助修改
        - 批量发送
        - 每日发送上限
        - 发送时间窗口
        - 已发送客户自动去重
        """
    )


# =========================================================
# 跟进
# =========================================================

elif (
    st.session_state.page
    == "📅 跟进"
):

    st.markdown(
        '<div class="page-title">跟进</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">管理客户回复和下一步销售动作。</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "邮件发送和客户回复接入后，这里会自动形成跟进任务。"
    )

    st.write(
        """
        推荐状态：

        新线索 → 待发送 → 已发送 → 已回复 · 待跟进
        → 跟进中 → 已成交 / 暂不考虑 / 无效
        """
    )


# =========================================================
# 数据
# =========================================================

elif (
    st.session_state.page
    == "📊 数据"
):

    st.markdown(
        '<div class="page-title">数据</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-desc">查看获客效率、联系方式和 AI 使用成本。</div>',
        unsafe_allow_html=True,
    )

    df = st.session_state.leads_df

    c1, c2, c3, c4 = st.columns(
        4
    )

    with c1:

        st.metric(
            "企业线索",
            len(df),
        )

    email_col = first_column(
        df,
        [
            "邮箱",
            "email",
            "Email",
        ],
    )

    phone_col = first_column(
        df,
        [
            "电话",
            "手机号",
            "手机",
            "phone",
        ],
    )

    demand_col = first_column(
        df,
        [
            "需求关键词",
        ],
    )

    with c2:

        email_count = 0

        if email_col:

            email_count = int(
                df[email_col]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )

        st.metric(
            "邮箱",
            email_count,
        )

    with c3:

        phone_count = 0

        if phone_col:

            phone_count = int(
                df[phone_col]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )

        st.metric(
            "电话",
            phone_count,
        )

    with c4:

        demand_count = 0

        if demand_col:

            demand_count = int(
                df[demand_col]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )

        st.metric(
            "需求信号",
            demand_count,
        )

    st.divider()

    st.subheader(
        "AI 成本监控"
    )

    st.caption(
        "Token / API 成本统计将在 AI Agent 接入后自动记录。"
    )

    cost_df = pd.DataFrame(
        [
            {
                "项目": "Tavily 搜索",
                "今日调用": 0,
                "Token": "—",
                "成本": "待接入统计",
            },
            {
                "项目": "DeepSeek",
                "今日调用": 0,
                "Token": "—",
                "成本": "待接入统计",
            },
            {
                "项目": "AI 开发信",
                "今日调用": 0,
                "Token": "—",
                "成本": "待接入统计",
            },
        ]
    )

    st.dataframe(
        cost_df,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "获客任务"
    )

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

        st.caption(
            "暂无获客任务"
        )