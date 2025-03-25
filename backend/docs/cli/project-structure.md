<!-- type: topic -->

# 项目结构说明

Smoothstack项目的标准目录结构和文件组织说明。

## 元数据
- title: project-structure
- brief: 项目结构说明
- tags: [项目, 结构, 目录]
- version: 1.0.0

## 目录结构

Smoothstack项目采用以下标准目录结构：

```
myproject/
├── backend/           # 后端代码
│   ├── api/          # API接口
│   ├── core/         # 核心功能
│   ├── models/       # 数据模型
│   └── tests/        # 测试代码
├── frontend/         # 前端代码
│   ├── src/          # 源代码
│   ├── public/       # 静态资源
│   └── tests/        # 测试代码
├── docs/             # 文档
│   ├── api/          # API文档
│   └── guides/       # 使用指南
├── scripts/          # 工具脚本
├── config/           # 配置文件
└── data/             # 数据文件
```

## 重要文件

### 配置文件
- `pyproject.toml`: Python项目配置
- `package.json`: Node.js项目配置
- `docker-compose.yml`: Docker服务配置
- `.env`: 环境变量配置

### 文档文件
- `README.md`: 项目说明
- `CHANGELOG.md`: 版本变更记录
- `CONTRIBUTING.md`: 贡献指南

### 其他文件
- `.gitignore`: Git忽略规则
- `.dockerignore`: Docker忽略规则
- `Dockerfile`: Docker镜像构建配置

## 最佳实践

### 目录命名
1. 使用小写字母和下划线
2. 选择有描述性的名称
3. 避免使用特殊字符

### 文件组织
1. 相关文件放在同一目录
2. 保持目录结构清晰
3. 避免目录层级过深

### 模块划分
1. 按功能模块划分
2. 保持模块独立性
3. 避免循环依赖

## 参考资料
- [Python项目结构最佳实践](https://docs.python-guide.org/)
- [Vue.js项目结构指南](https://vuejs.org/guide/best-practices/) 