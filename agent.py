import json
import os
import re
import uuid
from datetime import datetime

from openai import OpenAI

from forecast_weather import get_weather_forecast


def get_client():
    """
    创建大模型客户端。

    本地开发时读取 .env；
    Streamlit Cloud 部署时读取 Secrets。
    """
    api_key = os.getenv("OPENAI_API_KEY")

    base_url = os.getenv(
        "OPENAI_BASE_URL",
        "https://open.bigmodel.cn/api/paas/v4"
    )

    model = os.getenv(
        "OPENAI_MODEL",
        "glm-4.7-flash"
    )

    if not api_key:
        raise ValueError(
            "没有找到 OPENAI_API_KEY，请检查 .env 或 Streamlit Secrets。"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    return client, model


def get_forecast_tool(city: str, days: int = 3):
    """
    调用未来天气预报工具。
    返回适合交给大模型分析的 JSON 数据。
    """
    days = max(1, min(int(days), 16))

    result = get_weather_forecast(
        city=city,
        forecast_days=days
    )

    if not result:
        return {
            "success": False,
            "message": f"没有找到城市“{city}”的天气数据。"
        }

    daily_df = result.get("daily")
    hourly_df = result.get("hourly")

    daily_data = []
    hourly_data = []

    if daily_df is not None:
        daily_data = daily_df.to_dict(orient="records")

    if hourly_df is not None:
        # 防止一次传给模型的数据太多
        hourly_data = hourly_df.head(72).to_dict(orient="records")

    return {
        "success": True,
        "city": city,
        "daily": daily_data,
        "hourly": hourly_data
    }


def build_tools():
    """
    定义大模型可以调用的工具。
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather_forecast",
                "description": (
                    "查询指定城市未来几天的天气预报。"
                    "可以获取温度、降水概率、降水量、风速、阵风、"
                    "天气状况、日出和日落时间等信息。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "需要查询的城市，例如珠海、深圳、澳门。"
                        },
                        "days": {
                            "type": "integer",
                            "description": "需要查询的未来天数，范围为1到16天。",
                            "minimum": 1,
                            "maximum": 16
                        }
                    },
                    "required": ["city", "days"]
                }
            }
        }
    ]


def run_tool(tool_name, arguments):
    """
    根据大模型的工具调用结果，实际执行工具。
    """
    if tool_name == "get_weather_forecast":
        return get_forecast_tool(
            city=arguments["city"],
            days=arguments.get("days", 3)
        )

    return {
        "success": False,
        "message": f"未找到工具：{tool_name}"
    }


def parse_xml_tool_calls(content):
    """
    兼容部分模型返回的 XML 风格工具调用。

    例如：

    <tool_call>
    <get_weather_forecast>
    <arg_key>city</arg_key>
    <arg_value>珠海</arg_value>
    <arg_key>days</arg_key>
    <arg_value>1</arg_value>
    </get_weather_forecast>
    </tool_call>

    返回标准化后的工具调用列表。
    """
    if not content or "<tool_call>" not in content:
        return []

    tool_calls = []

    # 匹配每一个工具调用
    pattern = re.compile(
        r"<([a-zA-Z_][a-zA-Z0-9_]*)>\s*"
        r"(.*?)"
        r"</\1>",
        re.DOTALL
    )

    # 只处理 tool_call 标签内部
    match = re.search(
        r"<tool_call>\s*(.*?)\s*</tool_call>",
        content,
        re.DOTALL
    )

    if not match:
        return []

    tool_content = match.group(1)

    for tool_match in pattern.finditer(tool_content):
        tool_name = tool_match.group(1)
        arguments_text = tool_match.group(2)

        # 解析 arg_key / arg_value
        keys = re.findall(
            r"<arg_key>\s*(.*?)\s*</arg_key>",
            arguments_text,
            re.DOTALL
        )

        values = re.findall(
            r"<arg_value>\s*(.*?)\s*</arg_value>",
            arguments_text,
            re.DOTALL
        )

        arguments = {}

        for key, value in zip(keys, values):
            key = key.strip()
            value = value.strip()

            # 尝试把数字转换为整数
            if key == "days":
                try:
                    value = int(value)
                except ValueError:
                    value = 3

            arguments[key] = value

        tool_calls.append(
            {
                "id": f"xml_call_{uuid.uuid4().hex[:8]}",
                "name": tool_name,
                "arguments": arguments
            }
        )

    return tool_calls


def get_standard_tool_calls(assistant_message):
    """
    读取 OpenAI SDK 标准格式的工具调用。
    """
    if not assistant_message.tool_calls:
        return []

    tool_calls = []

    for tool_call in assistant_message.tool_calls:
        try:
            arguments = json.loads(
                tool_call.function.arguments
            )
        except (json.JSONDecodeError, TypeError):
            arguments = {}

        tool_calls.append(
            {
                "id": tool_call.id,
                "name": tool_call.function.name,
                "arguments": arguments
            }
        )

    return tool_calls


def ask_weather_agent(question: str):
    """
    气象 Agent 主入口。

    工作流程：

    1. 接收自然语言问题；
    2. 让大模型判断是否需要调用天气工具；
    3. 支持标准 tool_calls 和 XML 工具调用；
    4. 执行工具；
    5. 将工具结果交给大模型；
    6. 生成最终中文回答。
    """
    if not question or not question.strip():
        return "请输入你的气象问题。"

    client, model = get_client()
    tools = build_tools()

    today = datetime.now().strftime("%Y-%m-%d")

    system_prompt = f"""
你是一个专业、谨慎、清晰的中文气象智能助手。

当前日期是：{today}

你的任务：
1. 理解用户的自然语言气象问题；
2. 如果问题涉及具体城市的当前天气或未来天气，必须调用天气预报工具；
3. 如果用户没有明确说明查询几天，根据问题自动判断：
   - “今天”查询1天；
   - “明天”查询1天；
   - “后天”查询2天；
   - “未来几天”默认查询3天；
   - “未来一周”查询7天；
4. 回答时使用中文；
5. 所有温度、风速、降水量等数值尽量保留一位小数；
6. 不要编造天气数据；
7. 如果工具没有返回数据，要如实说明；
8. 对无人机飞行、户外活动、钓鱼等问题，只能根据天气数据进行风险提示，
   不能把天气预报说成绝对安全或绝对危险；
9. 如果用户询问气象基础知识，可以直接解释，不一定调用工具；
10. 回答要有条理，必要时使用项目符号或表格；
11. 如果已经获得天气工具返回的数据，直接根据数据回答用户，
    不要再次输出工具调用代码；
12. 不要向用户展示 <tool_call>、<arg_key>、<arg_value> 等内部工具调用标签。
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # 最多允许连续处理3轮工具调用
    for _ in range(3):

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2
        )

        assistant_message = response.choices[0].message

        # 读取标准工具调用
        standard_tool_calls = get_standard_tool_calls(
            assistant_message
        )

        # 如果标准工具调用为空，再尝试解析 XML 工具调用
        xml_tool_calls = []

        if not standard_tool_calls:
            xml_tool_calls = parse_xml_tool_calls(
                assistant_message.content
            )

        tool_calls = standard_tool_calls or xml_tool_calls

        # 如果没有工具调用，直接返回普通回答
        if not tool_calls:
            return assistant_message.content or "暂时没有生成有效回答。"

        # 记录助手消息
        if standard_tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in assistant_message.tool_calls
                    ]
                }
            )
        else:
            # XML 工具调用不是标准格式，
            # 这里保留原始内容，方便兼容部分模型
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content
                }
            )

        # 执行所有工具调用
        for tool_call in tool_calls:

            tool_name = tool_call["name"]
            arguments = tool_call["arguments"]

            tool_result = run_tool(
                tool_name=tool_name,
                arguments=arguments
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                        default=str
                    )
                }
            )

    return "工具调用次数超过限制，请稍后重试。"