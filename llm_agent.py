import json
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS


# ============================================================
# 1. 加载环境变量
# ============================================================

load_dotenv()


# ============================================================
# 2. 读取配置
# ============================================================

API_KEY = os.getenv("OPENAI_API_KEY")

BASE_URL = os.getenv(
    "OPENAI_BASE_URL",
    "https://open.bigmodel.cn/api/paas/v4",
)

MODEL_NAME = os.getenv(
    "OPENAI_MODEL",
    "glm-4.7-flash",
)


if not API_KEY:
    raise ValueError(
        "没有读取到 OPENAI_API_KEY，请检查项目目录下的 .env 文件。"
    )


client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)


# ============================================================
# 3. 工具说明
# ============================================================

TOOL_DESCRIPTIONS = {
    "check_quality": {
        "name": "check_quality",
        "description": (
            "检查本地 CSV 气象数据质量，包括缺失值、重复记录、"
            "重复时间、数值范围异常和时间间隔异常。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "本地 CSV 文件路径",
                }
            },
            "required": [],
        },
    },
    "calculate_stats": {
        "name": "calculate_stats",
        "description": (
            "统计本地 CSV 气象数据，包括记录数量、起止时间、"
            "平均温度、最高温度、最低温度、平均湿度、"
            "平均风速、最大风速、累计降水和平均日较差。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "本地 CSV 文件路径",
                }
            },
            "required": [],
        },
    },
    "plot_trend": {
        "name": "plot_trend",
        "description": (
            "根据本地 CSV 气象数据绘制温度、湿度、风速和降水趋势图，"
            "并保存为 PNG 图片。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "本地 CSV 文件路径",
                },
                "output_path": {
                    "type": "string",
                    "description": "输出图片路径",
                },
            },
            "required": [],
        },
    },
}


# ============================================================
# 4. 系统提示词
# ============================================================

SYSTEM_PROMPT = """
你是一个气象数据分析 Agent。

你可以使用以下工具：

1. check_quality
   检查本地 CSV 气象数据质量。

2. calculate_stats
   统计本地 CSV 气象数据。

3. plot_trend
   绘制本地 CSV 气象趋势图。

注意：

- 实时天气查询已经由 Python 程序直接处理，不需要调用大模型工具。
- check_quality、calculate_stats、plot_trend 只用于本地 CSV 文件。
- 不要把本地历史 CSV 数据描述为实时天气。
- 回答时请使用中文。
"""


# ============================================================
# 5. 识别用户是否在查询实时天气
# ============================================================

def is_current_weather_question(question):
    """
    判断用户是否在询问实时天气。
    """

    weather_keywords = [
        "天气",
        "气温",
        "温度",
        "下雨",
        "降雨",
        "湿度",
        "风速",
        "实时",
        "现在",
        "当前",
        "今日",
        "今天",
    ]

    return any(
        keyword in question
        for keyword in weather_keywords
    )


# ============================================================
# 6. 从问题中提取城市
# ============================================================

def extract_city(question):
    """
    从用户问题中提取城市名称。

    先清理常见天气查询词，
    再提取剩余的地点名称。
    """

    question = question.strip()

    remove_words = [
        "请查询",
        "帮我查询",
        "帮我查一下",
        "查询",
        "查一下",
        "查看",
        "现在",
        "当前",
        "实时",
        "今天",
        "今日",
        "天气",
        "气温",
        "温度",
        "怎么样",
        "如何",
        "是多少",
        "的",
    ]

    city = question

    for word in remove_words:
        city = city.replace(word, "")

    city = city.strip()

    # 去除常见标点
    city = city.replace("？", "")
    city = city.replace("?", "")
    city = city.replace("。", "")
    city = city.replace("，", "")
    city = city.replace(",", "")
    city = city.strip()

    if not city:
        return "澳门"

    return city·


# ============================================================
# 7. 格式化实时天气结果
# ============================================================

