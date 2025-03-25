# Smoothstack

<p align="center">
  <img src="/assets/logo.svg" alt="Smoothstack Logo" width="200" />
</p>

<p align="center">
  <strong>现代化全栈应用开发框架 | Modern Full-Stack Application Development Framework</strong>
</p>

<p align="center">
  <a href="#核心特性">核心特性</a> •
  <a href="#技术栈">技术栈</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#容器化开发与依赖管理">容器化开发与依赖管理</a> •
  <a href="#架构概览">架构概览</a> •
  <a href="#使用场景">使用场景</a> •
  <a href="#示例应用">示例应用</a> •
  <a href="#扩展指南">扩展指南</a> •
  <a href="#贡献指南">贡献指南</a>
</p>

## 项目愿景

Smoothstack 致力于解决全栈开发中的环境配置痛点，让开发者将精力集中在业务逻辑实现上，而非繁琐的环境搭建与依赖管理。通过 Docker 容器化技术和自动化脚本，提供一键式开发环境部署，实现「**配置即代码**」的开发理念。

> 💡 **核心理念**：环境搭建不应成为开发瓶颈，依赖管理不应消耗创造力。

## 核心特性

- **一键式环境部署**：5分钟内完成从零到可用的全栈开发环境搭建
- **Docker 容器化管理**：隔离的开发环境确保"我这能运行"就是"到处能运行"
- **跨平台兼容**：Windows、macOS、Linux 全平台支持，消除"在我电脑上能跑"的问题
- **自动化依赖管理**：前后端依赖统一管理，版本锁定与冲突检测
- **多环境支持**：开发、测试、预发布、生产环境配置分离与一键切换
- **双语言整合**：无缝集成 JavaScript/TypeScript 前端与 Python 后端的开发体验
- **模块化架构**：可插拔组件设计，按需引入所需功能
- **开发体验优先**：热重载、智能日志、调试工具链一应俱全
- **多语言与国际化**：内置i18n支持，便捷的语言切换机制
- **数据可视化支持**：集成专业图表库，快速构建数据驱动的应用
- **高度可扩展**：模块化设计使您可以仅使用需要的部分

## 技术栈

### 前端技术栈

