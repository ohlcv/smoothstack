"""
CLI帮助文档系统

提供CLI工具的帮助文档功能，支持多语言、富文本格式和示例代码。
"""

import os
import sys
import textwrap
from typing import Dict, List, Optional, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table

# 创建Rich控制台实例
console = Console()


class DocType(Enum):
    """文档类型"""

    COMMAND = "command"  # 命令文档
    TOPIC = "topic"  # 主题文档
    EXAMPLE = "example"  # 示例文档
    FAQ = "faq"  # 常见问题


@dataclass
class DocMeta:
    """文档元数据"""

    type: DocType
    title: str
    brief: str
    tags: List[str]
    locale: str = "zh_CN"
    version: str = "1.0.0"


@dataclass
class CommandDoc:
    """命令文档"""

    meta: DocMeta
    usage: str
    description: str
    arguments: List[Dict[str, str]]
    options: List[Dict[str, str]]
    examples: List[Dict[str, str]]
    notes: List[str] = field(default_factory=list)
    see_also: List[str] = field(default_factory=list)


@dataclass
class TopicDoc:
    """主题文档"""

    meta: DocMeta
    content: str
    sections: List[Dict[str, str]]
    references: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ExampleDoc:
    """示例文档"""

    meta: DocMeta
    scenario: str
    prerequisites: List[str]
    steps: List[Dict[str, str]]
    code: str
    output: str = ""
    notes: List[str] = field(default_factory=list)


@dataclass
class FaqDoc:
    """常见问题文档"""

    meta: DocMeta
    questions: List[Dict[str, str]]
    related_topics: List[str] = field(default_factory=list)


