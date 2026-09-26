import streamlit as st
import pandas as pd

from ai_analyzer import analyze_customer
from excel_validator import validate_excel
from sales_task import generate_sales_tasks
from today_tasks import get_today_tasks


st.set_page_config(
    page_title="AI获客分析系统",
    page_icon="🤖",
    layout="wide"
)


st.title("🤖 AI获客分析系统")
st.write("上传客户Excel，AI自动分析客户价值并生成开发建议。")


# ==============================
# 初始化Session State
# ==============================

if "result_df" not in st.session_state:
    st.session_state["result_df"] = None


# ==============================
# 上传Excel
# ==============================

uploaded_file = st.file_uploader(
    "请选择客户Excel文件",
    type=["xlsx"]
)


if uploaded_file is not None:

    # ==============================
    # Excel格式和数据检查
    # ==============================

    is_valid, message, df = validate_excel(
        uploaded_file
    )

    if not is_valid:
        st.error(message)
        st.stop()

    st.success(message)
    st.success(f"成功读取 {len(df)} 个客户")


    # ==============================
    # 原始客户数据统计
    # ==============================

    st.subheader("📊 客户数据概览")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "客户总数",
            len(df)
        )

    with col2:
        st.metric(
            "高优先级客户",
            0
        )

    with col3:
        st.metric(
            "中优先级客户",
            0
        )

    with col4:
        st.metric(
            "数据行数",
            len(df)
        )


    # ==============================
    # 客户数据预览
    # ==============================

    st.subheader("客户数据预览")

    st.dataframe(
        df,
        use_container_width=True
    )


    # ==============================
    # 开始AI分析
    # ==============================

    if st.button(
        "🚀 开始AI分析",
        type="primary"
    ):

        results = []

        progress = st.progress(0)

        status = st.empty()


        # ==============================
        # 逐个分析客户
        # ==============================

        for index, row in df.iterrows():

            company = row["公司"]

            status.write(
                f"正在分析：{company}"
            )

            customer = {
                "公司": row["公司"],
                "国家": row["国家"],
                "行业": row["行业"],
                "员工数量": row["员工数量"],
                "网站": row["网站"]
            }

            try:

                result = analyze_customer(
                    customer
                )

                score = int(
                    result["customer_score"]
                )


                # ==============================
                # 客户优先级
                # ==============================

                if score >= 80:

                    priority = "高"
                    action = "立即发送开发邮件"
                    follow_up_days = 1

                elif score >= 70:

                    priority = "中"
                    action = "进一步收集客户信息，3天内跟进"
                    follow_up_days = 3

                else:

                    priority = "低"
                    action = "暂缓开发"
                    follow_up_days = 7


                # ==============================
                # 保存结果
                # ==============================

                results.append({

                    "公司": customer["公司"],
                    "国家": customer["国家"],
                    "行业": customer["行业"],
                    "员工数量": customer["员工数量"],
                    "网站": customer["网站"],

                    "客户等级": result[
                        "customer_level"
                    ],

                    "客户评分": score,

                    "客户优先级": priority,

                    "推荐动作": action,

                    "跟进天数": follow_up_days,

                    "客户画像": result[
                        "customer_profile"
                    ],

                    "可能需求": "\n".join(
                        result["possible_needs"]
                    ),

                    "开发策略": result[
                        "development_strategy"
                    ],

                    "邮件主题": result[
                        "email_subject"
                    ],

                    "邮件正文": result[
                        "email_body"
                    ]
                })

                print(
                    f"{company} 分析完成"
                )

            except Exception as e:

                st.error(
                    f"{company} 分析失败：{e}"
                )

            progress.progress(
                (index + 1) / len(df)
            )


        status.success(
            "🎉 AI分析完成！"
        )


        # ==============================
        # 生成结果DataFrame
        # ==============================

        result_df = pd.DataFrame(
            results
        )

        st.session_state["result_df"] = result_df


    # ==============================
    # 获取已经保存的分析结果
    # ==============================

    result_df = st.session_state["result_df"]


    if result_df is not None:

        # ==============================
        # AI分析统计
        # ==============================

        st.subheader("📈 AI分析概览")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "客户总数",
                len(result_df)
            )

        with col2:

            high_count = (
                result_df["客户优先级"] == "高"
            ).sum()

            st.metric(
                "高优先级客户",
                high_count
            )

        with col3:

            medium_count = (
                result_df["客户优先级"] == "中"
            ).sum()

            st.metric(
                "中优先级客户",
                medium_count
            )

        with col4:

            average_score = round(
                result_df["客户评分"].mean(),
                1
            )

            st.metric(
                "平均客户评分",
                average_score
            )


        # ==============================
        # 客户优先级可视化
        # ==============================

        st.subheader("📊 客户优先级分布")

        priority_counts = (
            result_df["客户优先级"]
            .value_counts()
            .reindex(
                ["高", "中", "低"],
                fill_value=0
            )
        )

        st.bar_chart(
            priority_counts
        )


        # ==============================
        # 客户开发邮件
        # ==============================

        st.subheader("📧 客户开发邮件")

        company_list = result_df[
            "公司"
        ].tolist()

        selected_company = st.selectbox(
            "请选择一个客户",
            company_list
        )

        selected_customer = result_df[
            result_df["公司"] == selected_company
        ].iloc[0]


        # ==============================
        # 客户信息
        # ==============================

        st.markdown(
            "### 👤 客户信息"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.write(
                f"**公司：** "
                f"{selected_customer['公司']}"
            )

        with col2:

            st.write(
                f"**国家：** "
                f"{selected_customer['国家']}"
            )

        with col3:

            st.write(
                f"**客户评分：** "
                f"{selected_customer['客户评分']}"
            )


        # ==============================
        # 客户开发策略
        # ==============================

        st.markdown(
            "### 🎯 客户开发策略"
        )

        st.write(
            selected_customer["开发策略"]
        )


        # ==============================
        # 邮件主题
        # ==============================

        st.markdown(
            "### ✉️ 邮件主题"
        )

        st.text_input(
            "邮件主题",
            value=selected_customer["邮件主题"],
            key="email_subject_preview"
        )


        # ==============================
        # 英文开发邮件
        # ==============================

        st.markdown(
            "### 📝 英文开发邮件"
        )

        st.text_area(
            "邮件正文",
            value=selected_customer["邮件正文"],
            height=300,
            key="email_body_preview"
        )


        # ==============================
        # AI分析结果
        # ==============================

        st.subheader(
            "AI分析结果"
        )

        st.dataframe(
            result_df,
            use_container_width=True
        )


        # ==============================
        # AI销售任务中心
        # ==============================

        st.subheader(
            "🎯 AI销售任务中心"
        )

        task_df = generate_sales_tasks(
            result_df
        )

        st.dataframe(
            task_df,
            use_container_width=True
        )


        # ==============================
        # 保存Excel
        # ==============================

        output_file = (
            "day9_ai_sales_tasks.xlsx"
        )

        task_df.to_excel(
            output_file,
            index=False
        )


        # ==============================
        # 下载按钮
        # ==============================

        with open(
            output_file,
            "rb"
        ) as file:

            st.download_button(

                label="📥 下载销售任务表",

                data=file,

                file_name=output_file,

                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                )
            )