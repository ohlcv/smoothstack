"""
帮助系统测试
"""

import os
import tempfile
from pathlib import Path
from textwrap import dedent

import pytest
from cli.help import (
    HelpManager,
    DocType,
    DocMeta,
    CommandDoc,
    TopicDoc,
    FaqDoc,
    ExampleDoc,
)


@pytest.fixture
def temp_docs_dir():
    """创建临时文档目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_command_doc(temp_docs_dir):
    """创建示例命令文档"""
    doc_content = dedent(
        """
    <!-- type: command -->

    # test-cmd

    测试命令示例。

    ## 元数据
    - title: test-cmd
    - brief: 测试命令
    - tags: [测试, 示例]
    - version: 1.0.0

    ## 用法
    ```bash
    smoothstack test-cmd [选项]
    ```

    ## 描述
    这是一个用于测试的示例命令。

    ## 参数
    - 输入文件：要处理的文件路径

    ## 选项
    - --verbose：显示详细输出
    - --output：指定输出文件

    ## 示例

    ### 基本用法
    ```bash
    smoothstack test-cmd input.txt
    ```

    ### 使用详细输出
    ```bash
    smoothstack test-cmd --verbose input.txt
    ```

    ## 注意事项
    1. 输入文件必须存在
    2. 输出文件会被覆盖

    ## 相关主题
    - other-cmd：其他相关命令
    """
    )

    doc_file = temp_docs_dir / "test-cmd.md"
    doc_file.write_text(doc_content)
    return doc_file


@pytest.fixture
def sample_topic_doc(temp_docs_dir):
    """创建示例主题文档"""
    doc_content = dedent(
        """
    <!-- type: topic -->

    # project-structure

    项目结构说明文档。

    ## 元数据
    - title: project-structure
    - brief: 项目结构说明
    - tags: [项目, 结构]
    - version: 1.0.0

    ## 目录结构

    标准目录结构如下：

    ```
    project/
    ├── src/
    └── tests/
    ```

    ## 配置文件

    主要配置文件包括：

    - `config.yaml`
    - `.env`

    ## 参考资料
    - [Python项目结构](https://python.org)
    - [最佳实践指南](https://example.com)
    """
    )

    doc_file = temp_docs_dir / "project-structure.md"
    doc_file.write_text(doc_content)
    return doc_file


@pytest.fixture
def sample_faq_doc(temp_docs_dir):
    """创建示例FAQ文档"""
    doc_content = dedent(
        """
    <!-- type: faq -->

    # FAQ

    常见问题解答。

    ## 元数据
    - title: faq
    - brief: 常见问题解答
    - tags: [FAQ, 帮助]
    - version: 1.0.0

    ## 安装问题

    ### 如何安装？
    使用pip安装：

    ```bash
    pip install mypackage
    ```

    ### 支持哪些系统？
    支持以下系统：
    - Windows 10+
    - Linux
    - macOS

    ## 使用问题

    ### 如何开始？
    1. 安装软件
    2. 运行初始化命令
    3. 开始使用

    ## 相关主题
    - install：安装指南
    - quickstart：快速入门
    """
    )

    doc_file = temp_docs_dir / "faq.md"
    doc_file.write_text(doc_content)
    return doc_file


@pytest.fixture
def sample_example_doc(temp_docs_dir):
    """创建示例示例文档"""
    doc_content = dedent(
        """
    <!-- type: example -->

    # 示例命令

    演示如何使用示例命令。

    ## 元数据
    - title: example-cmd
    - brief: 示例命令演示
    - tags: [示例, 命令]
    - version: 1.0.0

    ## 场景
    你需要处理一个大型文本文件，提取其中的特定内容。

    ## 前提条件
    1. 已安装软件包
    2. 有读写权限
    3. 文件大小小于2GB

    ## 步骤

    ### 1. 准备输入文件
    创建一个示例输入文件：

    ```bash
    echo "test content" > input.txt
    ```

    ### 2. 运行命令
    执行处理命令：

    ```bash
    myapp process input.txt --output result.txt
    ```

    ### 3. 检查结果
    查看处理结果：

    ```bash
    cat result.txt
    ```

    ## 输出
    ```
    处理完成：
    - 输入行数：100
    - 输出行数：50
    - 耗时：2.5s
    ```

    ## 注意事项
    1. 备份重要文件
    2. 检查磁盘空间
    3. 注意文件编码
    """
    )

    doc_file = temp_docs_dir / "example-cmd.md"
    doc_file.write_text(doc_content)
    return doc_file


def test_get_doc_type(sample_command_doc):
    """测试文档类型检测"""
    help_manager = HelpManager(sample_command_doc.parent)
    content = sample_command_doc.read_text()

    assert help_manager._get_doc_type(content) == DocType.COMMAND
    assert help_manager._get_doc_type("<!-- type: topic -->") == DocType.TOPIC
    assert help_manager._get_doc_type("<!-- type: example -->") == DocType.EXAMPLE
    assert help_manager._get_doc_type("<!-- type: faq -->") == DocType.FAQ
    assert help_manager._get_doc_type("no type specified") == DocType.TOPIC


def test_parse_meta(sample_command_doc):
    """测试元数据解析"""
    help_manager = HelpManager(sample_command_doc.parent)
    content = sample_command_doc.read_text()
    meta = help_manager._parse_meta(content)

    assert isinstance(meta, DocMeta)
    assert meta.type == DocType.COMMAND
    assert meta.title == "test-cmd"
    assert meta.brief == "测试命令"
    assert meta.tags == ["测试", "示例"]
    assert meta.version == "1.0.0"
    assert meta.locale == "zh_CN"


def test_parse_command_doc(sample_command_doc):
    """测试命令文档解析"""
    help_manager = HelpManager(sample_command_doc.parent)
    content = sample_command_doc.read_text()
    meta = help_manager._parse_meta(content)
    doc = help_manager._parse_command_doc(content, meta)

    assert isinstance(doc, CommandDoc)
    assert doc.meta == meta
    assert doc.usage == "smoothstack test-cmd [选项]"
    assert "这是一个用于测试的示例命令" in doc.description

    assert len(doc.arguments) == 1
    assert doc.arguments[0]["name"] == "输入文件"
    assert "要处理的文件路径" in doc.arguments[0]["description"]

    assert len(doc.options) == 2
    assert doc.options[0]["name"] == "--verbose"
    assert "显示详细输出" in doc.options[0]["description"]
    assert doc.options[1]["name"] == "--output"
    assert "指定输出文件" in doc.options[1]["description"]

    assert len(doc.examples) == 2
    assert doc.examples[0]["description"] == "基本用法"
    assert "smoothstack test-cmd input.txt" in doc.examples[0]["code"]
    assert doc.examples[1]["description"] == "使用详细输出"
    assert "--verbose" in doc.examples[1]["code"]

    assert len(doc.notes) == 2
    assert "输入文件必须存在" in doc.notes[0]
    assert "输出文件会被覆盖" in doc.notes[1]

    assert len(doc.see_also) == 1
    assert "other-cmd" in doc.see_also


def test_help_manager_init(temp_docs_dir):
    """测试帮助管理器初始化"""
    help_manager = HelpManager(temp_docs_dir)
    assert help_manager.docs_dir == temp_docs_dir
    assert isinstance(help_manager.docs_cache, dict)


def test_help_manager_load_docs(sample_command_doc):
    """测试文档加载"""
    help_manager = HelpManager(sample_command_doc.parent)
    assert len(help_manager.docs_cache) == 1
    assert "test-cmd" in help_manager.docs_cache

    doc = help_manager.docs_cache["test-cmd"]
    assert isinstance(doc, CommandDoc)
    assert doc.meta.title == "test-cmd"


def test_parse_topic_doc(sample_topic_doc):
    """测试主题文档解析"""
    help_manager = HelpManager(sample_topic_doc.parent)
    content = sample_topic_doc.read_text()
    meta = help_manager._parse_meta(content)
    doc = help_manager._parse_topic_doc(content, meta)

    assert isinstance(doc, TopicDoc)
    assert doc.meta == meta
    assert "项目结构说明文档" in doc.content

    assert len(doc.sections) == 2
    assert doc.sections[0]["title"] == "目录结构"
    assert "标准目录结构" in doc.sections[0]["content"]
    assert doc.sections[1]["title"] == "配置文件"
    assert "主要配置文件" in doc.sections[1]["content"]

    assert len(doc.references) == 2
    assert doc.references[0]["title"] == "Python项目结构"
    assert doc.references[0]["url"] == "https://python.org"
    assert doc.references[1]["title"] == "最佳实践指南"
    assert doc.references[1]["url"] == "https://example.com"


def test_parse_faq_doc(sample_faq_doc):
    """测试FAQ文档解析"""
    help_manager = HelpManager(sample_faq_doc.parent)
    content = sample_faq_doc.read_text()
    meta = help_manager._parse_meta(content)
    doc = help_manager._parse_faq_doc(content, meta)

    assert isinstance(doc, FaqDoc)
    assert doc.meta == meta

    assert len(doc.questions) == 3

    # 测试第一个问题
    assert doc.questions[0]["question"] == "如何安装？"
    assert "pip install mypackage" in doc.questions[0]["answer"]

    # 测试第二个问题
    assert doc.questions[1]["question"] == "支持哪些系统？"
    assert "Windows 10+" in doc.questions[1]["answer"]
    assert "Linux" in doc.questions[1]["answer"]
    assert "macOS" in doc.questions[1]["answer"]

    # 测试第三个问题
    assert doc.questions[2]["question"] == "如何开始？"
    assert "安装软件" in doc.questions[2]["answer"]
    assert "运行初始化命令" in doc.questions[2]["answer"]
    assert "开始使用" in doc.questions[2]["answer"]

    # 测试相关主题
    assert len(doc.related_topics) == 2
    assert "install" in doc.related_topics
    assert "quickstart" in doc.related_topics


def test_parse_example_doc(sample_example_doc):
    """测试示例文档解析"""
    help_manager = HelpManager(sample_example_doc.parent)
    content = sample_example_doc.read_text()
    meta = help_manager._parse_meta(content)
    doc = help_manager._parse_example_doc(content, meta)

    assert isinstance(doc, ExampleDoc)
    assert doc.meta == meta

    # 测试场景
    assert "你需要处理一个大型文本文件" in doc.scenario

    # 测试前提条件
    assert len(doc.prerequisites) == 3
    assert "已安装软件包" in doc.prerequisites[0]
    assert "有读写权限" in doc.prerequisites[1]
    assert "文件大小小于2GB" in doc.prerequisites[2]

    # 测试步骤
    assert len(doc.steps) == 3
    assert doc.steps[0]["title"] == "1. 准备输入文件"
    assert "echo" in doc.steps[0]["content"]
    assert doc.steps[1]["title"] == "2. 运行命令"
    assert "myapp process" in doc.steps[1]["content"]
    assert doc.steps[2]["title"] == "3. 检查结果"
    assert "cat result.txt" in doc.steps[2]["content"]

    # 测试输出
    assert "处理完成" in doc.output
    assert "输入行数：100" in doc.output
    assert "输出行数：50" in doc.output

    # 测试注意事项
    assert len(doc.notes) == 3
    assert "备份重要文件" in doc.notes[0]
    assert "检查磁盘空间" in doc.notes[1]
    assert "注意文件编码" in doc.notes[2]
