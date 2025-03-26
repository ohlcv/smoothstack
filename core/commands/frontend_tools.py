"""
前端工具命令类
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from .base import BaseCommand


class FrontendToolsCommand(BaseCommand):
    """前端工具命令类，提供通用的前端开发工具"""

    def __init__(self):
        super().__init__()
        self.frontend_dir = self.project_root / "frontend"
        self.templates_dir = self.project_root / "templates" / "frontend"

    def create_app(self, name: str, template: str = "vue"):
        """创建新的前端应用

        Args:
            name: 应用名称
            template: 模板类型 (vue/react)
        """
        self.info(f"创建{template}应用: {name}")
        try:
            # 检查模板
            template_dir = self.templates_dir / template
            if not template_dir.exists():
                raise ValueError(f"模板不存在: {template}")

            # 创建应用目录
            app_dir = self.frontend_dir / name
            if app_dir.exists():
                raise ValueError(f"应用已存在: {name}")

            # 复制模板
            self.copy_item(str(template_dir), str(app_dir))

            # 替换模板变量
            self._replace_template_vars(
                app_dir, {"APP_NAME": name, "PROJECT_NAME": self.project_root.name}
            )

            # 安装依赖
            os.chdir(str(app_dir))
            os.system("npm install")

            self.success(f"应用创建成功: {name}")
        except Exception as e:
            self.error(f"创建应用失败: {str(e)}")
            raise

    def add_component(self, name: str, type: str = "functional"):
        """添加组件

        Args:
            name: 组件名称
            type: 组件类型 (functional/class)
        """
        self.info(f"添加组件: {name}")
        try:
            components_dir = self.frontend_dir / "src" / "components"
            components_dir.mkdir(exist_ok=True)

            # 创建组件文件
            component_file = components_dir / f"{name}.vue"
            if component_file.exists():
                raise ValueError(f"组件已存在: {name}")

            # 生成组件代码
            component_template = self._get_component_template(name, type)
            with open(component_file, "w", encoding="utf-8") as f:
                f.write(component_template)

            # 创建样式文件
            style_file = components_dir / f"{name}.scss"
            with open(style_file, "w", encoding="utf-8") as f:
                f.write(self._get_style_template(name))

            self.success(f"组件添加成功: {name}")
        except Exception as e:
            self.error(f"添加组件失败: {str(e)}")
            raise

    def add_view(self, name: str):
        """添加视图

        Args:
            name: 视图名称
        """
        self.info(f"添加视图: {name}")
        try:
            views_dir = self.frontend_dir / "src" / "views"
            views_dir.mkdir(exist_ok=True)

            # 创建视图文件
            view_file = views_dir / f"{name}.vue"
            if view_file.exists():
                raise ValueError(f"视图已存在: {name}")

            # 生成视图代码
            view_template = self._get_view_template(name)
            with open(view_file, "w", encoding="utf-8") as f:
                f.write(view_template)

            # 更新路由
            self._update_router(name)

            self.success(f"视图添加成功: {name}")
        except Exception as e:
            self.error(f"添加视图失败: {str(e)}")
            raise

    def add_store(self, name: str):
        """添加状态管理

        Args:
            name: Store名称
        """
        self.info(f"添加Store: {name}")
        try:
            stores_dir = self.frontend_dir / "src" / "stores"
            stores_dir.mkdir(exist_ok=True)

            # 创建store文件
            store_file = stores_dir / f"{name}.ts"
            if store_file.exists():
                raise ValueError(f"Store已存在: {name}")

            # 生成store代码
            store_template = self._get_store_template(name)
            with open(store_file, "w", encoding="utf-8") as f:
                f.write(store_template)

            self.success(f"Store添加成功: {name}")
        except Exception as e:
            self.error(f"添加Store失败: {str(e)}")
            raise

    def add_api(self, name: str):
        """添加API服务

        Args:
            name: API服务名称
        """
        self.info(f"添加API服务: {name}")
        try:
            api_dir = self.frontend_dir / "src" / "api"
            api_dir.mkdir(exist_ok=True)

            # 创建API文件
            api_file = api_dir / f"{name}.ts"
            if api_file.exists():
                raise ValueError(f"API服务已存在: {name}")

            # 生成API代码
            api_template = self._get_api_template(name)
            with open(api_file, "w", encoding="utf-8") as f:
                f.write(api_template)

            self.success(f"API服务添加成功: {name}")
        except Exception as e:
            self.error(f"添加API服务失败: {str(e)}")
            raise

    def run_dev(self, port: int = 3000):
        """运行开发服务器

        Args:
            port: 端口号
        """
        self.info("启动开发服务器")
        try:
            os.chdir(str(self.frontend_dir))
            os.system(f"npm run dev -- --port {port}")
        except Exception as e:
            self.error(f"启动开发服务器失败: {str(e)}")
            raise

    def build(self, mode: str = "production"):
        """构建项目

        Args:
            mode: 构建模式 (production/development)
        """
        self.info(f"构建项目: {mode}")
        try:
            os.chdir(str(self.frontend_dir))
            os.system(f"npm run build -- --mode {mode}")
        except Exception as e:
            self.error(f"构建项目失败: {str(e)}")
            raise

    def _replace_template_vars(self, directory: Path, vars: dict):
        """替换模板变量"""
        for file in directory.rglob("*"):
            if file.is_file():
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()

                for key, value in vars.items():
                    content = content.replace(f"${{{key}}}", value)

                with open(file, "w", encoding="utf-8") as f:
                    f.write(content)

    def _get_component_template(self, name: str, type: str = "functional") -> str:
        """获取组件模板"""
        if type == "functional":
            return f"""<template>
  <div class="{name}">
    {{{{ message }}}}
  </div>
