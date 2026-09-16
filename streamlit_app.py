import streamlit as st
import pandas as pd

from pathlib import Path
from datetime import date, timedelta

from tools import TOOLS
from historical_weather import fetch_historical_weather
from weather_code import weather_code_to_chinese


# ==================================================
# 页面基本设置
# ==================================================

st.set_page_config(
    page_title="气象智能助手",
    page_icon="🌤️",
    layout="wide"
)


# ==================================================
# 项目文件路径
# ==================================================

BASE_DIR = Path(__file__).resolve().parent

WEATHER_DATA_FILE = BASE_DIR / "weather_data.csv"


# ==================================================
# 数值格式化函数
# ==================================================

def format_decimal(value, digits=1):
    """
    将数值格式化为指定的小数位数。
    默认保留一位小数。
    """

    if value is None:
        return "--"

    try:

        return f"{float(value):.{digits}f}"

    except (TypeError, ValueError):

        return str(value)


def format_integer(value):
    """
    将数值格式化为整数。
    """

    if value is None:
        return "--"

    try:

        return f"{int(value)}"

    except (TypeError, ValueError):

        return str(value)


def round_dataframe_numbers(dataframe):
    """
    将 DataFrame 中所有数值列统一保留一位小数。
    """

    dataframe = dataframe.copy()

    numeric_columns = dataframe.select_dtypes(
        include="number"
    ).columns

    dataframe[numeric_columns] = dataframe[
        numeric_columns
    ].round(1)

    return dataframe


def get_result_value(result, *keys):
    """
    按顺序从结果字典中获取字段值。
    """

    for key in keys:

        if key in result and result[key] is not None:

            return result[key]

    return None


# ==================================================
# 页面标题
# ==================================================

st.title("🌤️ 气象智能助手")

st.caption(
    "公开气象数据采集 · 实时天气查询 · 气象数据分析 · 数据质量检查"
)


# ==================================================
# 侧边栏菜单
# ==================================================

with st.sidebar:

    st.header("功能菜单")

    selected_function = st.radio(
        "请选择功能",
        [
            "公开气象数据采集",
            "实时天气查询",
            "气象数据分析",
            "数据质量检查"
        ]
    )


# ==================================================
# 功能一：公开气象数据采集
# ==================================================

