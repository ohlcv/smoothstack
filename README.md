# smoothstack

<p align="center">
  <img src="assets/logo.png" alt="smoothstack Logo" width="200" />
</p>

<p align="center">
  <strong>现代化全栈应用开发框架 | Modern Full-Stack Application Development Framework</strong>
</p>

<p align="center">
  <a href="#核心特性">核心特性</a> •
  <a href="#技术栈">技术栈</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#架构概览">架构概览</a> •
  <a href="#使用场景">使用场景</a> •
  <a href="#示例应用">示例应用</a> •
  <a href="#扩展指南">扩展指南</a> •
  <a href="#贡献指南">贡献指南</a>
</p>

## 项目愿景

smoothstack 致力于解决全栈开发中的环境配置痛点，让开发者将精力集中在业务逻辑实现上，而非繁琐的环境搭建与依赖管理。通过 Docker 容器化技术和自动化脚本，提供一键式开发环境部署，实现「**配置即代码**」的开发理念。

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

虽然smoothstack的底层实现已经从Bash脚本迁移到了Python (基于[重构方案](docs/重构方案.md))，但我们仍然保留了`start.sh`作为用户接口入口点，以提供平滑的过渡体验：

- **底层实现**: 所有核心功能均由Python模块实现，提供更好的跨平台兼容性和功能扩展性
- **命令接口**: 保留Shell脚本作为简单入口点，内部调用Python实现
- **为什么这样做**: 确保向后兼容性，让现有用户和自动化脚本无需立即调整
- **未来发展**: 长期计划提供纯Python CLI命令 (`vuepy` 或 `python -m vuepy_cli`)

**技术实现**:
```bash
# start.sh 内部实际上执行的是
python -m vuepy_cli "$@"
```

## 容器化开发与依赖管理

smoothstack 提供了先进的容器化开发体验和精细的依赖管理能力：

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

- **源管理配置**：
  ```bash
  # 查看当前源配置
  ./start.sh deps sources list
  
  # 添加自定义源
  ./start.sh deps sources add custom https://custom.pypi.org/simple
  
  # 设置源优先级
  ./start.sh deps sources priority tsinghua 1
  
  # 测试源连接
  ./start.sh deps sources test tsinghua
  ```

- **网络诊断工具**：
  ```bash
  # 测试网络连接
  ./start.sh deps network test
  
  # 诊断源连接问题
  ./start.sh deps network diagnose tsinghua
  
  # 查看下载速度统计
  ./start.sh deps network stats
  ```

- **故障排除指南**：
  - 网络连接问题
  - 源访问问题
  - 依赖冲突解决
  - 版本兼容性问题
  - 代理配置问题
  ```bash
  # 运行网络诊断
  ./start.sh deps troubleshoot network
  
  # 运行依赖诊断
  ./start.sh deps troubleshoot deps
  
  # 查看详细日志
  ./start.sh deps logs --verbose
  ```

### 多容器策略管理

- **独立策略容器**：支持为不同策略创建独立的容器实例
  - 每个交易策略可在独立容器中运行，实现资源隔离
  - 支持策略容器间的安全通信和数据共享
- **批量容器操作**：提供管理多个容器的批量操作命令
  - 批量启动: `./start.sh strategies start-all`
  - 批量监控: `./start.sh strategies monitor`
  - 选择性操作: `./start.sh strategies start grid-strategy-1 grid-strategy-2`
- **容器资源控制**：为每个策略容器精确分配CPU、内存和存储资源
- **状态持久化**：支持策略状态的持久化存储和灾难恢复
- **集中化监控**：统一监控所有策略容器的运行状态、资源使用和日志

## 架构概览

smoothstack 采用模块化、松耦合架构设计，确保各组件可独立开发与测试：

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
├── docker-compose.yml  # Docker Compose 配置
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

smoothstack 适用于多种开发场景：

### 1. 数据分析应用

结合 Vue 的交互能力与 Python 的数据处理优势，快速构建数据可视化应用。
- 利用Python科学计算生态(NumPy, Pandas)处理数据
- 通过ECharts创建专业的数据可视化界面
- 支持实时数据更新和交互式分析

### 2. 企业内部工具

利用 Electron 打包能力，构建跨平台桌面应用，满足企业内部工具需求。
- 本地数据处理和存储，保障数据安全
- 结合企业认证系统，提供安全访问
- 自动更新机制确保工具始终为最新版本

### 3. Web 应用原型

快速启动新项目，5分钟内从想法到可运行的全栈原型。
- 使用现成的UI组件快速构建界面
- 灵活的后端API支持各种数据服务
- Docker容器确保开发和演示环境一致

### 4. 教育与培训

