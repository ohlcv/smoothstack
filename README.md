# Smoothstack

<div align="center">
  <img src="frontend/public/assets/logo.svg" alt="Smoothstack Logo" width="200" />
  <p>
    <strong>现代化全栈应用开发框架 | Modern Full-Stack Application Development Framework</strong>
  </p>
  <p>
    <a href="#核心特性">核心特性</a> •
    <a href="#技术栈">技术栈</a> •
    <a href="#快速开始">快速开始</a> •
    <a href="#已实现功能">已实现功能</a> •
    <a href="#架构概览">架构概览</a> •
    <a href="#使用场景">使用场景</a> •
    <a href="#扩展指南">扩展指南</a> •
    <a href="#故障排除指南">故障排除</a> •
    <a href="#贡献指南">贡献指南</a>
  </p>
</div>

## 项目愿景

Smoothstack 致力于解决全栈开发中的环境配置痛点，让开发者将精力集中在业务逻辑实现上，而非繁琐的环境搭建与依赖管理。通过 Docker 容器化技术和自动化脚本，提供一键式开发环境部署，实现「**配置即代码**」的开发理念。

> 💡 **核心理念**：
> - 环境搭建不应成为开发瓶颈
> - 依赖管理不应消耗创造力
> - 一次配置，随处运行
> - 标准化的开发流程

## 核心特性

- 🚀 **一键式环境部署**
  - 10分钟内完成从零到可用的全栈开发环境搭建
  - 自动化的依赖安装和配置
  - 跨平台兼容性保证

- 🐳 **Docker 容器化管理**
  - 隔离的开发环境
  - 统一的运行环境
  - 简化的部署流程

- 📦 **智能依赖管理**
  - 自动化的依赖安装和更新
  - 版本冲突检测和解决
  - 依赖安全审计

- 🛠️ **开发体验优先**
  - 热重载支持
  - 智能日志系统
  - 完整的调试工具链

- 🔌 **高度可扩展**
  - 插件系统支持
  - 自定义模板
  - 灵活的配置选项

## 技术栈

### 前端技术栈
- Vue 3 + TypeScript
- Vite
- Ant Design Vue
- Pinia
- Vue Router

### 后端技术栈
- Python 3.11+
- FastAPI/Django/Flask
- SQLAlchemy
- PostgreSQL/Redis

### 开发工具
- Docker + docker-compose
- Git
- VS Code 配置
- 自动化测试工具

## 快速开始

### 环境要求
- Docker Desktop 24.0.0+
- Git 2.40.0+
- VS Code, Cursor(推荐)
- Node.js 18+ (可选，如果不使用Docker)
- Python 3.11+ (可选，如果不使用Docker)

### 部署步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/smoothstack.git
cd smoothstack
```

2. **初始化环境**
```bash
# 使用Python CLI工具初始化环境
python smoothstack.py env setup

# 如果需要使用中国镜像源加速
python smoothstack.py env setup --use-cn-mirror
```

3. **启动开发环境**
```bash
# 启动所有服务
python smoothstack.py docker up

# 仅启动特定服务
python smoothstack.py docker up --service frontend  # 仅启动前端
python smoothstack.py docker up --service backend   # 仅启动后端
```

4. **访问服务**
- 前端开发服务器: http://localhost:3000
- 后端API服务: http://localhost:5000
- API文档: http://localhost:5000/docs
- 数据库管理: http://localhost:8080

### 命令行使用指南

Smoothstack 提供了统一的命令行工具，通过Python脚本执行：

```bash
python smoothstack.py <命令> [选项]
```

基本命令：

```bash
# 环境管理
python smoothstack.py env check    # 检查开发环境
python smoothstack.py env setup    # 设置开发环境
python smoothstack.py env clean    # 清理开发环境

# Docker管理
python smoothstack.py docker up       # 启动Docker服务
python smoothstack.py docker down     # 停止Docker服务
python smoothstack.py docker restart  # 重启Docker服务
python smoothstack.py docker status   # 查看Docker状态
python smoothstack.py docker logs     # 查看Docker日志

# 项目管理
python smoothstack.py project create <name>  # 创建新项目
python smoothstack.py project list           # 列出所有项目
python smoothstack.py project delete <name>  # 删除项目

