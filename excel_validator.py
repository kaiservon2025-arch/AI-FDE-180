import pandas as pd


# 系统要求的字段
REQUIRED_COLUMNS = [
    "公司",
    "国家",
    "行业",
    "员工数量",
    "网站"
]


def validate_excel(file):
    """
    检查上传的 Excel 是否符合系统要求
    """

    # ==============================
    # 1. 尝试读取 Excel
    # ==============================

    try:
        df = pd.read_excel(file)

    except Exception as e:
        return False, f"无法读取Excel文件：{e}", None


    # ==============================
    # 2. 检查字段
    # ==============================

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        message = (
            "Excel格式不正确，缺少以下字段：\n"
            + "\n".join(
                f"- {column}"
                for column in missing_columns
            )
        )

        return False, message, None


    # ==============================
    # 3. 检查是否有客户数据
    # ==============================

    if len(df) == 0:

        return False, "Excel文件中没有客户数据。", None


    # ==============================
    # 4. 检查关键字段是否为空
    # ==============================

    errors = []


    # 公司不能为空
    empty_company = df["公司"].isna()

    if empty_company.any():

        rows = (
            df.index[empty_company] + 2
        ).tolist()

        errors.append(
            f"公司字段存在空值，Excel第 {rows} 行"
        )


    # 国家不能为空
    empty_country = df["国家"].isna()

    if empty_country.any():

        rows = (
            df.index[empty_country] + 2
        ).tolist()

        errors.append(
            f"国家字段存在空值，Excel第 {rows} 行"
        )


    # 行业不能为空
    empty_industry = df["行业"].isna()

    if empty_industry.any():

        rows = (
            df.index[empty_industry] + 2
        ).tolist()

        errors.append(
            f"行业字段存在空值，Excel第 {rows} 行"
        )


    # ==============================
    # 5. 检查员工数量
    # ==============================

    invalid_employees = pd.to_numeric(
        df["员工数量"],
        errors="coerce"
    ).isna()

    if invalid_employees.any():

        rows = (
            df.index[invalid_employees] + 2
        ).tolist()

        errors.append(
            f"员工数量必须是数字，Excel第 {rows} 行存在错误"
        )


    # ==============================
    # 6. 返回检查结果
    # ==============================

    if errors:

        message = (
            "Excel数据存在问题：\n\n"
            + "\n".join(
                f"- {error}"
                for error in errors
            )
        )

        return False, message, None


    return True, "Excel格式和数据检查通过。", df