def format_current_weather(result):
    """
    将实时天气 API 返回的数据转换成中文。
    """

    if not result.get("success"):
        return (
            "实时天气查询失败："
            + str(result.get("error", "未知错误"))
        )

    city = result.get("city", "")
    region = result.get("region", "")
    country = result.get("country", "")
    time_text = result.get("time", "")

    temperature = result.get("temperature")
    apparent_temperature = result.get("apparent_temperature")
    humidity = result.get("relative_humidity")
    precipitation = result.get("precipitation")
    wind_speed = result.get("wind_speed")
    weather_code = result.get("weather_code")

    location_text = city

    if region:
        location_text += f"（{region}）"

    if country:
        location_text += f"，{country}"

    weather_description = weather_code_to_text(weather_code)

    lines = [
        f"📍 城市：{location_text}",
        f"🕒 数据时间：{time_text}",
        f"🌡️ 当前温度：{temperature} °C",
        f"🌡️ 体感温度：{apparent_temperature} °C",
        f"💧 相对湿度：{humidity} %",
        f"🌧️ 当前降水：{precipitation} mm",
        f"💨 风速：{wind_speed} km/h",
        f"☁️ 天气状况：{weather_description}",
    ]

    return "\n".join(lines)


# ============================================================
# 8. 将 WMO 天气代码转换为中文
# ============================================================

def weather_code_to_text(code):
    """
    Open-Meteo 使用 WMO 天气代码。
    """

    weather_code_map = {
        0: "晴",
        1: "大致晴朗",
        2: "部分多云",
        3: "阴",
        45: "雾",
        48: "雾凇",
        51: "小毛毛雨",
        53: "中等毛毛雨",
        55: "较强毛毛雨",
        56: "冻毛毛雨",
        57: "较强冻毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "冻雨",
        67: "强冻雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "小阵雨",
        81: "中等阵雨",
        82: "强阵雨",
        85: "小阵雪",
        86: "强阵雪",
        95: "雷雨",
        96: "雷雨并伴有小冰雹",
        99: "雷雨并伴有大冰雹",
    }

    return weather_code_map.get(
        code,
        f"未知天气代码：{code}",
    )


# ============================================================
# 9. 调用大模型
# ============================================================

def call_llm(messages):
    """
    调用大模型。

    遇到限流时最多重试 3 次。
    """

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.2,
            )

            return response

        except Exception as error:
            error_text = str(error)

            print("\n大模型调用失败：")
            print(error_text)

            if "429" in error_text or "1305" in error_text:
                if attempt < max_retries - 1:
                    wait_seconds = 5 * (attempt + 1)

                    print(
                        f"\n接口暂时限流，"
                        f"{wait_seconds} 秒后进行第 "
                        f"{attempt + 2} 次重试..."
                    )

                    time.sleep(wait_seconds)
                    continue

            return None


# ============================================================
# 10. 提取工具调用
# ============================================================

def extract_tool_call(message):
    """
    从模型消息中提取工具名称和参数。
    """

    if getattr(message, "tool_calls", None):
        tool_call = message.tool_calls[0]

        tool_name = tool_call.function.name
        raw_arguments = tool_call.function.arguments

        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            arguments = {}

        return tool_name, arguments

    content = message.content or ""

    if "<tool_call>" not in content:
        return None, None

    try:
        start_index = content.find("<tool_call>")
        end_index = content.find("</tool_call>")

        if end_index == -1:
            return None, None

        tool_text = content[
            start_index + len("<tool_call>"):end_index
        ].strip()

        try:
            tool_data = json.loads(tool_text)

            tool_name = tool_data.get("name")
            arguments = tool_data.get("arguments", {})

            return tool_name, arguments

        except json.JSONDecodeError:
            pass

    except Exception:
        return None, None

    return None, None


# ============================================================
# 11. 清理工具参数
# ============================================================

def clean_tool_arguments(tool_name, arguments):
    """
    严格按照工具类型清理参数。
    """

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        arguments = {}

    if tool_name == "check_quality":
        return {
            "file_path": arguments.get(
                "file_path",
                "weather_data.csv",
            )
        }

    if tool_name == "calculate_stats":
        return {
            "file_path": arguments.get(
                "file_path",
                "weather_data.csv",
            )
        }

    if tool_name == "plot_trend":
        return {
            "file_path": arguments.get(
                "file_path",
                "weather_data.csv",
            ),
            "output_path": arguments.get(
                "output_path",
                "weather_trend.png",
            ),
        }

    return arguments


# ============================================================
# 12. 执行本地工具
# ============================================================

def execute_tool(tool_name, arguments):
    """
    执行本地 CSV 工具。
    """

    if tool_name not in TOOLS:
        return {
            "success": False,
            "error": f"不存在的工具：{tool_name}",
        }

    try:
        clean_arguments = clean_tool_arguments(
            tool_name,
            arguments,
        )

        print("\n清理后的工具参数：")
        print(clean_arguments)

        result = TOOLS[tool_name](**clean_arguments)

        return {
            "success": True,
            "tool": tool_name,
            "result": result,
        }

    except Exception as error:
        return {
            "success": False,
            "tool": tool_name,
            "error": str(error),
        }