</template>

<script lang="ts" setup>
import {{ ref }} from 'vue'

const message = ref('Hello from {name}!')
</script>

<style lang="scss" scoped>
@import './{name}.scss';
</style>
"""
        else:
            return f"""<template>
  <div class="{name}">
    {{{{ message }}}}
  </div>
</template>

<script lang="ts">
import {{ defineComponent }} from 'vue'

export default defineComponent({{
  name: '{name}',
  data() {{
    return {{
      message: 'Hello from {name}!'
    }}
  }}
}})
</script>

<style lang="scss" scoped>
@import './{name}.scss';
</style>
"""

    def _get_style_template(self, name: str) -> str:
        """获取样式模板"""
        return f"""// {name} styles
.{name} {{
  // Add your styles here
}}
"""

    def _get_view_template(self, name: str) -> str:
        """获取视图模板"""
        return f"""<template>
  <div class="{name}-view">
    <h1>{name}</h1>
  </div>
</template>

<script lang="ts" setup>
import {{ onMounted }} from 'vue'

onMounted(() => {{
  console.log('{name} view mounted')
}})
</script>

<style lang="scss" scoped>
.{name}-view {{
  padding: 20px;
}}
</style>
"""

    def _get_store_template(self, name: str) -> str:
        """获取Store模板"""
        return f"""import {{ defineStore }} from 'pinia'

export const use{name}Store = defineStore('{name}', {{
  state: () => ({{
    // Define your state here
  }}),
  
  getters: {{
    // Define your getters here
  }},
  
  actions: {{
    // Define your actions here
  }}
}})
"""

    def _get_api_template(self, name: str) -> str:
        """获取API模板"""
        return f"""import {{ http }} from '@/utils/http'

export const {name}Api = {{
  getList: () => http.get('/{name.lower()}s'),
  getById: (id: number) => http.get(`/{name.lower()}s/${{id}}`),
  create: (data: any) => http.post('/{name.lower()}s', data),
  update: (id: number, data: any) => http.put(`/{name.lower()}s/${{id}}`, data),
  delete: (id: number) => http.delete(`/{name.lower()}s/${{id}}`)
}}
"""

    def _update_router(self, name: str):
        """更新路由配置"""
        router_file = self.frontend_dir / "src" / "router" / "index.ts"
        if not router_file.exists():
            return

        with open(router_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 添加路由导入
        import_str = f"import {name}View from '@/views/{name}.vue'"
        if import_str not in content:
            content = import_str + "\n" + content

        # 添加路由配置
        route_str = f"""  {{
    path: '/{name.lower()}',
    name: '{name}',
    component: {name}View
  }},"""

        if route_str not in content:
            content = content.replace("routes: [", f"routes: [\n{route_str}")

        with open(router_file, "w", encoding="utf-8") as f:
            f.write(content)
