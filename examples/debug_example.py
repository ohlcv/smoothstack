#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器内调试示例程序

演示如何配置和使用容器内调试功能
"""

import os
import sys
import time
import logging
import argparse
import random
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("debug_example")


class Calculator:
    """简单计算器类，用于演示调试功能"""

    def __init__(self, precision: int = 2):
        """初始化计算器"""
        self.precision = precision
        self.history = []
        logger.info(f"计算器初始化，精度设置为 {precision} 位小数")

    def add(self, a: float, b: float) -> float:
        """加法运算"""
        result = round(a + b, self.precision)
        self.history.append(f"{a} + {b} = {result}")
        logger.debug(f"执行加法: {a} + {b} = {result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """减法运算"""
        result = round(a - b, self.precision)
        self.history.append(f"{a} - {b} = {result}")
        logger.debug(f"执行减法: {a} - {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """乘法运算"""
        result = round(a * b, self.precision)
        self.history.append(f"{a} * {b} = {result}")
        logger.debug(f"执行乘法: {a} * {b} = {result}")
        return result

    def divide(self, a: float, b: float) -> float:
        """除法运算"""
        if b == 0:
            # 这里故意添加一个bug，用于演示调试
            # 正确的做法应该是抛出异常
            logger.error("除数不能为零!")
            result = float("inf")  # 使用无穷大表示错误
        else:
            result = round(a / b, self.precision)

        self.history.append(f"{a} / {b} = {result}")
        logger.debug(f"执行除法: {a} / {b} = {result}")
        return result

    def power(self, a: float, b: float) -> float:
        """幂运算"""
        # 另一个潜在的bug: 对于非常大的数可能导致溢出
        result = round(a**b, self.precision)
        self.history.append(f"{a} ^ {b} = {result}")
        logger.debug(f"执行幂运算: {a} ^ {b} = {result}")
        return result

    def get_history(self) -> list:
        """获取计算历史"""
        return self.history


class ComplexCalculation:
    """复杂计算类，用于演示调试更复杂的逻辑"""

    def __init__(self, calculator: Calculator):
        """初始化复杂计算类"""
        self.calculator = calculator
        self.results = []

    def fibonacci(self, n: int) -> int:
        """计算斐波那契数列第n项"""
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        else:
            return self.fibonacci(n - 1) + self.fibonacci(n - 2)

    def calculate_series(self, start: float, end: float, step: float) -> list:
        """计算一系列数值的和、差、积、商"""
        results = []
        current = start

        while current <= end:
            next_val = current + step
            if next_val > end:
                break

            # 使用计算器执行各种运算
            sum_result = self.calculator.add(current, next_val)
            diff_result = self.calculator.subtract(current, next_val)
            prod_result = self.calculator.multiply(current, next_val)

            # 故意在这里加入除法计算，可能会遇到除零错误
            div_result = self.calculator.divide(current, next_val - current)

            results.append(
                {
                    "current": current,
                    "next": next_val,
                    "sum": sum_result,
                    "difference": diff_result,
                    "product": prod_result,
                    "quotient": div_result,
                }
            )

            current = next_val

        self.results = results
        return results

    def analyze_results(self) -> dict:
        """分析计算结果"""
        if not self.results:
            return {"error": "没有可分析的结果"}

        sums = [r["sum"] for r in self.results]
        differences = [r["difference"] for r in self.results]
        products = [r["product"] for r in self.results]
        quotients = [r["quotient"] for r in self.results]

        analysis = {
            "sum_avg": sum(sums) / len(sums),
            "diff_avg": sum(differences) / len(differences),
            "prod_avg": sum(products) / len(products),
            "quot_avg": sum(quotients) / len(quotients),
            "count": len(self.results),
        }

        # 计算标准差 - 这里可能会有错误，适合调试
        analysis["sum_std"] = self._calculate_std(sums)
        analysis["diff_std"] = self._calculate_std(differences)
        analysis["prod_std"] = self._calculate_std(products)
        analysis["quot_std"] = self._calculate_std(quotients)

        return analysis

    def _calculate_std(self, values: list) -> float:
        """计算标准差"""
        if not values:
            return 0

        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        return self.calculator.power(variance, 0.5)  # 开平方


def print_separator(title=None):
    """打印分隔符"""
    width = 80
    if title:
        print("\n" + "=" * 10 + f" {title} " + "=" * (width - len(title) - 12) + "\n")
    else:
        print("\n" + "=" * width + "\n")


def run_demo():
    """运行演示程序"""
    print_separator("容器内调试示例程序")
    print("这个程序演示如何使用容器内调试功能")
    print("在VS Code中，您可以设置断点，然后使用launch.json连接到调试会话")
    print("程序中有几个故意添加的bug，您可以通过调试来发现它们")
    print_separator()

    # 创建计算器
    calculator = Calculator(precision=3)

    # 基本计算示例
    print("执行基本计算:")
    a, b = 10.5, 5.25
    print(f"a = {a}, b = {b}")
    print(f"a + b = {calculator.add(a, b)}")
    print(f"a - b = {calculator.subtract(a, b)}")
    print(f"a * b = {calculator.multiply(a, b)}")
    print(f"a / b = {calculator.divide(a, b)}")
    print(f"a ^ b = {calculator.power(a, b)}")
    print()

    # 除零错误示例
    print("尝试除以零 (这里有一个bug):")
    c, d = 10, 0
    try:
        print(f"{c} / {d} = {calculator.divide(c, d)}")
    except Exception as e:
        print(f"发生异常: {e}")
    print()

    # 复杂计算示例
    print("执行复杂计算:")
    complex_calc = ComplexCalculation(calculator)

    # 斐波那契数列
    n = 10
    print(f"斐波那契数列第 {n} 项 = {complex_calc.fibonacci(n)}")
    print()

    # 数列计算与分析
    start, end, step = 1.0, 5.0, 1.0
    print(f"计算数列 [{start}...{end}]，步长={step}:")
    results = complex_calc.calculate_series(start, end, step)

    print("\n计算结果:")
    for i, result in enumerate(results, 1):
        print(f"  步骤 {i}:")
        print(f"    当前值: {result['current']}")
        print(f"    下一个值: {result['next']}")
        print(f"    和: {result['sum']}")
        print(f"    差: {result['difference']}")
        print(f"    积: {result['product']}")
        print(f"    商: {result['quotient']}")
        print()

    # 分析结果
    print("结果分析:")
    analysis = complex_calc.analyze_results()
    for key, value in analysis.items():
        print(f"  {key}: {value}")

    print_separator("演示结束")
    print("您可以在计算过程中设置断点，查看变量值，步进执行代码")
    print("尝试找出程序中的bug并修复它们")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="容器内调试示例程序")
    parser.add_argument(
        "--wait", type=int, default=0, help="等待秒数后再启动，方便连接调试器"
    )

    args = parser.parse_args()

    if args.wait > 0:
        print(f"等待 {args.wait} 秒以便连接调试器...")
        time.sleep(args.wait)

    run_demo()
