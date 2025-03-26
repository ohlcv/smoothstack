# Smoothstack Frontend

基于 Vue 3 + TypeScript + Vite 的现代化前端开发框架。

## 技术栈

- **核心框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI框架**: Ant Design Vue
- **状态管理**: Pinia
- **路由管理**: Vue Router
- **HTTP客户端**: Axios
- **工具库**: 
  - lodash (工具函数)
  - dayjs (日期处理)
  - echarts (数据可视化)
- **CSS预处理**: SCSS
- **国际化**: Vue I18n
- **组合式API工具**: VueUse

## 项目结构

```
frontend/
├── src/                # 源代码目录
│   ├── assets/        # 静态资源
│   ├── components/    # 通用组件
│   ├── composables/   # 组合式函数
│   ├── config/        # 配置文件
│   ├── hooks/         # 自定义钩子
│   ├── i18n/          # 国际化资源
│   ├── layouts/       # 布局组件
│   ├── router/        # 路由配置
│   ├── services/      # API服务
│   ├── stores/        # 状态管理
│   ├── styles/        # 全局样式
│   ├── types/         # TypeScript类型
│   ├── utils/         # 工具函数
│   └── views/         # 页面组件
├── public/            # 公共资源
├── tests/             # 测试文件
│   ├── unit/         # 单元测试
│   └── e2e/          # 端到端测试
├── .env              # 环境变量
├── index.html        # HTML模板
├── package.json      # 项目配置
├── tsconfig.json     # TypeScript配置
└── vite.config.ts    # Vite配置

```

## 开发指南

### 环境要求

- Node.js 18+
- npm 8+ 或 yarn 1.22+

### 开发环境设置

1. **安装依赖**
```bash
# 使用框架CLI工具
./cli.py deps install frontend

# 或直接使用npm
npm install
```

2. **启动开发服务器**
```bash
# 使用框架CLI工具
./cli.py frontend run

# 或直接使用npm
npm run dev
```

3. **构建生产版本**
```bash
# 使用框架CLI工具
./cli.py frontend build

# 或直接使用npm
npm run build
```

### 开发规范

1. **组件开发**
- 使用组合式API (Composition API)
- 按功能模块组织组件
- 使用TypeScript类型注解

2. **状态管理**
- 使用Pinia进行状态管理
- 按领域模型组织store
- 使用组合式store模式

3. **样式指南**
- 使用SCSS预处理器
- 遵循BEM命名规范
- 使用主题变量系统

4. **国际化**
- 使用Vue I18n管理多语言
- 按语言代码组织翻译文件
- 支持按需加载语言包

### 常用命令

```bash
# 开发
npm run dev           # 启动开发服务器
npm run build        # 构建生产版本
npm run preview      # 预览生产版本

# 测试
npm run test:unit    # 运行单元测试
npm run test:e2e     # 运行端到端测试
npm run coverage     # 生成测试覆盖报告

# 代码质量
npm run lint         # 运行代码检查
npm run format       # 格式化代码
```

### Docker支持

项目提供完整的Docker支持，可以在容器中进行开发：

```bash
# 使用框架CLI工具
./cli.py docker up web          # 启动前端容器
./cli.py docker logs web       # 查看前端日志
./cli.py docker exec web sh    # 进入前端容器

# 依赖管理
./cli.py deps install frontend vue@latest  # 安装新依赖
./cli.py deps update frontend              # 更新所有依赖
```

## API集成

### 配置API客户端

在 `src/services/api.ts` 中配置API客户端：

```typescript
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
})
```

### 使用API服务

在 `src/services` 目录下按领域创建API服务：

```typescript
// src/services/userService.ts
import { api } from './api'

export const userService = {
  async getProfile() {
    const { data } = await api.get('/user/profile')
    return data
  }
}
```

## 部署指南

1. **构建生产版本**
```bash
./cli.py frontend build
```

2. **使用Docker部署**
```bash
./cli.py docker build web
./cli.py docker push web
```

3. **环境变量配置**

生产环境需要配置以下环境变量：
- `VITE_API_URL`: API服务地址
- `NODE_ENV`: 运行环境(production)

## 性能优化

1. **代码分割**
- 路由级别的组件动态导入
- 第三方库按需加载
- 使用动态导入实现按需加载

2. **资源优化**
- 图片资源压缩和CDN部署
- 使用现代图片格式(webp)
- 实现资源预加载策略

3. **缓存策略**
- 合理使用浏览器缓存
- 实现API响应缓存
- 使用Service Worker缓存静态资源

## 测试指南

1. **单元测试**
```bash
# 运行所有测试
npm run test:unit

# 运行特定测试文件
npm run test:unit path/to/test.spec.ts

# 监视模式
npm run test:unit:watch
```

2. **端到端测试**
```bash
# 运行所有E2E测试
npm run test:e2e

# 开发模式
npm run test:e2e:dev
```

## 常见问题

1. **开发环境问题**
- 端口冲突：修改 `vite.config.ts` 中的端口配置
- 热重载失效：检查文件监听限制
- 依赖安装失败：尝试清除npm缓存

2. **构建问题**
- 构建失败：检查Node.js版本兼容性
- 资源引用错误：检查公共路径配置
- 内存不足：增加Node.js内存限制

## 贡献指南

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用 [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE) 许可证。 