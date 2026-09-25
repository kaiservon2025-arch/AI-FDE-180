import pandas as pd

# 读取 Day 5 的分析结果
df = pd.read_excel("day5_customer_analysis.xlsx")


# 根据客户评分判断优先级
def get_priority(score):

    if score >= 80:
        return "高"

    elif score >= 60:
        return "中"

    else:
        return "低"


# 根据优先级生成销售动作
def get_action(priority):

    if priority == "高":
        return "立即发送开发邮件"

    elif priority == "中":
        return "进一步收集客户信息，3天内跟进"

    else:
        return "暂缓开发"


# 生成优先级
df["优先级"] = df["客户评分"].apply(get_priority)

# 生成推荐动作
df["推荐动作"] = df["优先级"].apply(get_action)


# 按客户评分从高到低排序
df = df.sort_values(
    by=["客户评分"],
    ascending=False
)


# 保存结果
df.to_excel(
    "day6_customer_priority.xlsx",
    index=False
)


print("客户优先级分析完成")
print()

print(
    df[
        [
            "公司",
            "客户评分",
            "客户等级",
            "优先级",
            "推荐动作"
        ]
    ]
)

print()
print("生成文件：day6_customer_priority.xlsx")