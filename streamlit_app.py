import streamlit as st
from pathlib import Path

from tools import TOOLS


# ==================================================
# 页面基本设置
# ==================================================

st.set_page_config(
    page_title="气象智能 Agent",
    page_icon="🌤️",
    layout="wide"
)


# ==================================================
# 项目文件路径
# ==================================================

# 当前 streamlit_app.py 所在目录
BASE_DIR = Path(__file__).resolve().parent

# 气象数据文件
WEATHER_DATA_FILE = BASE_DIR / "weather_data.csv"


# ==================================================
# 页面标题
# ==================================================

st.title("🌤️ 气象智能 Agent")

st.caption(
    "实时天气查询 · 气象数据分析 · 数据质量检查"
)


# ==================================================
# 侧边栏菜单
# ==================================================

with st.sidebar:

    st.header("功能菜单")

    selected_function = st.radio(
        "请选择功能",
        [
            "实时天气查询",
            "气象数据分析",
            "数据质量检查"
        ]
    )


# ==================================================
# 功能一：实时天气查询
# ==================================================

if selected_function == "实时天气查询":

    st.header("📍 实时天气查询")

    city = st.text_input(
        "请输入城市名称",
        value="澳门",
        placeholder="例如：澳门、珠海、深圳、广州"
    )

    query_button = st.button(
        "查询当前天气",
        type="primary"
    )

    if query_button:

        if not city.strip():

            st.warning("请输入城市名称")

        else:

            with st.spinner("正在查询天气数据……"):

                try:

                    result = TOOLS["get_current_weather"](
                        city.strip()
                    )

                except Exception as error:

                    st.error("天气查询时发生错误：")

                    st.exception(error)

                    result = None

            if isinstance(result, dict) and result.get("success"):

                st.success("天气查询成功")

                st.subheader(
                    f"📍 {result.get('city', city)} 当前天气"
                )

                # 第一行：核心天气指标
                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.metric(
                        "当前温度",
                        f"{result.get('temperature', '--')} ℃"
                    )

                with col2:

                    st.metric(
                        "体感温度",
                        f"{result.get('apparent_temperature', '--')} ℃"
                    )

                with col3:

                    st.metric(
                        "相对湿度",
                        f"{result.get('relative_humidity', '--')} %"
                    )

                with col4:

                    st.metric(
                        "风速",
                        f"{result.get('wind_speed', '--')} km/h"
                    )

                st.divider()

                # 第二行：其他天气信息
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
                        f"{result.get('precipitation', '--')} mm"
                    )

                    st.write(
                        f"**天气状况：** "
                        f"{result.get('weather_code', '--')}"
                    )

                # 展示完整返回结果，便于调试
                with st.expander("查看完整天气数据"):

                    st.json(result)

            elif isinstance(result, dict):

                st.error(
                    result.get(
                        "error",
                        "天气查询失败，请稍后重试。"
                    )
                )

                with st.expander("查看完整返回结果"):

                    st.json(result)

            elif result is not None:

                st.error("天气查询返回的数据格式不正确。")

                st.write(result)


# ==================================================
# 功能二：气象数据分析
# ==================================================

elif selected_function == "气象数据分析":

    st.header("📊 气象数据分析")

    st.write(
        "该模块分析项目目录中的 weather_data.csv 文件。"
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
                "找不到 weather_data.csv。"
                "请检查该文件是否已经上传到 GitHub，"
                "并且文件名是否完全一致。"
            )

        else:

            with st.spinner("正在分析本地气象数据……"):

                try:

                    result = TOOLS["calculate_stats"](
                        str(WEATHER_DATA_FILE)
                    )

                    st.write("**工具返回结果：**")

                    if isinstance(result, dict):

                        st.json(result)

                    else:

                        st.write(result)

                    if isinstance(result, dict) and result.get("success"):

                        st.success("数据分析完成")

                        st.subheader("统计结果")

                        # 尝试读取常见统计指标
                        col1, col2, col3 = st.columns(3)

                        with col1:

                            st.metric(
                                "记录数",
                                result.get(
                                    "record_count",
                                    result.get("count", "--")
                                )
                            )

                        with col2:

                            st.metric(
                                "平均温度",
                                f"{result.get('mean_temperature', '--')} ℃"
                            )

                        with col3:

                            st.metric(
                                "平均湿度",
                                f"{result.get('mean_humidity', '--')} %"
                            )

                    elif isinstance(result, dict):

                        st.error(
                            "数据分析失败："
                            + str(
                                result.get(
                                    "error",
                                    "工具没有返回具体错误信息。"
                                )
                            )
                        )

                    else:

                        st.error(
                            "数据分析失败：工具返回的数据格式不是字典。"
                        )

                except Exception as error:

                    st.error("数据分析时发生错误：")

                    st.exception(error)


# ==================================================
# 功能三：数据质量检查
# ==================================================

elif selected_function == "数据质量检查":

    st.header("🔍 数据质量检查")

    st.write(
        "检查缺失值、重复记录、异常数值和时间连续性。"
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
                "找不到 weather_data.csv。"
                "请检查该文件是否已经上传到 GitHub，"
                "并且文件名是否完全一致。"
            )

        else:

            with st.spinner("正在检查数据质量……"):

                try:

                    result = TOOLS["check_quality"](
                        str(WEATHER_DATA_FILE)
                    )

                    st.write("**质量检查返回结果：**")

                    if isinstance(result, dict):

                        st.json(result)

                    else:

                        st.write(result)

                    if isinstance(result, dict) and result.get("success"):

                        st.success("质量检查完成")

                    elif isinstance(result, dict):

                        st.error(
                            "数据质量检查失败："
                            + str(
                                result.get(
                                    "error",
                                    "工具没有返回具体错误信息。"
                                )
                            )
                        )

                    else:

                        st.error(
                            "数据质量检查失败："
                            "工具返回的数据格式不是字典。"
                        )

                except Exception as error:

                    st.error("数据质量检查时发生错误：")

                    st.exception(error)