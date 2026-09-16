import os
from io import BytesIO

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from agent import ask_weather_agent
from forecast_weather import get_weather_forecast


# =========================
# 加载环境变量
# =========================

load_dotenv()


# =========================
# 页面设置
# =========================

st.set_page_config(
    page_title="翀舟气象智能助手",
    page_icon="🌦️",
    layout="wide"
)


# =========================
# 页面标题
# =========================

st.title("🌦️ 翀舟气象智能助手")

st.caption(
    "基于大语言模型、气象数据接口和数据分析工具的自然语言气象 Agent"
)


# =========================
# 侧边栏功能菜单
# =========================

st.sidebar.title("功能菜单")

page = st.sidebar.radio(
    "请选择功能",
    [
        "自然语言气象助手",
        "公开气象数据采集",
        "未来天气预报",
        "实时天气查询",
        "气象数据分析",
        "数据质量检查"
    ]
)


# =========================================================
# 功能一：自然语言气象助手
# =========================================================

if page == "自然语言气象助手":

    st.header("自然语言气象助手")

    st.markdown(
        """
你可以直接用自然语言提问，Agent 会根据问题自动判断是否需要查询天气数据。

例如：

- 珠海明天的天气怎么样？
- 深圳未来三天会下雨吗？
- 珠海明天适合进行无人机培训吗？
- 帮我分析未来三天的风速和降水风险。
- 澳门这几天的最高温度是多少？
- 什么是相对湿度？
- 雷暴天气为什么不适合无人机飞行？
"""
    )

    st.divider()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 清空聊天记录按钮
    col1, col2 = st.columns([1, 5])

    with col1:
        if st.button("清空对话"):
            st.session_state.messages = []
            st.rerun()

    # 显示历史聊天记录
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 自然语言输入框
    question = st.chat_input(
        "请输入你的气象问题……"
    )

    if question:

        # 保存用户问题
        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        # 显示用户问题
        with st.chat_message("user"):
            st.markdown(question)

        # 调用 Agent
        with st.chat_message("assistant"):

            with st.spinner("正在理解问题并查询气象数据……"):

                try:
                    answer = ask_weather_agent(question)

                    if not answer:
                        answer = "暂时没有生成有效回答，请换一种方式提问。"

                    st.markdown(answer)

                except Exception as e:
                    answer = f"运行过程中出现错误：{e}"
                    st.error(answer)

        # 保存 Agent 回答
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


# =========================================================
# 功能二：公开气象数据采集
# =========================================================

