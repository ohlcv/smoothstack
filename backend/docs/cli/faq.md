<!-- type: faq -->

# 常见问题

Smoothstack CLI 工具的常见问题解答。

## 元数据
- title: faq
- brief: 常见问题解答
- tags: [FAQ, 帮助]
- version: 1.0.0

## 安装问题

### 如何安装Smoothstack CLI？
使用pip安装：

```bash
pip install smoothstack-cli
```

或者从源码安装：

```bash
git clone https://github.com/smoothstack/smoothstack-cli.git
cd smoothstack-cli
pip install -e .
```

### 为什么安装失败？
常见的安装失败原因包括：

1. Python版本不兼容（需要Python 3.8+）
2. pip版本过旧
3. 系统依赖缺失

解决方法：
1. 升级到Python 3.8或更高版本
2. 运行 `pip install --upgrade pip`
3. 安装必要的系统依赖

## 使用问题

### 如何查看命令帮助？
使用 `--help` 选项：

```bash
smoothstack --help
smoothstack <命令> --help
```

### 如何更新Smoothstack CLI？
使用pip更新：

```bash
pip install --upgrade smoothstack-cli
```

## 配置问题

### 配置文件在哪里？
配置文件位置：

- Windows: `%APPDATA%\smoothstack\config.yaml`
- Linux/macOS: `~/.config/smoothstack/config.yaml`

### 如何修改默认配置？
1. 打开配置文件
2. 修改相应的配置项
3. 保存文件

也可以使用命令行：

```bash
smoothstack config set <key> <value>
```

## 相关主题
- config：配置命令详解
- install：安装指南
- troubleshooting：故障排除 