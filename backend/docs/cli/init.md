<!-- type: command -->

# init

初始化一个新的Smoothstack项目。

## 元数据
- title: init
- brief: 初始化新项目
- tags: [项目, 初始化, 配置]
- version: 1.0.0

## 用法
```bash
smoothstack init [项目名称] [选项]
```

## 描述
`init` 命令用于创建一个新的Smoothstack项目。它会生成项目的基本目录结构、配置文件和必要的依赖项。
你可以指定项目名称和各种选项来自定义项目的初始化过程。

## 参数
- 项目名称：新项目的名称（可选，默认使用当前目录名）

## 选项
- --template, -t：使用指定的项目模板（默认：basic）
- --python-version：指定Python版本（默认：3.8）
- --node-version：指定Node.js版本（默认：16）
- --docker：添加Docker支持（默认：false）
- --git：初始化Git仓库（默认：true）
- --force, -f：强制覆盖已存在的目录（默认：false）

## 示例

### 基本用法
```bash
smoothstack init myproject
```

### 使用特定模板
```bash
smoothstack init myproject --template fullstack
```

### 指定Python和Node.js版本
```bash
smoothstack init myproject --python-version 3.9 --node-version 18
```

### 添加Docker支持
```bash
smoothstack init myproject --docker
```

## 注意事项
1. 确保有足够的磁盘空间用于项目初始化
2. 如果使用 --force 选项，请注意可能会删除现有文件
3. 项目名称应遵循Python包命名规范

## 相关主题
- project-structure：项目结构说明
- templates：可用项目模板列表
- configuration：配置文件详解 