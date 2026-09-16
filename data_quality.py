
import pandas as pd


def load_weather_data(file_path):
    """
    读取气象 CSV，并处理时间字段。
    """
    df = pd.read_csv(file_path)

    required_columns = [
        "time",
        "temperature",
        "humidity",
        "wind_speed",
        "precipitation",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"缺少必要字段：{missing_columns}"
        )

    df["time"] = pd.to_datetime(
        df["time"],
        errors="coerce"
    )

    return df


def check_missing_values(df):
    """
    检查各字段缺失值数量。
    """
    missing_counts = df.isnull().sum()

    return missing_counts[
        missing_counts > 0
    ]


def check_duplicate_records(df):
    """
    检查完全重复的记录。
    """
    duplicate_rows = df[
        df.duplicated(keep=False)
    ]

    return duplicate_rows


def check_duplicate_times(df):
    """
    检查重复的观测时间。
    """
    duplicate_time_rows = df[
        df["time"].duplicated(keep=False)
    ]

    return duplicate_time_rows


def check_value_ranges(df):
    """
    检查气象要素是否超出设定范围。

    注意：
    这里是质量检查阈值，不代表所有地区、
    所有气象站的绝对物理极限。
    """

    rules = {
        "temperature": (-50, 60),
        "humidity": (0, 100),
        "wind_speed": (0, 100),
        "precipitation": (0, 1000),
    }

    abnormal_records = {}

    for column, (min_value, max_value) in rules.items():

        abnormal = df[
            (df[column] < min_value)
            | (df[column] > max_value)
        ]

        if not abnormal.empty:
            abnormal_records[column] = abnormal

    return abnormal_records


def check_time_continuity(df):
    """
    检查时间序列中是否存在时间间隔异常。

    本练习假设：
    数据应该每小时记录一次。
    """

    sorted_df = df.sort_values("time").copy()

    time_diff = sorted_df["time"].diff()

    expected_interval = pd.Timedelta(hours=1)

    abnormal_intervals = sorted_df[
        time_diff.notna()
        & (time_diff != expected_interval)
    ].copy()

    abnormal_intervals["time_diff"] = time_diff[
        abnormal_intervals.index
    ]

    return abnormal_intervals


def run_quality_check(file_path):
    """
    执行完整的数据质量检查。
    """

    df = load_weather_data(file_path)

    print("\n========== 数据质量检查报告 ==========")

    print(f"\n记录数量：{len(df)}")
    print(f"字段数量：{len(df.columns)}")

    # 1. 缺失值
    print("\n【1. 缺失值检查】")
    missing = check_missing_values(df)

    if missing.empty:
        print("未发现缺失值。")
    else:
        print(missing)

    # 2. 完全重复记录
    print("\n【2. 完全重复记录检查】")
    duplicate_records = check_duplicate_records(df)

    if duplicate_records.empty:
        print("未发现完全重复记录。")
    else:
        print(duplicate_records)

    # 3. 重复时间
    print("\n【3. 重复时间检查】")
    duplicate_times = check_duplicate_times(df)

    if duplicate_times.empty:
        print("未发现重复时间。")
    else:
        print(duplicate_times)

    # 4. 数值范围
    print("\n【4. 数值范围检查】")
    abnormal_records = check_value_ranges(df)

    if not abnormal_records:
        print("未发现超出设定范围的数值。")
    else:
        for column, abnormal_df in abnormal_records.items():
            print(f"\n字段：{column}")
            print(abnormal_df)

    # 5. 时间连续性
    print("\n【5. 时间连续性检查】")
    abnormal_intervals = check_time_continuity(df)

    if abnormal_intervals.empty:
        print("未发现时间间隔异常。")
    else:
        print(abnormal_intervals)

    print("\n========== 检查完成 ==========")


if __name__ == "__main__":

    file_path = "quality_test_data.csv"

    try:
        run_quality_check(file_path)

    except FileNotFoundError:
        print(f"找不到文件：{file_path}")

    except ValueError as e:
        print(f"数据处理错误：{e}")