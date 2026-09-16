
import pandas as pd


def load_weather_data(file_path):
    """
    读取气象 CSV 文件，并进行基础时间处理。
    """

    # 1. 读取 CSV
    df = pd.read_csv(file_path)

    # 2. 检查必要字段
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

    # 3. 将时间字段转换为 datetime
    df["time"] = pd.to_datetime(df["time"])

    # 4. 按时间排序
    df = df.sort_values("time").reset_index(drop=True)

    return df


def describe_weather_data(df):
    """
    输出气象数据的基本概况。
    """

    print("\n===== 数据概况 =====")
    print(f"记录数量：{len(df)}")
    print(f"字段数量：{len(df.columns)}")

    print(f"开始时间：{df['time'].min()}")
    print(f"结束时间：{df['time'].max()}")

    print("\n字段信息：")
    print(df.dtypes)

    print("\n前 5 条记录：")
    print(df.head())


def calculate_basic_statistics(df):
    """
    计算气象要素的基本统计量。
    """

    print("\n===== 气象统计 =====")

    print(f"平均温度：{df['temperature'].mean():.2f} °C")
    print(f"最高温度：{df['temperature'].max():.2f} °C")
    print(f"最低温度：{df['temperature'].min():.2f} °C")

    print(f"平均湿度：{df['humidity'].mean():.2f} %")
    print(f"最大风速：{df['wind_speed'].max():.2f} m/s")

    print(
        f"累计降水：{df['precipitation'].sum():.2f} mm"
    )


if __name__ == "__main__":

    file_path = "weather_data.csv"

    try:
        weather_df = load_weather_data(file_path)

        describe_weather_data(weather_df)

        calculate_basic_statistics(weather_df)

    except FileNotFoundError:
        print(f"找不到文件：{file_path}")

    except ValueError as e:
        print(f"数据处理错误：{e}")