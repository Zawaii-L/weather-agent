
import requests


def get_location(city):
    """
    根据城市名称获取经纬度。
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 1,
        "language": "zh",
        "format": "json",
    }

    response = requests.get(url, params=params, timeout=10)

    # 如果 HTTP 状态码不是 200，抛出异常
    response.raise_for_status()

    data = response.json()

    if "results" not in data or not data["results"]:
        raise ValueError(f"没有找到城市：{city}")

    location = data["results"][0]

    return {
        "name": location["name"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "country": location.get("country", ""),
    }


def get_weather_forecast(latitude, longitude):
    """
    根据经纬度获取未来 3 天的天气预报。
    """
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "weather_code",
        ],
        "forecast_days": 3,
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)

    response.raise_for_status()

    data = response.json()

    return data


def weather_code_to_text(code):
    """
    将 WMO 天气代码转换成简单的中文描述。
    """
    weather_codes = {
        0: "晴",
        1: "大致晴",
        2: "局部多云",
        3: "阴",
        45: "雾",
        48: "雾凇",
        51: "小毛毛雨",
        53: "中毛毛雨",
        55: "大毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        80: "小阵雨",
        81: "中阵雨",
        82: "强阵雨",
        95: "雷雨",
        96: "雷雨伴有小冰雹",
        99: "雷雨伴有大冰雹",
    }

    return weather_codes.get(code, f"未知天气代码（{code}）")


def print_forecast(city):
    """
    查询城市并打印未来 3 天天气。
    """
    location = get_location(city)

    print(f"\n地点：{location['name']}")
    print(f"国家/地区：{location['country']}")
    print(
        f"坐标：纬度 {location['latitude']}，"
        f"经度 {location['longitude']}"
    )

    weather_data = get_weather_forecast(
        location["latitude"],
        location["longitude"],
    )

    daily = weather_data["daily"]

    print("\n未来 3 天天气预报：")

    for i in range(len(daily["time"])):
        date = daily["time"][i]
        max_temp = daily["temperature_2m_max"][i]
        min_temp = daily["temperature_2m_min"][i]
        weather_code = daily["weather_code"][i]

        weather_text = weather_code_to_text(weather_code)

        print(
            f"{date} | {weather_text} | "
            f"最高温 {max_temp}°C | 最低温 {min_temp}°C"
        )


if __name__ == "__main__":
    city = input("请输入城市名称：").strip()

    if not city:
        print("城市名称不能为空。")
    else:
        try:
            print_forecast(city)
        except requests.RequestException as e:
            print(f"网络请求失败：{e}")
        except (KeyError, ValueError) as e:
            print(f"数据处理失败：{e}")