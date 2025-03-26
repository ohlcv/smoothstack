以下是针对你的需求定制的“加密货币网格交易系统最小 MVP（Minimum Viable Product）验证文档”。这个 MVP 旨在验证你的技术栈（基于 Node.js 官方镜像 `node:20-slim`）、部署环境（Windows 11 + Docker）、测试方案、打包分发全流程，确保所有依赖版本正确配置并正常使用，项目架构和数据流顺利流转，最终打包为 `.exe` 方便分发。这将为你的正式开发奠定基础。

---

# 加密货币网格交易系统 MVP 验证文档

## 1. 目标与范围

### 1.1 验证目标
- **技术栈可行性**：验证 Electron 24+、Vue 3.3+、TypeScript 5.0+、Ant Design Vue 4.0+、Python 3.10+、SQLite、python-shell、ECharts 5.4+、Pinia 2.1+、Vite 4.0+、Hummingbot 的正确版本配置和正常运行。
- **架构与数据流**：确认主客户端（Electron + Vue3 + Python）和 Hummingbot 容器之间的数据流转顺畅。
- **打包分发**：验证能否打包为 `.exe`，用户无需配置 Docker 即可运行。

### 1.2 MVP 范围
- **功能**：
  - 一个简单的网格策略配置界面（选择交易所和交易对）。
  - 调用 Python 引擎生成配置。
  - 创建一个 Hummingbot 容器并显示状态。
  - 显示简单的交易监控数据（模拟）。
- **不包含**：
  - 完整的网格策略逻辑、风控系统、服务端 API（留待正式开发）。

---

## 2. 技术栈与依赖

### 2.1 客户端技术栈
| 技术           | 版本   | 作用                                 |
| -------------- | ------ | ------------------------------------ |
| Electron       | 24.0.0 | 跨平台桌面应用框架                   |
| Vue 3          | 3.3.0  | 响应式 UI 框架                       |
| TypeScript     | 5.0.0  | 类型安全                             |
| Ant Design Vue | 4.0.0  | UI 组件库                            |
| Python         | 3.10   | 核心引擎，处理策略和 Hummingbot 管理 |
| SQLite         | 内置   | 本地数据存储（MVP 仅测试连接）       |
| python-shell   | 1.0.0  | Electron 与 Python 通信              |
| ECharts        | 5.4.0  | 数据可视化（简单图表）               |
| Pinia          | 2.1.0  | 状态管理                             |
| Vite           | 4.0.0  | 前端构建工具                         |

### 2.2 Hummingbot 组件
- 使用官方镜像 `hummingbot/hummingbot:latest`，包含交易所连接器、订单管理等。

### 2.3 部署环境
- **操作系统**：Windows 11
- **工具**：
  - Docker Desktop（最新版）
  - Node.js（仅用于验证镜像构建，实际依赖由 Docker 提供）
  - Git（代码管理）

---

## 3. 项目结构

```
crypto-grid-mvp/
├── client/
│   ├── src/
│   │   ├── main/                    # Electron 主进程
│   │   │   ├── index.js             # 主进程入口
│   │   │   └── python-bridge.js     # Python 通信
│   │   ├── renderer/                # Vue3 前端
│   │   │   ├── App.vue              # 根组件
│   │   │   ├── main.ts              # 渲染进程入口
│   │   │   ├── components/          # 组件
│   │   │   │   └── StrategyForm.vue # 策略配置表单
│   │   │   ├── store/               # Pinia
│   │   │   │   └── strategy.ts      # 策略状态
│   │   └── python/                  # Python 引擎
│   │       ├── main.py              # 引擎入口
│   │       └── hummingbot_manager.py# Hummingbot 管理
│   ├── Dockerfile                   # 主客户端容器配置
│   ├── package.json                 # 前端依赖
│   ├── tsconfig.json                # TypeScript 配置
│   ├── vite.config.ts               # Vite 配置
│   └── requirements.txt             # Python 依赖
├── dist/                            # 打包输出目录
├── docker-compose.yml               # 开发环境配置
└── README.md                        # 说明文档
```

---

## 4. 部署环境搭建

### 4.1 安装 Docker Desktop
- **步骤**：
  1. 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)。
  2. 安装并启用 WSL 2（Windows Subsystem for Linux），按提示配置。
  3. 启动 Docker Desktop，验证：
     ```bash
     docker --version  # 输出如 "Docker version 24.0.7"
     ```

### 4.2 创建项目
- **命令**：
  ```bash
  mkdir crypto-grid-mvp
  cd crypto-grid-mvp
  mkdir client
  git init  # 可选，用于版本控制
  ```

---

## 5. 开发配置

### 5.1 主客户端容器配置
- **Dockerfile**（`client/Dockerfile`）：
  ```dockerfile
  FROM node:20-slim
  WORKDIR /app
  # 安装 Electron GUI 依赖和 Python
  RUN apt-get update && apt-get install -y \
      libx11-xcb1 libgtk-3-0 python3 python3-pip
  # 前端依赖
  COPY client/package.json client/package-lock.json ./
  RUN npm install
  # Python 依赖
  COPY client/requirements.txt ./
  RUN pip3 install -r requirements.txt
  # 项目代码
  COPY client/ ./
  # 构建前端
  RUN npm run build
  CMD ["npm", "run", "electron"]
  ```