# ============================================================
# 13. 格式化本地工具结果
# ============================================================

def format_tool_result(tool_name, tool_result):
    """
    将本地工具结果转换成文本。
    """

    if not tool_result.get("success"):
        return (
            f"工具 {tool_name} 执行失败。\n"
            f"错误信息：{tool_result.get('error', '未知错误')}"
        )

    result = tool_result.get("result")

    try:
        result_text = json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    except Exception:
        result_text = str(result)

    return (
        f"工具 {tool_name} 执行成功。\n"
        f"工具返回结果：\n"
        f"{result_text}"
    )


# ============================================================
# 14. 实时天气查询
# ============================================================

def handle_current_weather(question):
    """
    不经过大模型，直接调用实时天气工具。
    """

    city = extract_city(question)

    print("\n正在查询实时天气：")
    print(city)

    try:
        result = TOOLS["get_current_weather"](city)

        print("\n实时天气查询完成。")

        return format_current_weather(result)

    except Exception as error:
        return (
            "实时天气查询失败。\n"
            f"错误信息：{error}"
        )


# ============================================================
# 15. Agent 主流程
# ============================================================

def ask_agent(user_question):
    """
    Agent 主流程。
    """

    # --------------------------------------------------------
    # 第一优先级：实时天气直接查询
    # --------------------------------------------------------

    if is_current_weather_question(user_question):
        return handle_current_weather(user_question)

    # --------------------------------------------------------
    # 第二优先级：本地 CSV 分析交给大模型
    # --------------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_question,
        },
    ]

    response = call_llm(messages)

    if response is None:
        return (
            "当前大模型接口暂时无法访问，可能是模型访问量过大或接口限流。\n"
            "实时天气查询不受此影响，可以直接输入“澳门天气”进行查询。\n"
            "本次本地 CSV 分析暂时无法交给大模型处理，请稍后再试。"
        )

    message = response.choices[0].message

    tool_name, arguments = extract_tool_call(message)

    if not tool_name:
        return message.content or "模型没有返回有效回答。"

    print("\n大模型选择工具：")
    print(tool_name)

    print("\n大模型原始参数：")
    print(arguments)

    tool_result = execute_tool(
        tool_name,
        arguments,
    )

    print("\n工具执行状态：")
    print(tool_result.get("success"))

    messages.append(
        {
            "role": "assistant",
            "content": message.content or "",
        }
    )

    messages.append(
        {
            "role": "user",
            "content": format_tool_result(
                tool_name,
                tool_result,
            ),
        }
    )

    final_response = call_llm(messages)

    if final_response is None:
        return (
            f"工具 {tool_name} 已经执行完成，但大模型当前限流，"
            "暂时无法整理成自然语言回答。\n\n"
            f"工具原始结果：\n"
            f"{format_tool_result(tool_name, tool_result)}"
        )

    final_content = final_response.choices[0].message.content

    if not final_content:
        return "工具已经执行，但模型没有生成文字回答。"

    return final_content


# ============================================================
# 16. 命令行入口
# ============================================================

def main():
    print("=" * 60)
    print("气象数据 Agent")
    print("=" * 60)

    print("\n当前模型：")
    print(MODEL_NAME)

    print("\n可用功能：")
    print("1. 查询实时天气，例如：澳门天气")
    print("2. 检查本地 CSV 数据质量")
    print("3. 统计本地气象数据")
    print("4. 绘制气象趋势图")

    print("\n输入 exit、0 或 退出，可以结束程序。")

    while True:
        print("\n" + "-" * 60)

        user_question = input("请输入你的问题：").strip()

        if user_question in [
            "exit",
            "Exit",
            "EXIT",
            "0",
            "退出",
        ]:
            print("程序已退出。")
            break

        if not user_question:
            print("问题不能为空，请重新输入。")
            continue

        try:
            answer = ask_agent(user_question)

            print("\n========== Agent 回答 ==========")
            print(answer)

        except Exception as error:
            print("\n程序执行失败：")
            print(str(error))


# ============================================================
# 17. 启动程序
# ============================================================

if __name__ == "__main__":
    main()