- **核心框架**：[Vue 3](https://v3.vuejs.org/) + [TypeScript](https://www.typescriptlang.org/)
- **构建工具**：[Vite](https://vitejs.dev/) (开发服务器和构建工具)
- **UI 框架**：[Ant Design Vue](https://antdv.com/docs/vue/introduce-cn)
- **状态管理**：[Pinia](https://pinia.vuejs.org/)
- **路由管理**：[Vue Router](https://router.vuejs.org/)
- **桌面应用框架**：[Electron](https://www.electronjs.org/) (可选)
- **HTTP 客户端**：[Axios](https://axios-http.com/)
- **工具库**：[lodash](https://lodash.com/)、[dayjs](https://day.js.org/)
- **CSS 预处理**：[SCSS](https://sass-lang.com/)
- **数据可视化**：[ECharts](https://echarts.apache.org/) (强大的图表库)
- **国际化解决方案**：[Vue I18n](https://vue-i18n.intlify.dev/) (多语言支持)
- **组合式API工具**：[VueUse](https://vueuse.org/) (实用的组合式API集合)

### 后端技术栈

- **核心语言**：[Python 3.8+](https://www.python.org/)
- **数据库**：[SQLite](https://www.sqlite.org/) (默认) / 可扩展支持 PostgreSQL、MySQL
- **API 框架**：内置 Python API 服务，可扩展支持 [FastAPI](https://fastapi.tiangolo.com/)
- **异步任务**：可选集成 [Celery](https://docs.celeryq.dev/)
- **ORM**：可选集成 [SQLAlchemy](https://www.sqlalchemy.org/)
- **跨语言通信**：JavaScript-Python桥接

### 容器化与环境管理

- **容器技术**：[Docker](https://www.docker.com/) + [docker-compose](https://docs.docker.com/compose/)
- **容器化开发**：支持 [VS Code Dev Containers](https://code.visualstudio.com/docs/remote/containers)
- **环境管理**：Python 虚拟环境 + Node.js 版本管理
- **CI/CD 支持**：提供 GitHub Actions 工作流模板

### 测试框架

- **前端测试**：[Vitest](https://vitest.dev/) / [Jest](https://jestjs.io/) (单元测试)
- **组件测试**：[Vue Test Utils](https://test-utils.vuejs.org/)
- **端到端测试**：[Cypress](https://www.cypress.io/) (可选)
- **后端测试**：[pytest](https://pytest.org/) (Python测试框架)
- **API测试**：[Postman](https://www.postman.com/) / [Insomnia](https://insomnia.rest/) (可选)

## 快速开始

### 前提条件

- 已安装 [Docker](https://www.docker.com/get-started) 和 [docker-compose](https://docs.docker.com/compose/install/)
- 在 Windows 环境需安装 [Git Bash](https://gitforwindows.org/) 或启用 WSL2

### 基础使用

1. **克隆项目**

```bash
git clone https://github.com/yourusername/smoothstack.git
cd smoothstack
```

2. **环境初始化**

```bash
# 一键设置所有开发环境依赖
./start.sh setup

# 使用中国镜像源加速依赖下载（可选）
./start.sh setup --cn
```

3. **启动开发环境**

```bash
# 启动开发模式（支持热重载）
./start.sh run

# 查看系统状态
./start.sh status
```

4. **访问应用**

- 前端开发服务器：http://localhost:3000
- 桌面应用：自动启动
- API服务：http://localhost:5000

### 常用命令

```bash
# 显示帮助信息
./start.sh help

# 停止所有服务
./start.sh stop

# 查看日志
./start.sh logs

# 重启服务
./start.sh restart

# 切换国内/国外源
./start.sh sources cn  # 切换至中国镜像源
./start.sh sources us  # 切换至官方源

# 修复Windows环境中文编码问题
./start.sh fix-encoding

# 打包应用为可执行文件
./start.sh package
```

### 关于命令接口

虽然Smoothstack的底层实现已经从Bash脚本迁移到了Python (基于[重构方案](docs/重构方案.md))，但我们仍然保留了`start.sh`作为用户接口入口点，以提供平滑的过渡体验：

- **底层实现**: 所有核心功能均由Python模块实现，提供更好的跨平台兼容性和功能扩展性
- **命令接口**: 保留Shell脚本作为简单入口点，内部调用Python实现
- **为什么这样做**: 确保向后兼容性，让现有用户和自动化脚本无需立即调整
- **未来发展**: 长期计划提供纯Python CLI命令 (`smoothstack` 或 `python -m smoothstack_cli`)

**技术实现**:
```bash
# start.sh 内部实际上执行的是
python -m smoothstack_cli "$@"
```

## 容器化开发与依赖管理

Smoothstack 提供了先进的容器化开发体验和精细的依赖管理能力：

### 容器内开发

- **Dev Containers集成**：与VS Code Dev Containers完全集成，提供一致的开发环境
  - 自动生成标准化的devcontainer.json配置
  - 预配置各类开发环境模板（Python、Node.js、全栈开发等）
  - 支持端口映射、卷挂载和环境变量配置
  - 自动推荐并安装特定开发环境所需VS Code扩展
- **预配置开发环境**：包含所有必要工具和扩展的容器化开发环境
- **实时同步**：代码更改实时同步到容器，支持热重载
- **断点调试**：容器内完整调试支持，包括断点、变量检查和调用栈分析
- **远程开发**：支持在远程主机上的容器中进行开发，实现团队环境一致性

### 多容器服务编排

- **服务组定义**：通过YAML配置文件定义多容器服务组
- **依赖管理**：自动处理服务间的依赖关系和启动顺序
- **批量操作**：一键部署、启动、停止整个服务组
- **服务监控**：跟踪服务状态和健康情况
- **配置灵活**：支持环境变量、卷挂载和网络配置

### 容器网络配置

- **网络管理**：创建、删除和管理Docker网络
- **网络模板**：预置多种常用网络配置模板，快速创建标准化网络
- **容器连接**：管理容器与网络的连接关系
- **连接测试**：提供容器间网络连接测试和诊断工具
- **详细信息**：查看网络详情和容器IP分配情况
- **自定义配置**：支持自定义子网、网关和网络选项

### 依赖管理系统

- **多源智能切换**：支持多个镜像源，自动选择最优源
  - 内置多个国内源：清华源、阿里源、中科大源等
  - 内置多个国外源：PyPI官方源、AWS源等
  - 自动源健康检查：定期检测源可用性和速度
  - 智能源切换：根据网络状况自动选择最优源
  - 手动源切换：支持手动指定使用特定源
  ```bash
  # 自动选择最优源
  ./start.sh deps install django==4.2.1
  
  # 手动指定使用清华源
  ./start.sh deps install django==4.2.1 --source tsinghua
  
  # 手动指定使用PyPI官方源
  ./start.sh deps install django==4.2.1 --source pypi
  ```

- **网络优化与容错**：
  - 断点续传：支持大文件下载断点续传
  - 并发下载：多线程并发下载提高速度
  - 超时重试：智能超时设置和自动重试
  - 代理支持：支持配置HTTP/HTTPS代理
  - 源故障转移：当主源失败时自动切换到备用源
  ```bash
  # 配置代理
  ./start.sh deps config --proxy http://127.0.0.1:7890
  
  # 设置重试次数和超时
  ./start.sh deps config --retries 3 --timeout 30
  ```

- **离线包管理**：
  - 本地缓存：自动缓存已下载的包
  - 离线安装：支持从本地缓存安装
  - 包导出导入：支持导出依赖包供离线使用
  - 依赖分析：分析并导出完整的依赖树
  ```bash
  # 导出依赖包
  ./start.sh deps export --output ./deps_cache
  
  # 从本地缓存安装
  ./start.sh deps install --from-cache ./deps_cache
  ```

- **精确版本控制**：
  - 支持精确指定依赖版本
  - 支持版本范围指定
  - 支持版本锁定
  - 支持版本更新检查
  ```bash
  # 添加精确版本
  ./start.sh deps add django==4.2.1
  
  # 添加版本范围
  ./start.sh deps add "django>=4.2.0,<5.0.0"
  
  # 锁定当前版本
  ./start.sh deps lock
  
  # 检查更新
  ./start.sh deps check-updates
  ```

- **多环境依赖**：
  - 区分开发、测试和生产环境
  - 环境特定的依赖配置
  - 环境隔离
  - 环境同步
  ```bash
  # 安装开发环境依赖
  ./start.sh deps install --env dev
  
  # 安装生产环境依赖
  ./start.sh deps install --env prod
  
  # 同步环境依赖
  ./start.sh deps sync --env prod
  ```

- **依赖冲突检测**：
  - 自动检测依赖冲突
  - 提供冲突解决方案
  - 支持依赖树可视化
  - 支持依赖分析报告
  ```bash
  # 检查依赖冲突
  ./start.sh deps check-conflicts
  
  # 生成依赖分析报告
  ./start.sh deps analyze --output report.html
  ```

- **依赖审计**：
  - 定期检查依赖安全漏洞
  - 检查过时包
  - 提供更新建议
  - 支持自动更新
  ```bash
  # 检查安全漏洞
  ./start.sh deps audit
  
  # 检查过时包
  ./start.sh deps outdated
  
  # 自动更新依赖
  ./start.sh deps update
  ```

### 多容器策略管理

- **独立策略容器**：支持为不同策略创建独立的容器实例
  - 每个策略可在独立容器中运行，实现资源隔离
  - 支持策略容器间的安全通信和数据共享
- **批量容器操作**：提供管理多个容器的批量操作命令
  - 批量启动: `./start.sh strategies start-all`
  - 批量监控: `./start.sh strategies monitor`
  - 选择性操作: `./start.sh strategies start strategy-1 strategy-2`
- **容器资源控制**：为每个策略容器精确分配CPU、内存和存储资源
- **状态持久化**：支持策略状态的持久化存储和灾难恢复
- **集中化监控**：统一监控所有策略容器的运行状态、资源使用和日志

## 架构概览

Smoothstack 采用模块化、松耦合架构设计，确保各组件可独立开发与测试：

### 项目结构

```
smoothstack/
├── frontend/           # Vue 3 + TypeScript 前端应用
│   ├── src/            # 源代码
│   ├── public/         # 静态资源
│   └── vite.config.ts  # Vite 配置
├── backend/            # Python 后端服务
│   ├── api/            # API 接口定义
│   ├── core/           # 核心业务逻辑
│   └── models/         # 数据模型
├── electron/           # Electron 桌面应用配置
├── docker/             # Docker 相关配置
│   ├── frontend/       # 前端容器配置
│   └── backend/        # 后端容器配置
├── scripts/            # 自动化脚本集合
│   ├── setup/          # 环境设置脚本
│   └── docker/         # Docker 管理脚本
├── plugins/            # 插件系统
│   ├── core/           # 插件核心
│   └── examples/       # 示例插件
├── docs/               # 文档
│   ├── api/            # API文档
│   ├── architecture/   # 架构文档
│   ├── guides/         # 使用指南
│   └── references/     # 参考资料
├── tests/              # 测试
│   ├── unit/           # 单元测试
│   ├── integration/    # 集成测试
│   └── e2e/            # 端到端测试
├── config/             # 全局配置
│   ├── environments/   # 环境配置
│   └── docker-compose.yml # Docker Compose配置
└── start.sh            # 主控脚本
```

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Electron 主进程                        │
│                                                             │
│ ┌─────────────────────┐         ┌─────────────────────────┐ │
│ │    Vue 3 + Vite     │◄─────►  │       Python 引擎       │ │
│ │  (前端渲染进程)     │         │     (后端处理逻辑)      │ │
│ └─────────────────────┘         └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼─────────────────────┐
        ▼                    ▼                     ▼
┌─────────────┐     ┌─────────────┐       ┌─────────────┐
│ 本地存储    │     │ 外部API     │       │ 数据库      │
│ 文件系统    │     │ 网络服务    │       │ SQLite/其他 │
└─────────────┘     └─────────────┘       └─────────────┘
```

### 数据流

1. 前端 Vue 应用通过 API 接口与 Python 后端通信
2. Python 后端处理业务逻辑并管理数据存储
3. Electron 主进程提供桌面集成能力和操作系统访问
4. 整个系统通过 Docker 容器相互隔离但保持通信

### 技术栈交互

```
┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │
│    Vue 3 前端   │◄─────►│   Python 后端   │
│                 │       │                 │
└────────┬────────┘       └────────┬────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │
│  状态管理(Pinia)│       │ 数据库操作(ORM) │
│                 │       │                 │
└────────┬────────┘       └────────┬────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │
│  UI组件(AntDV)  │       │   外部API集成   │
│                 │       │                 │
└─────────────────┘       └─────────────────┘
```

## 使用场景

Smoothstack适用于以下场景：

1. **全栈应用开发**：集成前端Vue和后端Python的项目
2. **数据分析应用**：需要强大数据处理和可视化能力的应用
3. **桌面应用程序**：通过Electron实现跨平台桌面软件
4. **中小型团队项目**：需要统一开发环境和标准化流程
5. **快速原型开发**：需要迅速搭建功能完整的应用原型
6. **多平台部署项目**：需要在不同环境中保持一致性

## 示例应用

Smoothstack提供了几个示例应用，展示如何使用框架的各种功能：

1. **基础应用模板**：最小化设置的全栈应用
   ```bash
   ./start.sh create-app --template basic
   ```

2. **数据可视化仪表盘**：展示数据分析和图表功能
   ```bash
   ./start.sh create-app --template dashboard
   ```

3. **多服务微应用**：展示多容器服务协作
   ```bash
   ./start.sh create-app --template microservices
   ```

## 扩展指南

Smoothstack的插件系统允许扩展和定制框架功能：

1. **创建插件**
   ```bash
   ./start.sh plugin create my-plugin
   ```

2. **激活插件**
   ```bash
   ./start.sh plugin enable my-plugin
   ```

3. **发布插件**
   ```bash
   ./start.sh plugin package my-plugin
   ```

更多信息请参考[插件开发文档](docs/plugins/development.md)。

## 开发规划亮点

- **版本控制与发布策略**: 遵循语义化版本控制，采用`main`、`develop`、`feature/*`、`bugfix/*`、`release/*`分支策略。
- **插件系统设计**: 提供核心插件、领域插件、工具插件和UI插件，支持标准化接口和生命周期钩子。
- **多容器管理模型**: 包括核心容器、应用容器、工具容器和策略容器，支持动态资源调整和健康监控。
- **跨平台兼容性**: 支持Windows、macOS、Linux，处理环境差异和文件系统权限。

## 文档链接

- [Smoothstack MVP 计划清单](docs/Smoothstack%20MVP%20计划清单.md)
- [Smoothstack 开发规划](docs/Smoothstack%20开发规划.md)

## 未来规划

- Storybook 组件开发与文档系统
- FastAPI 微服务架构支持
- Celery 异步任务队列集成
- SQLAlchemy ORM 支持
- ELK 日志监控栈
- 完善的测试与 CI/CD 流程
- 插件系统支持社区扩展
- 移动端支持(基于Capacitor或React Native)

## 贡献指南

我们欢迎各种形式的贡献，无论是功能请求、bug 报告还是代码贡献：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发流程

1. **环境设置**
   - 克隆仓库并设置开发环境
   - 确保Docker和所需依赖已安装

2. **添加功能**
   - 遵循项目的编码规范
   - 编写相应的测试用例
   - 更新文档以反映变更

3. **提交变更**
   - 使用清晰的提交信息
   - 关联相关的issue(如有)
   - 提交Pull Request并等待审核

## 许可证

本项目采用 [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE) 许可证。

## 作者信息

- **作者**: ohlcv
- **联系邮箱**: 24369961@qq.com
- **版权所有**: © 2025-至今 ohlcv. 保留所有权利。

## 致谢

感谢所有为本项目做出贡献的开发者和用户。你们的反馈和支持是项目持续改进的动力。