
import pandas as pd


def calculate_weather_statistics(df):
    """
    计算气象数据的基本统计指标。

    参数：
        df: 包含气象要素的 Pandas DataFrame

    返回：
        一个字典，保存统计结果
    """

    # 确保时间字段已经是 datetime
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])

    # 基本统计
    statistics = {
        "record_count": len(df),

        "start_time": df["time"].min(),
        "end_time": df["time"].max(),

        "temperature_mean": df["temperature"].mean(),
        "temperature_max": df["temperature"].max(),
        "temperature_min": df["temperature"].min(),

        "humidity_mean": df["humidity"].mean(),

        "wind_speed_mean": df["wind_speed"].mean(),
        "wind_speed_max": df["wind_speed"].max(),

        "precipitation_total": df["precipitation"].sum(),
    }

    # 温度日较差
    # 这里按日期分组，计算每天最高温 - 最低温
    daily_temperature = (
        df.groupby(df["time"].dt.date)["temperature"]
        .agg(["max", "min"])
    )

    daily_temperature["diurnal_range"] = (
        daily_temperature["max"]
        - daily_temperature["min"]
    )

    statistics["daily_temperature_range"] = (
        daily_temperature["diurnal_range"].mean()
    )

    return statistics


def print_weather_statistics(statistics):
    """
    将统计结果格式化输出。
    """

    print("\n========== 气象统计报告 ==========")

    print(f"记录数量：{statistics['record_count']}")
    print(f"开始时间：{statistics['start_time']}")
    print(f"结束时间：{statistics['end_time']}")

    print("\n【温度】")
    print(
        f"平均温度："
        f"{statistics['temperature_mean']:.2f} °C"
    )
    print(
        f"最高温度："
        f"{statistics['temperature_max']:.2f} °C"
    )
    print(
        f"最低温度："
        f"{statistics['temperature_min']:.2f} °C"
    )

    print("\n【湿度】")
    print(
        f"平均湿度："
        f"{statistics['humidity_mean']:.2f} %"
    )

    print("\n【风速】")
    print(
        f"平均风速："
        f"{statistics['wind_speed_mean']:.2f} m/s"
    )
    print(
        f"最大风速："
        f"{statistics['wind_speed_max']:.2f} m/s"
    )

    print("\n【降水】")
    print(
        f"累计降水："
        f"{statistics['precipitation_total']:.2f} mm"
    )

    print("\n【温度日较差】")
    print(
        f"平均日较差："
        f"{statistics['daily_temperature_range']:.2f} °C"
    )


if __name__ == "__main__":

    file_path = "weather_data.csv"

    try:
        df = pd.read_csv(file_path)

        df["time"] = pd.to_datetime(df["time"])

        statistics = calculate_weather_statistics(df)

        print_weather_statistics(statistics)

    except FileNotFoundError:
        print(f"找不到文件：{file_path}")

    except ValueError as e:
        print(f"数据处理错误：{e}")