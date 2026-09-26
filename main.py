import pandas as pd
from ai_analyzer import analyze_customer


print("==============================")
print("       AI获客分析系统")
print("==============================")
print()

# ==============================
# 1. 读取客户数据
# ==============================

df = pd.read_excel("customers.xlsx")

print(f"读取客户数量：{len(df)}")
print()

results = []


# ==============================
# 2. AI分析客户
# ==============================

for index, row in df.iterrows():

    customer = {
        "公司": row["公司"],
        "国家": row["国家"],
        "行业": row["行业"],
        "员工数量": row["员工数量"],
        "网站": row["网站"]
    }

    print(f"正在分析：{customer['公司']}")

    try:

        result = analyze_customer(customer)

        score = int(result["customer_score"])

        # ==============================
        # 3. 自动判断客户优先级
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
        # 4. 保存结果
        # ==============================

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
            "可能需求": "\n".join(result["possible_needs"]),
            "开发策略": result["development_strategy"],

            "邮件主题": result["email_subject"],
            "邮件正文": result["email_body"]
        })

        print(
            f"分析完成：{customer['公司']} "
            f"| 评分：{score} "
            f"| 优先级：{priority}"
        )
        print()

    except Exception as e:

        print(f"分析失败：{customer['公司']}")
        print(f"错误：{e}")
        print()


# ==============================
# 5. 生成最终Excel
# ==============================

result_df = pd.DataFrame(results)

output_file = "day7_ai_lead_generation.xlsx"

result_df.to_excel(
    output_file,
    index=False
)


print("==============================")
print("       AI获客分析完成")
print("==============================")
print()
print(f"结果已保存：{output_file}")
print()
print("系统已经完成：")
print("1. Excel读取")
print("2. AI客户分析")
print("3. 客户评分")
print("4. 客户优先级")
print("5. 销售动作推荐")
print("6. 开发邮件生成")
print("7. Excel结果输出")
print("==============================")