if selected_function == "公开气象数据采集":

    st.header("📥 公开气象数据采集")

    st.write(
        "输入城市和日期范围，系统将自动获取公开历史气象数据，"
        "并保存为项目中的 weather_data.csv 文件。"
    )

    st.info(
        "数据来源：Open-Meteo 公开气象接口。"
        "历史数据属于公开气象资料，"
        "不等同于气象站逐小时实测数据。"
    )

    city = st.text_input(
        "城市名称",
        value="澳门",
        placeholder="例如：澳门、珠海、深圳、广州"
    )

    yesterday = date.today() - timedelta(days=1)

    default_start_date = yesterday - timedelta(days=6)

    col1, col2 = st.columns(2)

    with col1:

        start_date = st.date_input(
            "开始日期",
            value=default_start_date
        )

    with col2:

        end_date = st.date_input(
            "结束日期",
            value=yesterday
        )

    fetch_button = st.button(
        "获取公开气象数据",
        type="primary"
    )

    if fetch_button:

        if not city.strip():

            st.warning("请输入城市名称。")

        elif start_date > end_date:

            st.error("开始日期不能晚于结束日期。")

        else:

            with st.spinner(
                "正在查询城市位置并获取公开气象数据……"
            ):

                result = fetch_historical_weather(
                    city=city.strip(),
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    output_file=str(WEATHER_DATA_FILE)
                )

            if result.get("success"):

                st.success(
                    "公开气象数据获取成功，已保存为 weather_data.csv。"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "城市",
                        result.get("city", city)
                    )

                with col2:

                    st.metric(
                        "数据记录数",
                        format_integer(
                            result.get("record_count")
                        )
                    )

                with col3:

                    st.metric(
                        "时区",
                        result.get("timezone", "--")
                    )

                st.write(
                    f"**地理坐标：** "
                    f"{format_decimal(result.get('latitude'), 4)}, "
                    f"{format_decimal(result.get('longitude'), 4)}"
                )

                st.write(
                    f"**数据日期范围：** "
                    f"{result.get('start_date', '--')} 至 "
                    f"{result.get('end_date', '--')}"
                )

                st.subheader("数据预览")

                dataframe = result.get("data")

                if dataframe is not None:

                    preview_dataframe = round_dataframe_numbers(
                        dataframe.head(20)
                    )

                    st.dataframe(
                        preview_dataframe,
                        use_container_width=True
                    )

                    st.caption(
                        "上方表格仅展示前20条记录，"
                        "数值统一保留一位小数。"
                    )

                    st.write(
                        f"**实际保存记录数：** "
                        f"{format_integer(len(dataframe))} 条"
                    )

                    if "time" in dataframe.columns:

                        time_values = pd.to_datetime(
                            dataframe["time"],
                            errors="coerce"
                        ).dropna()

                        if not time_values.empty:

                            st.write(
                                f"**实际数据开始时间：** "
                                f"{time_values.min()}"
                            )

                            st.write(
                                f"**实际数据结束时间：** "
                                f"{time_values.max()}"
                            )

                    # 每日数据记录数
                    if "time" in dataframe.columns:

                        daily_dataframe = dataframe.copy()

                        daily_dataframe["日期"] = (
                            pd.to_datetime(
                                daily_dataframe["time"],
                                errors="coerce"
                            ).dt.date
                        )

                        daily_summary = (
                            daily_dataframe
                            .groupby("日期")
                            .size()
                            .reset_index(name="记录数")
                        )

                        st.subheader("每日数据记录数")

                        st.dataframe(
                            daily_summary,
                            use_container_width=True
                        )

                    # 下载完整 CSV
                    csv_data = dataframe.to_csv(
                        index=False,
                        encoding="utf-8-sig"
                    )

                    st.download_button(
                        label="下载完整气象数据 CSV",
                        data=csv_data,
                        file_name="weather_data.csv",
                        mime="text/csv"
                    )

                st.info(
                    "完整数据已经保存。"
                    "你可以进入“气象数据分析”或“数据质量检查”继续处理。"
                )

            else:

                st.error(
                    result.get(
                        "error",
                        "公开气象数据获取失败。"
                    )
                )


# ==================================================
# 功能二：实时天气查询
# ==================================================

elif selected_function == "实时天气查询":

    st.header("📍 实时天气查询")

    st.write(
        "输入城市名称，系统将自动查询该城市的当前天气情况。"
    )

    city = st.text_input(
        "城市名称",
        value="澳门",
        placeholder="例如：澳门、珠海、深圳、广州"
    )

    query_button = st.button(
        "查询当前天气",
        type="primary"
    )

    if query_button:

        if not city.strip():

            st.warning("请输入城市名称。")

        else:

            with st.spinner("正在查询当前天气……"):

                try:

                    result = TOOLS["get_current_weather"](
                        city.strip()
                    )

                except Exception as error:

                    st.error(
                        "实时天气查询时发生错误。"
                    )

                    st.exception(error)

                    result = None

            if isinstance(result, dict) and result.get("success"):

                st.success("实时天气查询成功。")

                st.subheader(
                    f"📍 {result.get('city', city)} 当前天气"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.metric(
                        "当前温度",
                        f"{format_decimal(result.get('temperature'))} ℃"
                    )

                with col2:

                    st.metric(
                        "体感温度",
                        f"{format_decimal(result.get('apparent_temperature'))} ℃"
                    )

                with col3:

                    humidity = get_result_value(
                        result,
                        "relative_humidity",
                        "humidity"
                    )

                    st.metric(
                        "相对湿度",
                        f"{format_decimal(humidity)} %"
                    )

                with col4:

                    st.metric(
                        "风速",
                        f"{format_decimal(result.get('wind_speed'))} km/h"
                    )

                st.divider()

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**城市：** {result.get('city', '--')}"
                    )

                    st.write(
                        f"**地区：** {result.get('region', '--')}"
                    )

                    st.write(
                        f"**国家或地区：** {result.get('country', '--')}"
                    )

                with col2:

                    st.write(
                        f"**数据时间：** {result.get('time', '--')}"
                    )

                    st.write(
                        f"**当前降水：** "
                        f"{format_decimal(result.get('precipitation'))} mm"
                    )

                    weather_code = result.get(
                        "weather_code"
                    )

                    st.write(
                        f"**天气代码：** "
                        f"{weather_code if weather_code is not None else '--'}"
                    )

                    st.write(
                        f"**天气状况：** "
                        f"{weather_code_to_chinese(weather_code)}"
                    )

                with st.expander("查看完整天气数据"):

                    st.json(result)

            elif isinstance(result, dict):

                st.error(
                    result.get(
                        "error",
                        "实时天气查询失败，请稍后重试。"
                    )
                )

                with st.expander("查看完整返回结果"):

                    st.json(result)

            elif result is not None:

                st.error(
                    "天气查询返回的数据格式不正确。"
                )

                st.write(result)


