import requests
import pandas as pd

from weather_code import weather_code_to_chinese


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_city_coordinates(city):
    """
    根据城市名称获取经纬度。
    """
    params = {
        "name": city,
        "count": 1,
        "language": "zh",
        "format": "json"
    }

    response = requests.get(
        GEOCODING_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results")

    if not results:
        return None

    location = results[0]

    return {
        "name": location.get("name", city),
        "country": location.get("country", ""),
        "admin1": location.get("admin1", ""),
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": location.get("timezone", "auto")
    }


def get_weather_forecast(city, forecast_days=3):
    """
    获取指定城市未来天气预报。

    参数：
        city：城市名称，例如珠海、深圳、澳门
        forecast_days：预报天数，范围为1到16天

    返回：
        {
            "location": 城市信息,
            "daily": 每日天气DataFrame,
            "hourly": 每小时天气DataFrame
        }
    """
    if not city or not str(city).strip():
        return None

    try:
        forecast_days = int(forecast_days)
    except (TypeError, ValueError):
        forecast_days = 3

    forecast_days = max(1, min(forecast_days, 16))

    location = get_city_coordinates(city)

    if location is None:
        return None

    latitude = location["latitude"]
    longitude = location["longitude"]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto",
        "forecast_days": forecast_days,

        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "precipitation_probability_max",
            "precipitation_sum",
            "rain_sum",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "sunrise",
            "sunset"
        ]),

        "hourly": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "cloud_cover"
        ])
    }

    response = requests.get(
        FORECAST_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    daily_data = data.get("daily", {})
    hourly_data = data.get("hourly", {})

    # =========================
    # 整理每日天气数据
    # =========================

    daily_df = pd.DataFrame({
        "日期": daily_data.get("time", []),
        "天气代码": daily_data.get("weather_code", []),
        "最高温度": daily_data.get("temperature_2m_max", []),
        "最低温度": daily_data.get("temperature_2m_min", []),
        "最高体感温度": daily_data.get("apparent_temperature_max", []),
        "最低体感温度": daily_data.get("apparent_temperature_min", []),
        "最高降水概率": daily_data.get("precipitation_probability_max", []),
        "预计降水量": daily_data.get("precipitation_sum", []),
        "预计降雨量": daily_data.get("rain_sum", []),
        "最大风速": daily_data.get("wind_speed_10m_max", []),
        "最大阵风": daily_data.get("wind_gusts_10m_max", []),
        "日出时间": daily_data.get("sunrise", []),
        "日落时间": daily_data.get("sunset", [])
    })

    if not daily_df.empty:
        daily_df["天气状况"] = daily_df["天气代码"].apply(
            weather_code_to_chinese
        )

        daily_df = daily_df[
            [
                "日期",
                "天气代码",
                "天气状况",
                "最高温度",
                "最低温度",
                "最高体感温度",
                "最低体感温度",
                "最高降水概率",
                "预计降水量",
                "预计降雨量",
                "最大风速",
                "最大阵风",
                "日出时间",
                "日落时间"
            ]
        ]

        numeric_columns = [
            "最高温度",
            "最低温度",
            "最高体感温度",
            "最低体感温度",
            "最高降水概率",
            "预计降水量",
            "预计降雨量",
            "最大风速",
            "最大阵风"
        ]

        for column in numeric_columns:
            if column in daily_df.columns:
                daily_df[column] = pd.to_numeric(
                    daily_df[column],
                    errors="coerce"
                ).round(1)

    # =========================
    # 整理每小时天气数据
    # =========================

    hourly_df = pd.DataFrame({
        "时间": hourly_data.get("time", []),
        "温度": hourly_data.get("temperature_2m", []),
        "体感温度": hourly_data.get("apparent_temperature", []),
        "相对湿度": hourly_data.get("relative_humidity_2m", []),
        "降水概率": hourly_data.get("precipitation_probability", []),
        "降水量": hourly_data.get("precipitation", []),
        "天气代码": hourly_data.get("weather_code", []),
        "风速": hourly_data.get("wind_speed_10m", []),
        "风向": hourly_data.get("wind_direction_10m", []),
        "阵风": hourly_data.get("wind_gusts_10m", []),
        "云量": hourly_data.get("cloud_cover", [])
    })

    if not hourly_df.empty:
        hourly_df["天气状况"] = hourly_df["天气代码"].apply(
            weather_code_to_chinese
        )

        hourly_df = hourly_df[
            [
                "时间",
                "温度",
                "体感温度",
                "相对湿度",
                "降水概率",
                "降水量",
                "天气代码",
                "天气状况",
                "风速",
                "风向",
                "阵风",
                "云量"
            ]
        ]

        numeric_columns = [
            "温度",
            "体感温度",
            "相对湿度",
            "降水概率",
            "降水量",
            "风速",
            "风向",
            "阵风",
            "云量"
        ]

        for column in numeric_columns:
            if column in hourly_df.columns:
                hourly_df[column] = pd.to_numeric(
                    hourly_df[column],
                    errors="coerce"
                ).round(1)

    return {
        "location": location,
        "daily": daily_df,
        "hourly": hourly_df
    }


if __name__ == "__main__":
    result = get_weather_forecast("珠海", 3)

    if result is None:
        print("没有获取到天气数据。")
    else:
        print("城市信息：")
        print(result["location"])

        print("\n未来天气：")
        print(result["daily"])

        print("\n每小时天气：")
        print(result["hourly"].head(10))