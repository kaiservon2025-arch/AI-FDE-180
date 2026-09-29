def get_dashboard_stats(result_df, task_df):
    """
    生成AI销售工作台需要的核心统计数据。
    """

    total_customers = len(result_df)

    high_priority = (
        result_df["客户优先级"] == "高"
    ).sum()

    medium_priority = (
        result_df["客户优先级"] == "中"
    ).sum()

    low_priority = (
        result_df["客户优先级"] == "低"
    ).sum()

    today_tasks = (
        task_df["建议时间"] == "今天"
    ).sum()

    if len(result_df) > 0:
        average_score = round(
            result_df["客户评分"].mean(),
            1
        )
    else:
        average_score = 0

    return {
        "客户总数": total_customers,
        "高优先级客户": high_priority,
        "中优先级客户": medium_priority,
        "低优先级客户": low_priority,
        "今日任务": today_tasks,
        "平均评分": average_score
    }