# 数据库管理
python smoothstack.py db migrate   # 运行数据库迁移
python smoothstack.py db rollback  # 回滚数据库迁移
python smoothstack.py db seed      # 填充数据库种子数据
```

### 高级功能

如果需要使用高级功能，可以使用`--advanced`选项：

```bash
python smoothstack.py --advanced <命令> [选项]
```

高级命令示例：

```bash
# 后端开发工具
python smoothstack.py --advanced backend create-app <name>       # 创建新的后端应用
python smoothstack.py --advanced backend add-model <app> <name>  # 添加数据模型
python smoothstack.py --advanced backend run <app>               # 运行开发服务器

# 前端开发工具
python smoothstack.py --advanced frontend create-app <name>    # 创建新的前端应用
python smoothstack.py --advanced frontend add-component <name> # 添加组件
python smoothstack.py --advanced frontend run                  # 运行前端开发服务器

# 依赖管理
python smoothstack.py --advanced deps install <type> <packages>   # 安装依赖
python smoothstack.py --advanced deps list <type>                 # 列出所有依赖

# 示例项目
python smoothstack.py --advanced example create <name>  # 创建示例项目
python smoothstack.py --advanced example list           # 列出可用的示例项目
```

## 故障排除指南

### 常见问题

1. **环境初始化问题**
   - 问题：Docker服务未启动
   - 解决：检查Docker Desktop是否正在运行，使用 `docker info` 验证
   
   - 问题：端口冲突
   - 解决：使用 `netstat -ano | findstr "3000 5000 8080"` 检查端口占用

2. **依赖管理问题**
   - 问题：前端依赖安装失败
   - 解决：清除NPM缓存 `python smoothstack.py --advanced deps clean frontend`
   
   - 问题：后端依赖版本冲突
   - 解决：使用 `python smoothstack.py --advanced deps check backend` 检查并解决冲突

3. **容器问题**
   - 问题：容器启动失败
   - 解决：检查日志 `python smoothstack.py docker logs --service <service>`
   
   - 问题：容器资源不足
   - 解决：调整Docker资源限制或清理未使用的容器和镜像

## 已实现功能

### 1. 环境管理
- [x] Docker容器化开发环境
- [x] 自动化环境配置
- [x] 跨平台兼容性支持
- [x] 开发环境热重载
- [ ] 生产环境配置（开发中）

### 2. 前端功能
- [x] Vue 3 + TypeScript 基础框架
- [x] Vite 开发服务器配置
- [x] Ant Design Vue 组件库集成
- [x] Pinia 状态管理
- [x] Vue Router 路由管理
- [ ] 组件开发系统（计划中）
- [ ] 主题定制系统（计划中）

### 3. 后端功能
- [x] FastAPI 基础框架
- [x] 数据库集成（PostgreSQL）
- [x] Redis 缓存支持
- [x] API 文档自动生成
- [ ] 认证授权系统（开发中）
- [ ] 任务队列集成（计划中）

### 4. 开发工具
- [x] 命令行工具（CLI）
- [x] 依赖管理系统
- [x] 代码格式化工具
- [x] 基础测试框架
- [ ] 自动化测试（开发中）
- [ ] CI/CD 配置（计划中）

## 架构概览

### 项目结构
```
smoothstack/
├── core/                   # 框架核心代码
│   ├── commands/          # CLI命令实现
│   ├── scripts/           # 自动化脚本
│   ├── templates/         # 框架模板
│   ├── docker/            # Docker相关配置
│   ├── env/               # 环境管理
│   ├── db/                # 数据库管理
│   └── cli.py             # 命令行接口
├── frontend/              # 前端应用
│   ├── src/               # 源代码
│   ├── public/            # 静态资源
│   ├── Dockerfile.dev     # 开发环境Docker配置
│   └── vite.config.ts     # Vite配置
├── backend/               # 后端服务
│   ├── api/               # API实现
│   ├── core/              # 核心功能
│   ├── cli/               # 后端CLI工具
│   ├── tools/             # 开发工具
│   ├── config/            # 配置管理
│   ├── database/          # 数据库模块
│   ├── container_manager/ # 容器管理
│   ├── dependency_manager/# 依赖管理
│   ├── platform_compat/   # 平台兼容性
│   └── main.py            # 应用入口
├── examples/              # 示例代码
├── templates/             # 项目模板
├── tests/                 # 测试代码
├── docs/                  # 项目文档
└── smoothstack.py         # 统一命令行入口
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

详细信息请参考[贡献指南](CONTRIBUTING.md)

## 许可证

本项目采用 [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE) 许可证。

## 作者信息

- **作者**: ohlcv
- **联系邮箱**: 24369961@qq.com
- **版权所有**: © 2025-至今 ohlcv. 保留所有权利。