# ==================================================
# 功能三：气象数据分析
# ==================================================

elif selected_function == "气象数据分析":

    st.header("📊 气象数据分析")

    st.write(
        "该模块分析通过公开气象接口获取并保存的 weather_data.csv 文件。"
    )

    analyze_button = st.button(
        "开始分析",
        type="primary"
    )

    if analyze_button:

        st.write(
            f"**数据文件路径：** `{WEATHER_DATA_FILE}`"
        )

        st.write(
            f"**文件是否存在：** `{WEATHER_DATA_FILE.exists()}`"
        )

        if not WEATHER_DATA_FILE.exists():

            st.error(
                "当前还没有 weather_data.csv。"
                "请先进入“公开气象数据采集”获取数据。"
            )

        else:

            with st.spinner("正在分析气象数据……"):

                try:

                    result = TOOLS["calculate_stats"](
                        str(WEATHER_DATA_FILE)
                    )

                    analysis_success = (
                        isinstance(result, dict)
                        and result.get("success", True)
                        and not result.get("error")
                    )

                    if analysis_success:

                        st.success(
                            "气象数据分析完成。"
                        )

                        st.subheader("主要统计指标")

                        col1, col2, col3 = st.columns(3)

                        record_count = get_result_value(
                            result,
                            "record_count",
                            "count"
                        )

                        temperature_mean = get_result_value(
                            result,
                            "temperature_mean",
                            "mean_temperature"
                        )

                        humidity_mean = get_result_value(
                            result,
                            "humidity_mean",
                            "mean_humidity"
                        )

                        with col1:

                            st.metric(
                                "记录数量",
                                format_integer(record_count)
                            )

                        with col2:

                            st.metric(
                                "平均温度",
                                f"{format_decimal(temperature_mean)} ℃"
                            )

                        with col3:

                            st.metric(
                                "平均湿度",
                                f"{format_decimal(humidity_mean)} %"
                            )

                        st.divider()

                        st.subheader("详细统计结果")

                        detail_col1, detail_col2 = st.columns(2)

                        with detail_col1:

                            st.write(
                                f"**数据开始时间：** "
                                f"{result.get('start_time', '--')}"
                            )

                            st.write(
                                f"**数据结束时间：** "
                                f"{result.get('end_time', '--')}"
                            )

                            st.write(
                                f"**最低温度：** "
                                f"{format_decimal(result.get('temperature_min'))} ℃"
                            )

                            st.write(
                                f"**最高温度：** "
                                f"{format_decimal(result.get('temperature_max'))} ℃"
                            )

                            st.write(
                                f"**平均温度：** "
                                f"{format_decimal(temperature_mean)} ℃"
                            )

                        with detail_col2:

                            st.write(
                                f"**平均湿度：** "
                                f"{format_decimal(humidity_mean)} %"
                            )

                            st.write(
                                f"**平均风速：** "
                                f"{format_decimal(result.get('wind_speed_mean'))} km/h"
                            )

                            st.write(
                                f"**最大风速：** "
                                f"{format_decimal(result.get('wind_speed_max'))} km/h"
                            )

                            st.write(
                                f"**累计降水量：** "
                                f"{format_decimal(result.get('precipitation_total'))} mm"
                            )

                            st.write(
                                f"**平均日温差：** "
                                f"{format_decimal(result.get('daily_temperature_range'))} ℃"
                            )

                        # ==================================================
                        # 天气状况统计
                        # ==================================================

                        st.subheader("天气状况统计")

                        try:

                            weather_dataframe = pd.read_csv(
                                WEATHER_DATA_FILE
                            )

                            if "weather_code" in weather_dataframe.columns:

                                weather_dataframe[
                                    "weather_description"
                                ] = weather_dataframe[
                                    "weather_code"
                                ].apply(
                                    weather_code_to_chinese
                                )

                                weather_summary = (
                                    weather_dataframe[
                                        "weather_description"
                                    ]
                                    .value_counts()
                                    .rename_axis("天气状况")
                                    .reset_index(
                                        name="出现次数"
                                    )
                                )

                                st.dataframe(
                                    weather_summary,
                                    use_container_width=True
                                )

                            else:

                                st.info(
                                    "当前数据中没有天气代码字段。"
                                )

                        except Exception as error:

                            st.warning(
                                f"天气状况统计展示失败：{error}"
                            )

                        # ==================================================
                        # 完整分析结果
                        # ==================================================

                        with st.expander("查看完整分析结果"):

                            display_result = result.copy()

                            decimal_fields = [
                                "temperature_mean",
                                "temperature_max",
                                "temperature_min",
                                "humidity_mean",
                                "wind_speed_mean",
                                "wind_speed_max",
                                "precipitation_total",
                                "daily_temperature_range"
                            ]

                            for field in decimal_fields:

                                if field in display_result:

                                    value = display_result[field]

                                    if isinstance(
                                        value,
                                        (int, float)
                                    ):

                                        display_result[field] = round(
                                            value,
                                            1
                                        )

                            st.json(display_result)

                    else:

                        st.error(
                            "气象数据分析失败："
                            + str(
                                result.get(
                                    "error",
                                    "工具没有返回具体错误信息。"
                                )
                            )
                        )

                        with st.expander("查看工具返回结果"):

                            st.json(result)

                except Exception as error:

                    st.error(
                        "气象数据分析时发生错误。"
                    )

                    st.exception(error)


