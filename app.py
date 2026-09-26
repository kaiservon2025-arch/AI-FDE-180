import streamlit as st
import pandas as pd
from ai_analyzer import analyze_customer


st.set_page_config(
    page_title="AI获客分析系统",
    page_icon="🤖",
    layout="wide"
)


st.title("🤖 AI获客分析系统")
st.write("上传客户Excel，AI自动分析客户价值并生成开发建议。")


# ==============================
# 上传Excel
# ==============================

uploaded_file = st.file_uploader(
    "请选择客户Excel文件",
    type=["xlsx"]
)


if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    st.success(f"成功读取 {len(df)} 个客户")

    st.subheader("客户数据预览")

    st.dataframe(
        df,
        use_container_width=True
    )


    # ==============================
    # 开始分析
    # ==============================

    if st.button(
        "🚀 开始AI分析",
        type="primary"
    ):

        results = []

        progress = st.progress(0)

        status = st.empty()


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

                result = analyze_customer(customer)

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


                results.append({

                    "公司": customer["公司"],
                    "国家": customer["国家"],
                    "行业": customer["行业"],
                    "员工数量": customer["员工数量"],
                    "网站": customer["网站"],

                    "客户等级": result["customer_level"],
                    "客户评分": score,

                    "客户优先级": priority,
                    "推荐动作": action,
                    "跟进天数": follow_up_days,

                    "客户画像": result["customer_profile"],
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
        # 生成结果
        # ==============================

        result_df = pd.DataFrame(
            results
        )


        st.subheader(
            "AI分析结果"
        )

        st.dataframe(
            result_df,
            use_container_width=True
        )


        # ==============================
        # 生成Excel
        # ==============================

        output_file = (
            "day7_ai_lead_generation.xlsx"
        )

        result_df.to_excel(
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

                label="📥 下载AI获客分析结果",

                data=file,

                file_name=output_file,

                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                )
            )