- **package.json**（`client/package.json`）：
  ```json
  {
    "name": "crypto-grid-mvp",
    "version": "1.0.0",
    "main": "src/main/index.js",
    "scripts": {
      "dev": "vite",
      "build": "vite build",
      "electron": "electron .",
      "package": "electron-builder --win --x64"
    },
    "dependencies": {
      "vue": "^3.3.0",
      "ant-design-vue": "^4.0.0",
      "echarts": "^5.4.0",
      "pinia": "^2.1.0",
      "python-shell": "^1.0.0"
    },
    "devDependencies": {
      "electron": "^24.0.0",
      "vite": "^4.0.0",
      "@vitejs/plugin-vue": "^4.0.0",
      "typescript": "^5.0.0",
      "electron-builder": "^24.0.0"
    },
    "build": {
      "appId": "com.example.cryptogrid",
      "win": {
        "target": "nsis"
      },
      "files": [
        "dist/**/*",
        "src/main/**/*",
        "src/python/**/*"
      ],
      "extraResources": [
        "src/python/**/*"
      ]
    }
  }
  ```

- **requirements.txt**（`client/requirements.txt`）：
  ```
  requests==2.31.0
  ```

### 5.2 前端代码
- **tsconfig.json**（`client/tsconfig.json`）：
  ```json
  {
    "compilerOptions": {
      "target": "esnext",
      "module": "esnext",
      "strict": true,
      "jsx": "preserve",
      "moduleResolution": "node"
    }
  }
  ```

- **vite.config.ts**（`client/vite.config.ts`）：
  ```typescript
  import { defineConfig } from 'vite';
  import vue from '@vitejs/plugin-vue';

  export default defineConfig({
    plugins: [vue()],
    server: { port: 3000 }
  });
  ```

- **main.ts**（`client/src/renderer/main.ts`）：
  ```typescript
  import { createApp } from 'vue';
  import App from './App.vue';
  import Antd from 'ant-design-vue';
  import 'ant-design-vue/dist/reset.css';
  import { createPinia } from 'pinia';

  createApp(App).use(Antd).use(createPinia).mount('#app');
  ```

- **App.vue**（`client/src/renderer/App.vue`）：
  ```vue
  <template>
    <a-form :model="form" @finish="createStrategy">
      <a-form-item label="交易所">
        <a-select v-model:value="form.exchange">
          <a-select-option value="binance">Binance</a-select-option>
          <a-select-option value="kucoin">KuCoin</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="交易对">
        <a-input v-model:value="form.pair" placeholder="如 BTC-USDT" />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit">创建策略</a-button>
      </a-form-item>
    </a-form>
    <div v-if="status">状态: {{ status }}</div>
    <div id="chart" style="width: 600px; height: 400px;"></div>
  </template>

  <script lang="ts">
  import { defineComponent } from 'vue';
  import { useStrategyStore } from './store/strategy';
  import * as echarts from 'echarts';

  export default defineComponent({
    data() {
      return {
        form: { exchange: 'binance', pair: '' },
        status: ''
      };
    },
    mounted() {
      const chart = echarts.init(document.getElementById('chart') as HTMLElement);
      chart.setOption({
        xAxis: { type: 'category', data: ['1', '2', '3'] },
        yAxis: { type: 'value' },
        series: [{ data: [10, 20, 15], type: 'line' }]
      });
    },
    methods: {
      async createStrategy() {
        const store = useStrategyStore();
        this.status = await store.createStrategy(this.form.exchange, this.form.pair);
      }
    }
  });
  </script>
  ```

- **StrategyForm.vue**（`client/src/renderer/components/StrategyForm.vue`）：
  ```vue
  <!-- 可留空，MVP 使用 App.vue 中的表单 -->
  ```

- **strategy.ts**（`client/src/renderer/store/strategy.ts`）：
  ```typescript
  import { defineStore } from 'pinia';
  import { python } from 'python-shell';

  export const useStrategyStore = defineStore('strategy', {
    state: () => ({ status: '' }),
    actions: {
      async createStrategy(exchange: string, pair: string) {
        const result = await python('src/python/main.py', exchange, pair);
        this.status = result || `Created ${exchange}:${pair}`;
        return this.status;
      }
    }
  });
  ```

### 5.3 主进程与 Python 集成
- **index.js**（`client/src/main/index.js`）：
  ```javascript
  const { app, BrowserWindow } = require('electron');
  const path = require('path');
  const { spawn } = require('child_process');

  let pythonProcess;

  function createWindow() {
    const win = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: { nodeIntegration: true, contextIsolation: false }
    });
    win.loadURL('http://localhost:3000');

    pythonProcess = spawn('python3', [path.join(__dirname, '../python/main.py')]);
    pythonProcess.stdout.on('data', (data) => console.log(`Python: ${data}`));
  }

  app.whenReady().then(createWindow);
  app.on('window-all-closed', () => {
    if (pythonProcess) pythonProcess.kill();
    if (process.platform !== 'darwin') app.quit();
  });
  ```