elif page == "公开气象数据采集":

    st.header("公开气象数据采集")

    st.write(
        "通过 Open-Meteo 公开接口获取指定城市的历史或公开气象数据。"
    )

    city = st.text_input(
        "请输入城市名称",
        value="珠海",
        key="collect_city"
    )

    start_date = st.date_input(
        "开始日期",
        key="collect_start_date"
    )

    end_date = st.date_input(
        "结束日期",
        key="collect_end_date"
    )

    if st.button("开始采集数据"):

        if start_date > end_date:
            st.error("开始日期不能晚于结束日期。")
        else:

            with st.spinner("正在采集公开气象数据……"):

                try:
                    geocoding_response = requests.get(
                        "https://geocoding-api.open-meteo.com/v1/search",
                        params={
                            "name": city,
                            "count": 1,
                            "language": "zh",
                            "format": "json"
                        },
                        timeout=20
                    )

                    geocoding_response.raise_for_status()

                    geocoding_data = geocoding_response.json()
                    results = geocoding_data.get("results", [])

                    if not results:
                        st.error(f"没有找到城市：{city}")
                    else:

                        location = results[0]

                        latitude = location["latitude"]
                        longitude = location["longitude"]

                        archive_url = (
                            "https://archive-api.open-meteo.com/v1/archive"
                        )

                        response = requests.get(
                            archive_url,
                            params={
                                "latitude": latitude,
                                "longitude": longitude,
                                "start_date": str(start_date),
                                "end_date": str(end_date),
                                "timezone": "auto",
                                "daily": ",".join(
                                    [
                                        "temperature_2m_max",
                                        "temperature_2m_min",
                                        "temperature_2m_mean",
                                        "precipitation_sum",
                                        "rain_sum",
                                        "snowfall_sum",
                                        "wind_speed_10m_max",
                                        "wind_gusts_10m_max",
                                        "relative_humidity_2m_mean",
                                        "sunrise",
                                        "sunset"
                                    ]
                                )
                            },
                            timeout=30
                        )

                        response.raise_for_status()

                        weather_data = response.json()
                        daily_data = weather_data.get("daily", {})

                        df = pd.DataFrame(
                            {
                                "日期": daily_data.get("time", []),
                                "最高温度": daily_data.get(
                                    "temperature_2m_max", []
                                ),
                                "最低温度": daily_data.get(
                                    "temperature_2m_min", []
                                ),
                                "平均温度": daily_data.get(
                                    "temperature_2m_mean", []
                                ),
                                "降水量": daily_data.get(
                                    "precipitation_sum", []
                                ),
                                "降雨量": daily_data.get(
                                    "rain_sum", []
                                ),
                                "降雪量": daily_data.get(
                                    "snowfall_sum", []
                                ),
                                "最大风速": daily_data.get(
                                    "wind_speed_10m_max", []
                                ),
                                "最大阵风": daily_data.get(
                                    "wind_gusts_10m_max", []
                                ),
                                "平均相对湿度": daily_data.get(
                                    "relative_humidity_2m_mean", []
                                ),
                                "日出时间": daily_data.get(
                                    "sunrise", []
                                ),
                                "日落时间": daily_data.get(
                                    "sunset", []
                                )
                            }
                        )

                        numeric_columns = [
                            "最高温度",
                            "最低温度",
                            "平均温度",
                            "降水量",
                            "降雨量",
                            "降雪量",
                            "最大风速",
                            "最大阵风",
                            "平均相对湿度"
                        ]

                        for column in numeric_columns:
                            if column in df.columns:
                                df[column] = pd.to_numeric(
                                    df[column],
                                    errors="coerce"
                                ).round(1)

                        st.success(
                            f"成功获取 {len(df)} 条气象数据。"
                        )

                        st.dataframe(
                            df,
                            use_container_width=True
                        )

                        csv_data = df.to_csv(
                            index=False,
                            encoding="utf-8-sig"
                        )

                        st.download_button(
                            label="下载 CSV 文件",
                            data=csv_data,
                            file_name=(
                                f"{city}_{start_date}_{end_date}_气象数据.csv"
                            ),
                            mime="text/csv"
                        )

                except Exception as e:
                    st.error(f"数据采集失败：{e}")


# =========================================================
# 功能三：未来天气预报
# =========================================================