class HelpManager:
    """帮助文档管理器"""

    def __init__(self, docs_dir: Optional[Union[str, Path]] = None):
        """
        初始化帮助文档管理器

        Args:
            docs_dir: 文档目录路径，如果为None则使用默认路径
        """
        if docs_dir is None:
            # 使用默认文档目录
            docs_dir = Path(__file__).parent.parent / "docs" / "cli"
        self.docs_dir = Path(docs_dir)
        self.docs_cache: Dict[str, Union[CommandDoc, TopicDoc, ExampleDoc, FaqDoc]] = {}
        self._load_docs()

    def _load_docs(self) -> None:
        """加载所有文档"""
        # 遍历文档目录
        for doc_file in self.docs_dir.glob("**/*.md"):
            try:
                # 解析文档内容
                doc = self._parse_doc(doc_file)
                if doc:
                    # 缓存文档
                    self.docs_cache[doc_file.stem] = doc
            except Exception as e:
                print(f"加载文档失败 {doc_file}: {e}")

    def _parse_doc(
        self, doc_file: Path
    ) -> Optional[Union[CommandDoc, TopicDoc, ExampleDoc, FaqDoc]]:
        """
        解析文档文件

        Args:
            doc_file: 文档文件路径

        Returns:
            解析后的文档对象
        """
        try:
            # 读取文档内容
            content = doc_file.read_text(encoding="utf-8")

            # 解析文档类型和元数据
            doc_type = self._get_doc_type(content)
            meta = self._parse_meta(content)

            # 根据文档类型解析具体内容
            if doc_type == DocType.COMMAND:
                return self._parse_command_doc(content, meta)
            elif doc_type == DocType.TOPIC:
                return self._parse_topic_doc(content, meta)
            elif doc_type == DocType.EXAMPLE:
                return self._parse_example_doc(content, meta)
            elif doc_type == DocType.FAQ:
                return self._parse_faq_doc(content, meta)
            else:
                print(f"未知文档类型: {doc_file}")
                return None
        except Exception as e:
            print(f"解析文档失败 {doc_file}: {e}")
            return None

    def _get_doc_type(self, content: str) -> DocType:
        """
        获取文档类型

        Args:
            content: 文档内容

        Returns:
            文档类型
        """
        # 解析文档类型标记
        if "<!-- type: command -->" in content:
            return DocType.COMMAND
        elif "<!-- type: topic -->" in content:
            return DocType.TOPIC
        elif "<!-- type: example -->" in content:
            return DocType.EXAMPLE
        elif "<!-- type: faq -->" in content:
            return DocType.FAQ
        else:
            # 默认为主题文档
            return DocType.TOPIC

    def _parse_meta(self, content: str) -> DocMeta:
        """
        解析文档元数据

        Args:
            content: 文档内容

        Returns:
            文档元数据
        """
        # 获取文档类型
        doc_type = self._get_doc_type(content)

        # 默认元数据
        title = ""
        brief = ""
        tags = []
        locale = "zh_CN"
        version = "1.0.0"

        try:
            # 查找元数据部分
            meta_start = content.find("## 元数据")
            if meta_start != -1:
                # 找到下一个 ## 标记或文档结束
                next_section = content.find("##", meta_start + 3)
                if next_section == -1:
                    next_section = len(content)

                # 提取元数据部分
                meta_section = content[meta_start:next_section].strip()

                # 解析每一行
                for line in meta_section.split("\n"):
                    line = line.strip()
                    if line.startswith("- "):
                        # 移除 "- " 前缀
                        line = line[2:]

                        # 解析键值对
                        if ":" in line:
                            key, value = [x.strip() for x in line.split(":", 1)]

                            # 根据键设置相应的值
                            if key == "title":
                                title = value
                            elif key == "brief":
                                brief = value
                            elif key == "tags":
                                # 解析标签列表 [tag1, tag2, tag3]
                                if value.startswith("[") and value.endswith("]"):
                                    tags = [
                                        tag.strip() for tag in value[1:-1].split(",")
                                    ]
                            elif key == "locale":
                                locale = value
                            elif key == "version":
                                version = value

            # 如果没有找到标题，使用文档第一个一级标题
            if not title:
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

            # 如果没有找到简介，使用文档第一个非标题、非元数据的段落
            if not brief:
                in_meta = False
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("## 元数据"):
                        in_meta = True
                    elif line.startswith("##"):
                        in_meta = False
                    elif not in_meta and line and not line.startswith("#"):
                        brief = line
                        break

        except Exception as e:
            print(f"解析元数据时出错: {e}")

        return DocMeta(
            type=doc_type,
            title=title,
            brief=brief,
            tags=tags,
            locale=locale,
            version=version,
        )

    def _parse_command_doc(self, content: str, meta: DocMeta) -> CommandDoc:
        """
        解析命令文档

        Args:
            content: 文档内容
            meta: 文档元数据

        Returns:
            命令文档对象
        """
        # 初始化命令文档属性
        usage = ""
        description = ""
        arguments = []
        options = []
        examples = []
        notes = []
        see_also = []

        try:
            # 按章节分割文档
            sections = {}
            current_section = None
            current_content = []

            for line in content.split("\n"):
                if line.startswith("## "):
                    # 保存上一个章节
                    if current_section:
                        sections[current_section] = "\n".join(current_content).strip()
                    # 开始新章节
                    current_section = line[3:].strip()
                    current_content = []
                else:
                    current_content.append(line)

            # 保存最后一个章节
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()

            # 解析用法部分
            if "用法" in sections:
                usage_section = sections["用法"]
                # 提取代码块中的内容
                if "```" in usage_section:
                    usage = usage_section.split("```")[1].strip()
                    if usage.startswith("bash\n"):
                        usage = usage[5:].strip()

            # 解析描述部分
            if "描述" in sections:
                description = sections["描述"].strip()

            # 解析参数部分
            if "参数" in sections:
                for line in sections["参数"].split("\n"):
                    if line.strip().startswith("- "):
                        param_text = line[2:].strip()
                        if "：" in param_text:
                            name, desc = param_text.split("：", 1)
                            arguments.append(
                                {"name": name.strip(), "description": desc.strip()}
                            )

            # 解析选项部分
            if "选项" in sections:
                for line in sections["选项"].split("\n"):
                    if line.strip().startswith("- "):
                        opt_text = line[2:].strip()
                        if "：" in opt_text:
                            name, desc = opt_text.split("：", 1)
                            options.append(
                                {"name": name.strip(), "description": desc.strip()}
                            )

            # 解析示例部分
            if "示例" in sections:
                example_section = sections["示例"]
                current_example = None
                current_description = None

                for line in example_section.split("\n"):
                    line = line.strip()
                    if line.startswith("### "):
                        # 新示例标题
                        current_description = line[4:].strip()
                    elif line.startswith("```"):
                        # 代码块开始或结束
                        if current_example is None:
                            current_example = ""
                        else:
                            # 代码块结束，保存示例
                            if current_description and current_example:
                                examples.append(
                                    {
                                        "description": current_description,
                                        "code": current_example.strip(),
                                    }
                                )
                            current_example = None
                    elif current_example is not None:
                        # 在代码块内
                        current_example += line + "\n"

            # 解析注意事项部分
            if "注意事项" in sections:
                for line in sections["注意事项"].split("\n"):
                    line = line.strip()
                    if line and line[0].isdigit() and ". " in line:
                        note = line.split(". ", 1)[1].strip()
                        notes.append(note)

            # 解析相关主题部分
            if "相关主题" in sections:
                for line in sections["相关主题"].split("\n"):
                    if line.strip().startswith("- "):
                        topic = line[2:].strip()
                        if "：" in topic:
                            topic = topic.split("：")[0].strip()
                        see_also.append(topic)

        except Exception as e:
            print(f"解析命令文档时出错: {e}")

        return CommandDoc(
            meta=meta,
            usage=usage,
            description=description,
            arguments=arguments,
            options=options,
            examples=examples,
            notes=notes,
            see_also=see_also,
        )

    def _parse_topic_doc(self, content: str, meta: DocMeta) -> TopicDoc:
        """
        解析主题文档

        Args:
            content: 文档内容
            meta: 文档元数据

        Returns:
            主题文档对象
        """
        # 初始化主题文档属性
        main_content = ""
        sections = []
        references = []

        try:
            # 按章节分割文档
            current_section = None
            current_content = []
            in_metadata = False
            after_metadata = False

            for line in content.split("\n"):
                # 跳过元数据部分
                if line.strip() == "## 元数据":
                    in_metadata = True
                    continue
                elif in_metadata and line.strip().startswith("##"):
                    in_metadata = False
                    after_metadata = True

                if in_metadata:
                    continue

                # 处理章节标题
                if line.strip().startswith("## "):
                    # 保存上一个章节
                    if current_section and current_content:
                        if current_section == "参考资料":
                            # 解析参考资料
                            for ref_line in current_content:
                                if ref_line.strip().startswith("- ["):
                                    # 解析Markdown链接格式：[title](url)
                                    title_start = ref_line.find("[") + 1
                                    title_end = ref_line.find("]")
                                    url_start = ref_line.find("(") + 1
                                    url_end = ref_line.find(")")

                                    if all(
                                        x != -1
                                        for x in [
                                            title_start,
                                            title_end,
                                            url_start,
                                            url_end,
                                        ]
                                    ):
                                        title = ref_line[title_start:title_end]
                                        url = ref_line[url_start:url_end]
                                        references.append({"title": title, "url": url})
                        else:
                            # 添加普通章节
                            sections.append(
                                {
                                    "title": current_section,
                                    "content": "\n".join(current_content).strip(),
                                }
                            )

                    # 开始新章节
                    current_section = line[3:].strip()
                    current_content = []
                else:
                    # 如果是主要内容（在元数据之后，第一个章节之前）
                    if after_metadata and not current_section and line.strip():
                        main_content += line + "\n"
                    # 否则添加到当前章节
                    elif current_section:
                        current_content.append(line)

            # 保存最后一个章节
            if current_section and current_content:
                if current_section == "参考资料":
                    # 解析参考资料
                    for ref_line in current_content:
                        if ref_line.strip().startswith("- ["):
                            # 解析Markdown链接格式：[title](url)
                            title_start = ref_line.find("[") + 1
                            title_end = ref_line.find("]")
                            url_start = ref_line.find("(") + 1
                            url_end = ref_line.find(")")

                            if all(
                                x != -1
                                for x in [title_start, title_end, url_start, url_end]
                            ):
                                title = ref_line[title_start:title_end]
                                url = ref_line[url_start:url_end]
                                references.append({"title": title, "url": url})
                else:
                    # 添加普通章节
                    sections.append(
                        {
                            "title": current_section,
                            "content": "\n".join(current_content).strip(),
                        }
                    )

        except Exception as e:
            print(f"解析主题文档时出错: {e}")

        return TopicDoc(
            meta=meta,
            content=main_content.strip(),
            sections=sections,
            references=references,
        )

    def _parse_example_doc(self, content: str, meta: DocMeta) -> ExampleDoc:
        """
        解析示例文档

        Args:
            content: 文档内容
            meta: 文档元数据

        Returns:
            示例文档对象
        """
        # 初始化示例文档属性
        scenario = ""
        prerequisites = []
        steps = []
        code = ""
        output = ""
        notes = []

        try:
            # 按章节分割文档
            current_section = None
            current_step = None
            current_content = []
            in_metadata = False
            in_code_block = False
            code_block_content = []

            for line in content.split("\n"):
                line_stripped = line.strip()

                # 处理元数据部分
                if line_stripped == "## 元数据":
                    in_metadata = True
                    continue
                elif in_metadata and line_stripped.startswith("##"):
                    in_metadata = False

                if in_metadata:
                    continue

                # 处理代码块
                if line_stripped.startswith("```"):
                    if in_code_block:
                        # 代码块结束
                        in_code_block = False
                        if current_step:
                            # 如果在步骤中，将代码块添加到步骤内容
                            current_content.extend(code_block_content)
                        elif current_section == "输出":
                            # 如果在输出部分，保存为输出
                            output = "\n".join(code_block_content).strip()
                        code_block_content = []
                    else:
                        # 代码块开始
                        in_code_block = True
                        if not line_stripped == "```":
                            # 如果指定了语言，跳过第一行
                            continue
                    continue

                if in_code_block:
                    code_block_content.append(line)
                    continue

                # 处理章节标题
                if line_stripped.startswith("## "):
                    # 保存上一个章节
                    if current_section == "场景":
                        scenario = "\n".join(current_content).strip()
                    elif current_section == "前提条件":
                        for prereq_line in current_content:
                            if prereq_line.strip().startswith(("- ", "* ", "1. ")):
                                prereq = prereq_line.strip()[2:].strip()
                                prerequisites.append(prereq)
                    elif current_section == "步骤" and current_step:
                        steps.append(
                            {
                                "title": current_step,
                                "content": "\n".join(current_content).strip(),
                            }
                        )
                    elif current_section == "注意事项":
                        for note_line in current_content:
                            if note_line.strip().startswith(("- ", "* ", "1. ")):
                                note = note_line.strip()[2:].strip()
                                notes.append(note)

                    # 开始新章节
                    current_section = line_stripped[3:].strip()
                    current_step = None
                    current_content = []

                # 处理步骤标题
                elif current_section == "步骤" and line_stripped.startswith("### "):
                    # 保存上一个步骤
                    if current_step:
                        steps.append(
                            {
                                "title": current_step,
                                "content": "\n".join(current_content).strip(),
                            }
                        )
                    # 开始新步骤
                    current_step = line_stripped[4:].strip()
                    current_content = []

                # 处理内容
                else:
                    current_content.append(line)

            # 保存最后一个章节
            if current_section == "场景":
                scenario = "\n".join(current_content).strip()
            elif current_section == "前提条件":
                for prereq_line in current_content:
                    if prereq_line.strip().startswith(("- ", "* ", "1. ")):
                        prereq = prereq_line.strip()[2:].strip()
                        prerequisites.append(prereq)
            elif current_section == "步骤" and current_step:
                steps.append(
                    {
                        "title": current_step,
                        "content": "\n".join(current_content).strip(),
                    }
                )
            elif current_section == "注意事项":
                for note_line in current_content:
                    if note_line.strip().startswith(("- ", "* ", "1. ")):
                        note = note_line.strip()[2:].strip()
                        notes.append(note)

        except Exception as e:
            print(f"解析示例文档时出错: {e}")

        return ExampleDoc(
            meta=meta,
            scenario=scenario,
            prerequisites=prerequisites,
            steps=steps,
            code=code,
            output=output,
            notes=notes,
        )

    def _parse_faq_doc(self, content: str, meta: DocMeta) -> FaqDoc:
        """
        解析FAQ文档

        Args:
            content: 文档内容
            meta: 文档元数据

        Returns:
            FAQ文档对象
        """
        # 初始化FAQ文档属性
        questions = []
        related_topics = []

        try:
            # 按章节分割文档
            current_section = None
            current_question = None
            current_answer = []
            in_metadata = False

            for line in content.split("\n"):
                line_stripped = line.strip()

                # 处理元数据部分
                if line_stripped == "## 元数据":
                    in_metadata = True
                    continue
                elif in_metadata and line_stripped.startswith("##"):
                    in_metadata = False

                if in_metadata:
                    continue

                # 处理章节标题
                if line_stripped.startswith("## "):
                    current_section = line_stripped[3:].strip()
                    # 保存上一个问题
                    if current_question and current_answer:
                        questions.append(
                            {
                                "question": current_question,
                                "answer": "\n".join(current_answer).strip(),
                            }
                        )
                        current_question = None
                        current_answer = []

                # 处理问题标题
                elif line_stripped.startswith("### "):
                    # 保存上一个问题
                    if current_question and current_answer:
                        questions.append(
                            {
                                "question": current_question,
                                "answer": "\n".join(current_answer).strip(),
                            }
                        )
                    # 开始新问题
                    current_question = line_stripped[4:].strip()
                    current_answer = []

                # 处理相关主题
                elif current_section == "相关主题" and line_stripped.startswith("- "):
                    topic = line_stripped[2:].strip()
                    if "：" in topic:
                        topic = topic.split("：")[0].strip()
                    related_topics.append(topic)

                # 处理答案内容
                elif current_question and not line_stripped.startswith("##"):
                    current_answer.append(line)

            # 保存最后一个问题
            if current_question and current_answer:
                questions.append(
                    {
                        "question": current_question,
                        "answer": "\n".join(current_answer).strip(),
                    }
                )

        except Exception as e:
            print(f"解析FAQ文档时出错: {e}")

        return FaqDoc(
            meta=meta,
            questions=questions,
            related_topics=related_topics,
        )

    def show_help(self, topic: Optional[str] = None) -> None:
        """
        显示帮助信息

        Args:
            topic: 帮助主题，如果为None则显示总体帮助
        """
        if topic is None:
            self._show_general_help()
        else:
            doc = self.docs_cache.get(topic)
            if doc:
                self._show_doc(doc)
            else:
                console.print(f"[red]未找到主题 '{topic}' 的帮助文档[/red]")
                self._show_similar_topics(topic)

    def _show_general_help(self) -> None:
        """显示总体帮助信息"""
        # 创建帮助概览表格
        table = Table(title="Smoothstack CLI 帮助系统")
        table.add_column("命令", style="cyan")
        table.add_column("描述", style="green")
        table.add_column("类型", style="blue")

        # 添加所有文档
        for doc_id, doc in sorted(self.docs_cache.items()):
            table.add_row(
                doc_id,
                doc.meta.brief,
                doc.meta.type.value,
            )

        # 显示表格
        console.print(table)
        console.print("\n使用 'smoothstack help <主题>' 查看详细帮助")

    def _show_doc(self, doc: Union[CommandDoc, TopicDoc, ExampleDoc, FaqDoc]) -> None:
        """
        显示具体文档

        Args:
            doc: 文档对象
        """
        if isinstance(doc, CommandDoc):
            self._show_command_doc(doc)
        elif isinstance(doc, TopicDoc):
            self._show_topic_doc(doc)
        elif isinstance(doc, ExampleDoc):
            self._show_example_doc(doc)
        elif isinstance(doc, FaqDoc):
            self._show_faq_doc(doc)

    def _show_command_doc(self, doc: CommandDoc) -> None:
        """
        显示命令文档

        Args:
            doc: 命令文档对象
        """
        # 显示命令用法
        console.print(f"\n[bold cyan]命令用法[/bold cyan]")
        console.print(Panel(doc.usage))

        # 显示命令描述
        console.print(f"\n[bold cyan]描述[/bold cyan]")
        console.print(Markdown(doc.description))

        # 显示参数
        if doc.arguments:
            console.print(f"\n[bold cyan]参数[/bold cyan]")
            args_table = Table(show_header=True, header_style="bold magenta")
            args_table.add_column("参数")
            args_table.add_column("描述")
            for arg in doc.arguments:
                args_table.add_row(arg["name"], arg["description"])
            console.print(args_table)

        # 显示选项
        if doc.options:
            console.print(f"\n[bold cyan]选项[/bold cyan]")
            opts_table = Table(show_header=True, header_style="bold magenta")
            opts_table.add_column("选项")
            opts_table.add_column("描述")
            for opt in doc.options:
                opts_table.add_row(opt["name"], opt["description"])
            console.print(opts_table)

        # 显示示例
        if doc.examples:
            console.print(f"\n[bold cyan]示例[/bold cyan]")
            for example in doc.examples:
                console.print(f"\n[green]{example['description']}[/green]")
                console.print(Panel(example["code"], expand=False))

        # 显示注意事项
        if doc.notes:
            console.print(f"\n[bold cyan]注意事项[/bold cyan]")
            for note in doc.notes:
                console.print(f"• {note}")

        # 显示相关主题
        if doc.see_also:
            console.print(f"\n[bold cyan]相关主题[/bold cyan]")
            for topic in doc.see_also:
                console.print(f"• {topic}")

    def _show_topic_doc(self, doc: TopicDoc) -> None:
        """
        显示主题文档

        Args:
            doc: 主题文档对象
        """
        # 显示主题内容
        console.print(Markdown(doc.content))

        # 显示章节
        for section in doc.sections:
            console.print(f"\n[bold cyan]{section['title']}[/bold cyan]")
            console.print(Markdown(section["content"]))

        # 显示参考资料
        if doc.references:
            console.print(f"\n[bold cyan]参考资料[/bold cyan]")
            for ref in doc.references:
                console.print(f"• [{ref['title']}]({ref['url']})")

    def _show_example_doc(self, doc: ExampleDoc) -> None:
        """
        显示示例文档

        Args:
            doc: 示例文档对象
        """
        # 显示场景描述
        console.print(f"\n[bold cyan]场景[/bold cyan]")
        console.print(Markdown(doc.scenario))

        # 显示前提条件
        console.print(f"\n[bold cyan]前提条件[/bold cyan]")
        for prereq in doc.prerequisites:
            console.print(f"• {prereq}")

        # 显示步骤
        console.print(f"\n[bold cyan]步骤[/bold cyan]")
        for i, step in enumerate(doc.steps, 1):
            console.print(f"\n[bold]{i}. {step['title']}[/bold]")
            console.print(Markdown(step["content"]))

        # 显示代码
        console.print(f"\n[bold cyan]代码[/bold cyan]")
        console.print(Syntax(doc.code, "python", theme="monokai"))

        # 显示输出
        if doc.output:
            console.print(f"\n[bold cyan]输出[/bold cyan]")
            console.print(Panel(doc.output))

        # 显示注意事项
        if doc.notes:
            console.print(f"\n[bold cyan]注意事项[/bold cyan]")
            for note in doc.notes:
                console.print(f"• {note}")

    def _show_faq_doc(self, doc: FaqDoc) -> None:
        """
        显示FAQ文档

        Args:
            doc: FAQ文档对象
        """
        # 显示问题和答案
        for i, qa in enumerate(doc.questions, 1):
            console.print(f"\n[bold cyan]Q{i}: {qa['question']}[/bold cyan]")
            console.print(Markdown(qa["answer"]))

        # 显示相关主题
        if doc.related_topics:
            console.print(f"\n[bold cyan]相关主题[/bold cyan]")
            for topic in doc.related_topics:
                console.print(f"• {topic}")

    def _show_similar_topics(self, topic: str) -> None:
        """
        显示相似主题建议

        Args:
            topic: 搜索的主题
        """
        # TODO: 实现模糊匹配算法
        similar_topics = []
        if similar_topics:
            console.print("\n[yellow]您是不是要找：[/yellow]")
            for t in similar_topics:
                console.print(f"• {t}")
