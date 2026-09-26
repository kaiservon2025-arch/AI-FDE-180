import streamlit as st


def show_email_preview(result_df):
    """
    显示客户信息和AI生成的开发邮件
    """

    st.subheader("📧 客户开发邮件")

    # 客户列表
    company_list = result_df["公司"].tolist()

    selected_company = st.selectbox(
        "请选择一个客户",
        company_list
    )

    # 获取当前客户
    selected_customer = result_df[
        result_df["公司"] == selected_company
    ].iloc[0]

    # ==============================
    # 客户信息
    # ==============================

    st.markdown("### 👤 客户信息")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(
            f"**公司：** {selected_customer['公司']}"
        )

    with col2:
        st.write(
            f"**国家：** {selected_customer['国家']}"
        )

    with col3:
        st.write(
            f"**客户评分：** {selected_customer['客户评分']}"
        )

    # ==============================
    # 客户开发策略
    # ==============================

    st.markdown("### 🎯 客户开发策略")

    st.write(
        selected_customer["开发策略"]
    )

    # ==============================
    # 邮件主题
    # ==============================

    st.markdown("### ✉️ 邮件主题")

    st.text_input(
        "邮件主题",
        value=selected_customer["邮件主题"],
        key="email_subject_preview"
    )

    # ==============================
    # 邮件正文
    # ==============================

    st.markdown("### 📝 英文开发邮件")

    st.text_area(
        "邮件正文",
        value=selected_customer["邮件正文"],
        height=300,
        key="email_body_preview"
    )