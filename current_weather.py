import requests

from geocoding import resolve_city


def get_current_weather(city):
    """
    查询指定城市的实时天气。

    城市定位交给 geocoding.py。
    当前天气查询只负责根据经纬度请求天气数据。
    """

    city_result = resolve_city(city)

    if not city_result.get("success"):
        return {
            "success": False,
            "error": city_result.get(
                "error",
                "城市定位失败",
            ),
        }

    location = city_result["result"]

    latitude = location["latitude"]
    longitude = location["longitude"]

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
    )

    weather_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "timezone": "auto",
    }

    weather_response = requests.get(
        weather_url,
        params=weather_params,
        timeout=15,
    )

    weather_response.raise_for_status()

    weather_data = weather_response.json()

    current = weather_data.get("current")

    if not current:
        return {
            "success": False,
            "error": "天气接口没有返回当前天气数据。",
        }

    return {
        "success": True,
        "city": location.get("name", city),
        "region": location.get("region", ""),
        "country": location.get("country", ""),
        "latitude": latitude,
        "longitude": longitude,
        "time": current.get("time"),
        "temperature": current.get("temperature_2m"),
        "relative_humidity": current.get(
            "relative_humidity_2m"
        ),
        "apparent_temperature": current.get(
            "apparent_temperature"
        ),
        "precipitation": current.get(
            "precipitation"
        ),
        "wind_speed": current.get(
            "wind_speed_10m"
        ),
        "weather_code": current.get(
            "weather_code"
        ),
    }


if __name__ == "__main__":
    result = get_current_weather("珠海")
    print(result)