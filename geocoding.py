import json
import re
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent
CITY_FILE = BASE_DIR / "cities.json"


def load_city_database():
    """
    读取本地城市坐标数据库。
    """

    if not CITY_FILE.exists():
        return {}

    with open(
        CITY_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def normalize_city_name(city):
    """
    标准化城市名称。
    """

    city = city.strip()

    city = city.replace(
        "中国广东省",
        "",
    )

    city = city.replace(
        "广东省",
        "",
    )

    city = city.replace(
        "中国",
        "",
    )

    city = city.replace(
        "天气",
        "",
    )

    city = city.replace(
        "市",
        "",
    )

    city = city.strip()

    return city


def find_city_from_local_database(city):
    """
    优先从本地城市数据库中查找。
    """

    database = load_city_database()

    normalized_city = normalize_city_name(city)

    # 直接匹配
    if city in database:
        return database[city]

    # 标准化后匹配
    for key, value in database.items():
        normalized_key = normalize_city_name(key)

        if normalized_key == normalized_city:
            return value

    return None


def search_city_online(city):
    """
    当本地数据库没有对应城市时，
    使用 Open-Meteo 地理编码接口。
    """

    geocoding_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
    )

    params = {
        "name": city,
        "count": 10,
        "language": "zh",
        "format": "json",
    }

    response = requests.get(
        geocoding_url,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results", [])

    if not results:
        return None

    # 优先选择中国境内结果
    china_results = []

    for item in results:
        country_code = item.get(
            "country_code",
            "",
        )

        country = item.get(
            "country",
            "",
        )

        if country_code == "CN" or country in [
            "中国",
            "China",
        ]:
            china_results.append(item)

    if china_results:
        results = china_results

    # 优先选择有行政区信息的结果
    results.sort(
        key=lambda item: (
            item.get("admin1", "") == "",
            item.get("name", "") != city,
        )
    )

    item = results[0]

    return {
        "name": item.get("name", city),
        "region": item.get("admin1", ""),
        "country": item.get("country", ""),
        "latitude": item["latitude"],
        "longitude": item["longitude"],
    }


def resolve_city(city):
    """
    统一城市解析入口：

    1. 优先本地数据库；
    2. 本地没有时调用在线地理编码；
    3. 找不到时返回错误。
    """

    local_result = find_city_from_local_database(city)

    if local_result:
        return {
            "success": True,
            "source": "local",
            "result": local_result,
        }

    online_result = search_city_online(city)

    if online_result:
        return {
            "success": True,
            "source": "online",
            "result": online_result,
        }

    return {
        "success": False,
        "error": f"无法定位城市：{city}",
    }


if __name__ == "__main__":
    test_cities = [
        "澳门",
        "珠海",
        "深圳",
        "北京",
        "新加坡",
    ]

    for city in test_cities:
        print("\n查询城市：", city)
        print(resolve_city(city))