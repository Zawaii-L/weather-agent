#.\.venv\Scripts\python.exe -m pip install 库名称 #虚拟环境安装库

from tools import TOOLS


def run_tool(tool_name, file_path):
    """
    根据工具名称调用对应工具。
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
    print("      气象数据智能分析 Agent")
    print("===================================")

    print("\n可用工具：")
    print("1. check_quality    - 数据质量检查")
    print("2. calculate_stats  - 气象统计分析")
    print("3. plot_trend      - 生成趋势图")
    print("0. 退出")

    while True:

        choice = input("\n请选择工具：").strip()

        if choice == "0":
            print("Agent 已退出。")
            break

        if choice == "1":
            tool_name = "check_quality"

        elif choice == "2":
            tool_name = "calculate_stats"

        elif choice == "3":
            tool_name = "plot_trend"

        else:
            print("无效选择，请重新输入。")
            continue

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