为全栈开发培训提供统一的环境，消除环境差异导致的学习障碍。
- 标准化的开发环境降低学习门槛
- 完整的技术栈覆盖前后端知识点
- 实例项目提供实践学习机会

### 5. 多策略交易系统

为加密货币或传统金融市场构建强大的交易系统。
- 多容器隔离的交易策略，确保单个策略崩溃不影响整体系统
- 集中化监控和管理界面，简化操作
- 统一日志和性能指标，便于分析和优化
- 灵活的资源分配，根据策略重要性调整资源

## 示例应用

本框架包含一个功能完整的加密货币网格交易系统作为示例应用，展示框架的实际应用能力：

### 加密货币网格交易系统

- **功能特点**：
  - 动态网格策略管理与优化
  - 多层风控系统，保障交易安全
  - 实时数据可视化与分析
  - 多交易所API集成
  - 自动化交易执行
  
- **技术亮点**：
  - 利用Python处理复杂的金融计算
  - 使用ECharts展示价格走势和交易记录
  - Electron确保桌面应用性能和安全性
  - SQLite本地数据库存储交易记录和配置
  - 通过Docker容器实现与交易所API的安全通信

<p align="center">
  <em>示例应用界面(示意图)</em>
</p>

> 注意：示例应用仅作为框架能力展示，不建议直接用于实盘交易。您可以基于此框架开发自己的应用。

## 与传统开发流程对比

| 开发环节   | 传统方式                     | smoothstack                   |
| ---------- | ---------------------------- | ----------------------------- |
| 环境搭建   | 手动安装各组件，解决依赖冲突 | 一键初始化，Docker 容器化隔离 |
| 依赖管理   | 前后端分别维护依赖           | 统一依赖管理，自动检测冲突    |
| 多环境支持 | 手动切换环境配置             | 环境配置文件分离，一键切换    |
| 团队协作   | "在我电脑上能跑"             | 容器化确保环境一致性          |
| 部署流程   | 复杂的手动部署步骤           | 简化的构建与部署流程          |
| 跨语言集成 | 需要手动配置前后端通信       | 内置JavaScript-Python桥接     |
| 测试流程   | 需配置多套测试环境           | 统一测试框架和环境            |

## 扩展指南

smoothstack 设计为高度可扩展的框架，您可以根据项目需求扩展各个方面：

### 前端扩展

1. **添加新UI组件库**
   ```bash
   # 安装新的UI组件库
   npm install new-ui-framework
   
   # 在main.js中注册
   import NewUI from 'new-ui-framework'
   app.use(NewUI)
   ```

2. **集成额外的状态管理工具**
   - 除了Pinia，您还可以集成Redux、MobX等状态管理库
   - 框架的模块化设计允许轻松替换或并行使用多种状态管理方案

3. **扩展数据可视化能力**
   - 除ECharts外，可集成D3.js、Highcharts等可视化库
   - 支持WebGL基于的3D可视化方案

### 后端扩展

1. **切换到高性能Web框架**
   - 集成FastAPI创建高性能REST API
   - 添加Django用于更复杂的后端服务
   - 使用Flask创建轻量级微服务

2. **数据库扩展**
   - 从默认的SQLite迁移到PostgreSQL、MySQL等生产级数据库
   - 集成MongoDB等NoSQL数据库支持
   - 添加Redis用于缓存和会话管理

3. **添加异步任务支持**
   - 集成Celery处理后台任务
   - 实现定时任务和批处理功能
   - 构建消息队列系统

### 部署扩展

1. **云服务部署**
   - AWS部署指南和自动化脚本
   - Azure和Google Cloud Platform支持
   - 阿里云等国内云平台部署方案

2. **容器编排**
   - Kubernetes配置和部署指南
   - Docker Swarm集群设置
   - 微服务架构的容器编排

3. **持续集成/持续部署**
   - GitHub Actions工作流配置
   - Jenkins流水线设置
   - GitLab CI/CD集成

## 未来规划

smoothstack 正在积极开发中，计划引入以下增强功能：

- Storybook 组件开发与文档系统
- FastAPI 微服务架构支持
- Celery 异步任务队列集成
- SQLAlchemy ORM 支持
- ELK 日志监控栈
- 完善的测试与 CI/CD 流程
- 插件系统支持社区扩展
- 移动端支持(基于Capacitor或React Native)

完整规划请参考 [重构方案](docs/重构方案.md) 和 [重构计划清单](docs/重构计划清单.md)。

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

本项目基于 [MIT 许可证](LICENSE) 开源。

## 致谢

感谢所有为本项目做出贡献的开发者和用户。你们的反馈和支持是项目持续改进的动力。 