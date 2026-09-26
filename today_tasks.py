import pandas as pd


def get_today_tasks(task_df):
    """
    从销售任务表中筛选今天需要优先处理的客户。
    """

    today_tasks = task_df[
        task_df["建议时间"] == "今天"
    ].copy()

    today_tasks = today_tasks.sort_values(
        by="客户评分",
        ascending=False
    )

    return today_tasks