- **main.py**（`client/src/python/main.py`）：
  ```python
  import sys
  import docker
  import os

  client = docker.from_client()

  def create_hummingbot(exchange, pair):
      strategy_id = f"{exchange}_{pair.replace('-', '')}"
      config_dir = f"strategy_files/{strategy_id}"
      os.makedirs(config_dir, exist_ok=True)
      with open(f"{config_dir}/conf_grid.yml", "w") as f:
          f.write(f"exchange: {exchange}\ntrading_pair: {pair}\n")
      container_name = f"hummingbot_{strategy_id}"
      try:
          client.containers.run(
              "hummingbot/hummingbot:latest",
              name=container_name,
              detach=True,
              volumes={os.path.abspath(config_dir): {"bind": "/conf", "mode": "rw"}}
          )
          return f"Container {container_name} started"
      except Exception as e:
          return str(e)

  if __name__ == "__main__":
      if len(sys.argv) == 3:
          exchange, pair = sys.argv[1], sys.argv[2]
          print(create_hummingbot(exchange, pair))
      else:
          print("Python engine running")
  ```

### 5.4 Docker Compose
- **docker-compose.yml**：
  ```yaml
  version: "3.9"
  services:
    client:
      build:
        context: .
        dockerfile: client/Dockerfile
      volumes:
        - ./client:/app
        - ./strategy_files:/app/strategy_files
      ports:
        - "3000:3000"
  ```

---

## 6. 测试方案

### 6.1 部署测试
- **步骤**：
  1. 运行 `docker-compose up --build`。
  2. 检查 Docker Desktop，确认 `client` 容器运行。
- **预期**：容器启动无错误。

### 6.2 技术栈验证
- **Electron + Vue3 + Ant Design Vue**：
  - 修改 `CMD` 为 `["npm", "run", "electron"]`，重启容器。
  - 预期：窗口显示表单。
- **TypeScript**：
  - 检查 `main.ts` 和 `strategy.ts` 无编译错误。
- **Pinia**：
  - 点击“创建策略”，状态更新。
- **python-shell**：
  - 点击按钮，控制台输出 Python 结果。
- **ECharts**：
  - 页面显示简单折线图。
- **Python + SQLite**：
  - 添加 SQLite 测试（可选）：
    ```python
    import sqlite3
    conn = sqlite3.connect(':memory:')
    conn.close()
    ```
- **Hummingbot**：
  - 输入“binance”和“BTC-USDT”，检查 Docker Desktop 是否创建 `hummingbot_binance_BTCUSDT`。

### 6.3 数据流验证
- **流程**：
  1. 用户输入策略（Vue3 UI）。
  2. Pinia 调用 Python（python-shell）。
  3. Python 创建 Hummingbot 容器。
  4. 返回状态更新 UI。
- **预期**：状态显示“Container hummingbot_xxx started”。

---

## 7. 打包分发全流程

### 7.1 调整 Dockerfile
- **client/Dockerfile**（打包用）：
  ```dockerfile
  FROM node:20-slim
  WORKDIR /app
  RUN apt-get update && apt-get install -y \
      libx11-xcb1 libgtk-3-0 python3 python3-pip
  COPY client/package.json client/package-lock.json ./
  RUN npm install
  COPY client/requirements.txt ./
  RUN pip3 install -r requirements.txt
  COPY client/ ./
  RUN npm run build
  RUN npm run package
  ```

### 7.2 构建与打包
- **命令**：
  ```bash
  docker build -t crypto-grid-mvp-builder -f client/Dockerfile .
  docker run --rm -v %CD%/dist:/app/dist crypto-grid-mvp-builder
  ```
- **结果**：`dist` 目录下生成 `crypto-grid-mvp-1.0.0.exe`。

### 7.3 分发
- **包内容**：
  - `crypto-grid-mvp-1.0.0.exe`
  - `strategy_files/`（Hummingbot 配置）
  - `src/python/`（Python 脚本）
- **压缩**：
  ```bash
  tar -cvf crypto-grid-mvp.tar dist strategy_files client/src/python
  ```
- **用户运行**：
  - 解压，双击 `.exe`，无需 Docker。

### 7.4 注意事项
- **Python 依赖**：用户需安装 Python 3.10，或使用 `PyInstaller` 将 `main.py` 打包为 `.exe`。
- **Hummingbot**：MVP 仅验证容器创建，正式版需嵌入 Hummingbot 或提供安装说明。

---

## 8. 验证结果

### 8.1 成功标准
- 所有依赖版本正确安装并运行。
- Electron 窗口显示 UI，数据流转正常。
- `.exe` 文件在 Windows 11 上双击运行成功。

### 8.2 下一步
- 扩展网格策略逻辑。
- 集成服务端（Django）。
- 优化 Hummingbot 管理。

---

这个 MVP 文档提供了从开发到分发的完整流程，适合 Windows 11 和你的技术栈。如果需要具体调试（例如打包失败），请告诉我，我会进一步协助！