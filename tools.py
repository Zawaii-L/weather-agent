import pandas as pd

from current_weather import get_current_weather
from data_quality import (
    load_weather_data,
    check_missing_values,
    check_duplicate_records,
    check_duplicate_times,
    check_value_ranges,
    check_time_continuity,
)

from analysis_tools import calculate_weather_statistics

from visualization import plot_weather_trend


def load_data(file_path):
    """
    工具 1：读取气象 CSV 文件。
    """
    return load_weather_data(file_path)


def check_quality(file_path):
    """
    工具 2：执行气象数据质量检查。

    返回结构化结果，方便后续交给大模型。
    """

    df = load_weather_data(file_path)

    missing = check_missing_values(df)
    duplicate_records = check_duplicate_records(df)
    duplicate_times = check_duplicate_times(df)
    abnormal_values = check_value_ranges(df)
    abnormal_intervals = check_time_continuity(df)

    result = {
        "record_count": len(df),
        "missing_values": missing.to_dict(),
        "duplicate_record_count": len(duplicate_records),
        "duplicate_time_count": len(duplicate_times),
        "abnormal_values": {
            column: len(data)
            for column, data in abnormal_values.items()
        },
        "abnormal_time_interval_count": len(abnormal_intervals),
    }

    return result


def calculate_stats(file_path):
    """
    工具 3：计算气象统计指标。
    """

    df = load_weather_data(file_path)

    statistics = calculate_weather_statistics(df)

    # 将 Timestamp 转成字符串，方便后续 JSON 传递
    statistics["start_time"] = str(
        statistics["start_time"]
    )

    statistics["end_time"] = str(
        statistics["end_time"]
    )

    return statistics


def plot_trend(file_path, output_path="weather_trend.png"):
    """
    工具 4：生成气象趋势图。
    """

    df = load_weather_data(file_path)

    plot_weather_trend(
        df,
        output_path=output_path
    )

    return {
        "success": True,
        "output_path": output_path,
        "message": "气象趋势图生成成功。",
    }

# 工具注册表
TOOLS = {
    "check_quality": check_quality,
    "calculate_stats": calculate_stats,
    "plot_trend": plot_trend,
    "get_current_weather": get_current_weather,
}
if __name__ == "__main__":

    file_path = "weather_data.csv"

    print("\n===== 工具 1：读取数据 =====")
    df = load_data(file_path)
    print(f"读取成功，共 {len(df)} 条记录。")

    print("\n===== 工具 2：数据质量检查 =====")
    quality_result = check_quality(file_path)
    print(quality_result)

    print("\n===== 工具 3：统计分析 =====")
    statistics = calculate_stats(file_path)

    for key, value in statistics.items():
        print(f"{key}: {value}")

    print("\n===== 工具 4：生成趋势图 =====")
    plot_result = plot_trend(file_path)
    print(plot_result)