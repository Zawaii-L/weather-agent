import requests
import pandas as pd

from pathlib import Path

from weather_code import weather_code_to_chinese


# ==================================================
# 公开气象接口地址
# ==================================================

GEOCODING_API_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)

HISTORICAL_API_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)


# ==================================================
# 城市位置查询
# ==================================================

def geocode_city(city: str):
    """
    根据城市名称查询经纬度。
    """

    if not city or not city.strip():

        return {
            "success": False,
            "error": "城市名称不能为空。"
        }

    params = {
        "name": city.strip(),
        "count": 1,
        "language": "zh",
        "format": "json"
    }

    try:

        response = requests.get(
            GEOCODING_API_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if not results:

            return {
                "success": False,
                "error": f"没有找到城市：{city}"
            }

        location = results[0]

        return {
            "success": True,
            "city": location.get("name", city),
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "country": location.get("country", ""),
            "country_code": location.get("country_code", ""),
            "admin1": location.get("admin1", ""),
            "timezone": location.get("timezone", "auto")
        }

    except requests.RequestException as error:

        return {
            "success": False,
            "error": f"城市位置查询失败：{error}"
        }

    except Exception as error:

        return {
            "success": False,
            "error": f"城市位置处理失败：{error}"
        }


# ==================================================
# 获取历史气象数据
# ==================================================

def fetch_historical_weather(
    city: str,
    start_date: str,
    end_date: str,
    output_file: str = "weather_data.csv"
):
    """
    从 Open-Meteo 公开历史气象接口获取小时数据，
    并保存为 CSV 文件。
    """

    if not start_date or not end_date:

        return {
            "success": False,
            "error": "开始日期和结束日期不能为空。"
        }

    if start_date > end_date:

        return {
            "success": False,
            "error": "开始日期不能晚于结束日期。"
        }

    # ==================================================
    # 第一步：查询城市经纬度
    # ==================================================

    location = geocode_city(city)

    if not location.get("success"):

        return location

    latitude = location["latitude"]
    longitude = location["longitude"]

    # ==================================================
    # 第二步：请求历史小时天气数据
    # ==================================================

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,

        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "surface_pressure",
            "cloud_cover"
        ]),

        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm"
    }

    try:

        response = requests.get(
            HISTORICAL_API_URL,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        if data.get("error"):

            return {
                "success": False,
                "error": data.get(
                    "reason",
                    "历史天气接口返回错误。"
                )
            }

        hourly_data = data.get("hourly")

        if not hourly_data:

            return {
                "success": False,
                "error": "接口没有返回小时气象数据。"
            }

        # ==================================================
        # 第三步：转换为 DataFrame
        # ==================================================

        dataframe = pd.DataFrame(hourly_data)

        if dataframe.empty:

            return {
                "success": False,
                "error": "获取到的气象数据为空。"
            }

        # ==================================================
        # 第四步：统一字段名称
        # ==================================================

        column_mapping = {
            "time": "time",
            "temperature_2m": "temperature",
            "relative_humidity_2m": "humidity",
            "apparent_temperature": "apparent_temperature",
            "precipitation": "precipitation",
            "weather_code": "weather_code",
            "wind_speed_10m": "wind_speed",
            "wind_direction_10m": "wind_direction",
            "wind_gusts_10m": "wind_gusts",
            "surface_pressure": "surface_pressure",
            "cloud_cover": "cloud_cover"
        }

        dataframe = dataframe.rename(
            columns=column_mapping
        )

        # ==================================================
        # 第五步：处理时间字段
        # ==================================================

        if "time" in dataframe.columns:

            dataframe["time"] = pd.to_datetime(
                dataframe["time"],
                errors="coerce"
            )

        # ==================================================
        # 第六步：增加中文天气描述
        # ==================================================

        if "weather_code" in dataframe.columns:

            dataframe["weather_description"] = (
                dataframe["weather_code"].apply(
                    weather_code_to_chinese
                )
            )

        # ==================================================
        # 第七步：调整字段顺序
        # ==================================================

        preferred_columns = [
            "time",
            "temperature",
            "apparent_temperature",
            "humidity",
            "precipitation",
            "weather_code",
            "weather_description",
            "wind_speed",
            "wind_direction",
            "wind_gusts",
            "surface_pressure",
            "cloud_cover"
        ]

        existing_columns = [
            column
            for column in preferred_columns
            if column in dataframe.columns
        ]

        remaining_columns = [
            column
            for column in dataframe.columns
            if column not in existing_columns
        ]

        dataframe = dataframe[
            existing_columns + remaining_columns
        ]

        # ==================================================
        # 第八步：所有数值统一保留一位小数
        # ==================================================

        numeric_columns = dataframe.select_dtypes(
            include="number"
        ).columns

        dataframe[numeric_columns] = dataframe[
            numeric_columns
        ].round(1)

        # ==================================================
        # 第九步：保存 CSV 文件
        # ==================================================

        output_path = Path(output_file)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        dataframe.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig"
        )

        # ==================================================
        # 第十步：返回结果
        # ==================================================

        return {
            "success": True,
            "city": location["city"],
            "country": location.get("country", ""),
            "latitude": round(
                float(latitude),
                4
            ),
            "longitude": round(
                float(longitude),
                4
            ),
            "timezone": data.get("timezone", ""),
            "start_date": start_date,
            "end_date": end_date,
            "record_count": len(dataframe),
            "output_file": str(output_path),
            "data": dataframe
        }

    except requests.RequestException as error:

        return {
            "success": False,
            "error": f"历史天气数据请求失败：{error}"
        }

    except Exception as error:

        return {
            "success": False,
            "error": f"历史天气数据处理失败：{error}"
        }