elif page == "未来天气预报":

    st.header("未来天气预报")

    city = st.text_input(
        "请输入城市名称",
        value="珠海",
        key="forecast_city"
    )

    forecast_days = st.slider(
        "预报天数",
        min_value=1,
        max_value=16,
        value=3,
        step=1
    )

    if st.button("查询未来天气"):

        with st.spinner("正在获取天气预报……"):

            try:
                result = get_weather_forecast(
                    city=city,
                    forecast_days=forecast_days
                )

                if result is None:
                    st.error(
                        f"没有找到城市“{city}”的天气数据。"
                    )
                else:

                    location = result["location"]
                    daily_df = result["daily"]
                    hourly_df = result["hourly"]

                    st.success(
                        f"已获取 {location.get('name', city)} "
                        f"未来 {forecast_days} 天的天气预报。"
                    )

                    st.subheader("城市信息")

                    st.write(
                        f"城市：{location.get('name', city)}"
                    )

                    if location.get("country"):
                        st.write(
                            f"国家或地区：{location['country']}"
                        )

                    if location.get("admin1"):
                        st.write(
                            f"行政区域：{location['admin1']}"
                        )

                    st.write(
                        f"纬度：{float(location['latitude']):.1f}"
                    )

                    st.write(
                        f"经度：{float(location['longitude']):.1f}"
                    )

                    st.divider()

                    st.subheader("每日天气预报")

                    st.dataframe(
                        daily_df,
                        use_container_width=True
                    )

                    st.subheader("每小时天气预报")

                    st.dataframe(
                        hourly_df,
                        use_container_width=True
                    )

                    daily_csv = daily_df.to_csv(
                        index=False,
                        encoding="utf-8-sig"
                    )

                    hourly_csv = hourly_df.to_csv(
                        index=False,
                        encoding="utf-8-sig"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.download_button(
                            label="下载每日预报 CSV",
                            data=daily_csv,
                            file_name=f"{city}_每日天气预报.csv",
                            mime="text/csv"
                        )

                    with col2:
                        st.download_button(
                            label="下载每小时预报 CSV",
                            data=hourly_csv,
                            file_name=f"{city}_每小时天气预报.csv",
                            mime="text/csv"
                        )

            except Exception as e:
                st.error(f"天气预报获取失败：{e}")


# =========================================================
# 功能四：实时天气查询
# =========================================================

elif page == "实时天气查询":

    st.header("实时天气查询")

    city = st.text_input(
        "请输入城市名称",
        value="珠海",
        key="current_city"
    )

    if st.button("查询实时天气"):

        with st.spinner("正在获取实时天气……"):

            try:
                geocoding_response = requests.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": city,
                        "count": 1,
                        "language": "zh",
                        "format": "json"
                    },
                    timeout=20
                )

                geocoding_response.raise_for_status()

                geocoding_data = geocoding_response.json()
                results = geocoding_data.get("results", [])

                if not results:
                    st.error(f"没有找到城市：{city}")
                else:

                    location = results[0]

                    latitude = location["latitude"]
                    longitude = location["longitude"]

                    response = requests.get(
                        "https://api.open-meteo.com/v1/forecast",
                        params={
                            "latitude": latitude,
                            "longitude": longitude,
                            "current": ",".join(
                                [
                                    "temperature_2m",
                                    "relative_humidity_2m",
                                    "apparent_temperature",
                                    "is_day",
                                    "precipitation",
                                    "rain",
                                    "weather_code",
                                    "cloud_cover",
                                    "pressure_msl",
                                    "surface_pressure",
                                    "wind_speed_10m",
                                    "wind_direction_10m",
                                    "wind_gusts_10m"
                                ]
                            ),
                            "timezone": "auto"
                        },
                        timeout=30
                    )

                    response.raise_for_status()

                    data = response.json()
                    current = data.get("current", {})

                    st.success(
                        f"已获取 {location.get('name', city)} 的实时天气。"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "当前温度",
                            f"{float(current.get('temperature_2m', 0)):.1f} °C"
                        )

                    with col2:
                        st.metric(
                            "体感温度",
                            f"{float(current.get('apparent_temperature', 0)):.1f} °C"
                        )

                    with col3:
                        st.metric(
                            "相对湿度",
                            f"{float(current.get('relative_humidity_2m', 0)):.1f} %"
                        )

                    current_table = pd.DataFrame(
                        {
                            "项目": [
                                "降水量",
                                "降雨量",
                                "天气代码",
                                "云量",
                                "海平面气压",
                                "地面气压",
                                "风速",
                                "风向",
                                "阵风"
                            ],
                            "数值": [
                                f"{float(current.get('precipitation', 0)):.1f}",
                                f"{float(current.get('rain', 0)):.1f}",
                                current.get("weather_code", "未知"),
                                f"{float(current.get('cloud_cover', 0)):.1f}",
                                f"{float(current.get('pressure_msl', 0)):.1f}",
                                f"{float(current.get('surface_pressure', 0)):.1f}",
                                f"{float(current.get('wind_speed_10m', 0)):.1f}",
                                f"{float(current.get('wind_direction_10m', 0)):.1f}",
                                f"{float(current.get('wind_gusts_10m', 0)):.1f}"
                            ]
                        }
                    )

                    st.dataframe(
                        current_table,
                        use_container_width=True,
                        hide_index=True
                    )

            except Exception as e:
                st.error(f"实时天气查询失败：{e}")