# ==================================================
# 功能四：数据质量检查
# ==================================================

elif selected_function == "数据质量检查":

    st.header("🔍 数据质量检查")

    st.write(
        "检查气象数据中的缺失值、重复记录、异常数值和时间连续性。"
    )

    quality_button = st.button(
        "检查数据质量",
        type="primary"
    )

    if quality_button:

        st.write(
            f"**数据文件路径：** `{WEATHER_DATA_FILE}`"
        )

        st.write(
            f"**文件是否存在：** `{WEATHER_DATA_FILE.exists()}`"
        )

        if not WEATHER_DATA_FILE.exists():

            st.error(
                "当前还没有 weather_data.csv。"
                "请先进入“公开气象数据采集”获取数据。"
            )

        else:

            with st.spinner("正在检查气象数据质量……"):

                try:

                    result = TOOLS["check_quality"](
                        str(WEATHER_DATA_FILE)
                    )

                    quality_success = (
                        isinstance(result, dict)
                        and result.get("success", True)
                        and not result.get("error")
                    )

                    if quality_success:

                        st.success(
                            "数据质量检查完成。"
                        )

                        st.subheader("质量检查结果")

                        if isinstance(result, dict):

                            st.json(result)

                        else:

                            st.write(result)

                    else:

                        st.error(
                            "数据质量检查失败："
                            + str(
                                result.get(
                                    "error",
                                    "工具没有返回具体错误信息。"
                                )
                            )
                        )

                        with st.expander("查看工具返回结果"):

                            st.json(result)

                except Exception as error:

                    st.error(
                        "数据质量检查时发生错误。"
                    )

                    st.exception(error)