
import pandas as pd
import matplotlib.pyplot as plt


def plot_weather_trend(df, output_path="weather_trend.png"):
    """
    绘制气象要素时间序列图。

    参数：
        df: 气象数据 DataFrame
        output_path: 图片保存路径
    """

    df = df.copy()

    # 时间字段转换
    df["time"] = pd.to_datetime(df["time"])

    # 按时间排序
    df = df.sort_values("time")

    # 创建画布
    fig, axes = plt.subplots(
        4,
        1,
        figsize=(12, 12),
        sharex=True
    )

    # 温度
    axes[0].plot(
        df["time"],
        df["temperature"],
        marker="o"
    )
    axes[0].set_ylabel("Temperature (°C)")
    axes[0].set_title("Temperature Trend")
    axes[0].grid(True)

    # 湿度
    axes[1].plot(
        df["time"],
        df["humidity"],
        marker="o"
    )
    axes[1].set_ylabel("Humidity (%)")
    axes[1].set_title("Humidity Trend")
    axes[1].grid(True)

    # 风速
    axes[2].plot(
        df["time"],
        df["wind_speed"],
        marker="o"
    )
    axes[2].set_ylabel("Wind Speed (m/s)")
    axes[2].set_title("Wind Speed Trend")
    axes[2].grid(True)

    # 降水
    axes[3].bar(
        df["time"],
        df["precipitation"],
        width=0.03
    )
    axes[3].set_ylabel("Precipitation (mm)")
    axes[3].set_title("Precipitation")
    axes[3].grid(True)

    axes[3].set_xlabel("Time")

    plt.tight_layout()

    # 保存图片
    plt.savefig(output_path, dpi=150)

    plt.show()

    print(f"图表已保存到：{output_path}")


if __name__ == "__main__":

    file_path = "weather_data.csv"

    try:
        df = pd.read_csv(file_path)

        plot_weather_trend(df)

    except FileNotFoundError:
        print(f"找不到文件：{file_path}")