# =========================================================
# 功能五：气象数据分析
# =========================================================

elif page == "气象数据分析":

    st.header("气象数据分析")

    uploaded_file = st.file_uploader(
        "请上传 CSV 气象数据文件",
        type=["csv"]
    )

    if uploaded_file is not None:

        try:
            df = pd.read_csv(uploaded_file)

            st.subheader("数据预览")

            st.dataframe(
                df.head(20),
                use_container_width=True
            )

            st.subheader("数据基本信息")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "数据行数",
                    f"{len(df):.1f}"
                )

            with col2:
                st.metric(
                    "数据列数",
                    f"{len(df.columns):.1f}"
                )

            with col3:
                st.metric(
                    "缺失值总数",
                    f"{int(df.isnull().sum().sum()):.1f}"
                )

            numeric_df = df.select_dtypes(
                include="number"
            )

            if not numeric_df.empty:

                st.subheader("数值型数据统计")

                st.dataframe(
                    numeric_df.describe().round(1),
                    use_container_width=True
                )

                selected_column = st.selectbox(
                    "请选择需要绘图的数值列",
                    numeric_df.columns
                )

                st.subheader(
                    f"{selected_column} 变化趋势"
                )

                st.line_chart(
                    numeric_df[selected_column]
                )

            else:
                st.info(
                    "当前文件没有检测到数值型字段。"
                )

        except Exception as e:
            st.error(f"数据分析失败：{e}")


# =========================================================
# 功能六：数据质量检查
# =========================================================

elif page == "数据质量检查":

    st.header("数据质量检查")

    uploaded_file = st.file_uploader(
        "请上传需要检查的 CSV 文件",
        type=["csv"],
        key="quality_file"
    )

    if uploaded_file is not None:

        try:
            df = pd.read_csv(uploaded_file)

            st.subheader("数据预览")

            st.dataframe(
                df.head(20),
                use_container_width=True
            )

            missing_values = df.isnull().sum()
            duplicate_count = int(df.duplicated().sum())

            quality_df = pd.DataFrame(
                {
                    "字段名称": df.columns,
                    "数据类型": [
                        str(df[column].dtype)
                        for column in df.columns
                    ],
                    "缺失值数量": [
                        int(missing_values[column])
                        for column in df.columns
                    ],
                    "缺失值比例": [
                        round(
                            float(missing_values[column] / len(df) * 100),
                            1
                        ) if len(df) > 0 else 0.0
                        for column in df.columns
                    ],
                    "唯一值数量": [
                        int(df[column].nunique())
                        for column in df.columns
                    ]
                }
            )

            st.subheader("字段质量检查结果")

            st.dataframe(
                quality_df,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("整体质量概况")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "数据行数",
                    f"{len(df):.1f}"
                )

            with col2:
                st.metric(
                    "重复行数量",
                    f"{duplicate_count:.1f}"
                )

            with col3:
                st.metric(
                    "缺失值总数",
                    f"{int(missing_values.sum()):.1f}"
                )

            if duplicate_count > 0:
                st.warning(
                    f"检测到 {duplicate_count} 行重复数据。"
                )
            else:
                st.success(
                    "没有检测到重复行。"
                )

            if int(missing_values.sum()) > 0:
                st.warning(
                    "数据中存在缺失值，建议进一步处理。"
                )
            else:
                st.success(
                    "没有检测到缺失值。"
                )

        except Exception as e:
            st.error(f"数据质量检查失败：{e}")