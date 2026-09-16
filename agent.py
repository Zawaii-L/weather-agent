
from tools import TOOLS


def detect_tool(user_input):
    """
    根据用户输入，判断应该调用哪个工具。

    目前使用简单关键词规则。
    后面会替换成大模型 Tool Calling。
    """

    text = user_input.lower()

    if any(keyword in text for keyword in [
        "检查",
        "质量",
        "缺失",
        "重复",
        "异常",
        "数据质量",
    ]):
        return "check_quality"

    elif any(keyword in text for keyword in [
        "统计",
        "平均温度",
        "最高温度",
        "最低温度",
        "平均湿度",
        "最大风速",
        "累计降水",
        "日较差",
    ]):
        return "calculate_stats"

    elif any(keyword in text for keyword in [
        "画图",
        "趋势图",
        "可视化",
        "图表",
        "绘图",
    ]):
        return "plot_trend"

    return None


def run_tool(tool_name, file_path):
    """
    执行指定工具。
    """

    if tool_name not in TOOLS:
        return {
            "success": False,
            "message": f"不存在的工具：{tool_name}",
        }

    try:
        result = TOOLS[tool_name](file_path)

        return {
            "success": True,
            "tool": tool_name,
            "result": result,
        }

    except Exception as e:
        return {
            "success": False,
            "tool": tool_name,
            "message": str(e),
        }


def main():

    print("===================================")
    print("       气象数据智能 Agent")
    print("===================================")

    print("\n你可以直接输入自然语言，例如：")
    print("  帮我检查这份气象数据")
    print("  计算平均温度")
    print("  画一张趋势图")
    print("  输入 exit 退出")

    while True:

        user_input = input("\n请输入任务：").strip()

        if user_input.lower() == "exit":
            print("Agent 已退出。")
            break

        tool_name = detect_tool(user_input)

        if tool_name is None:
            print("暂时无法识别这个任务，请换一种说法。")
            continue

        print(f"\n识别到工具：{tool_name}")

        file_path = input(
            "请输入 CSV 文件路径（直接回车使用 weather_data.csv）："
        ).strip()

        if not file_path:
            file_path = "weather_data.csv"

        result = run_tool(tool_name, file_path)

        print("\n========== 工具执行结果 ==========")
        print(result)
        print("===================================")


if __name__ == "__main__":
    main()