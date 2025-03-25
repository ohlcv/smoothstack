#!/usr/bin/env python
"""
容器依赖管理模块测试运行脚本
"""

import os
import sys
import unittest

# 确保能导入backend模块
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

if __name__ == "__main__":
    # 自动发现并运行测试
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern="test_*.py")

    # 运行测试
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # 根据测试结果设置退出码
    sys.exit(not result.wasSuccessful())
