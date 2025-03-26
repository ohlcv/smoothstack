# Smoothstack Backend

基于 Python 的现代化后端开发框架，支持 FastAPI/Django/Flask。

## 技术栈

- **核心语言**: Python 3.11+
- **Web框架**: FastAPI (默认) / Django / Flask
- **ORM**: SQLAlchemy
- **数据库**: PostgreSQL / SQLite
- **缓存**: Redis
- **任务队列**: Celery
- **API文档**: Swagger UI / ReDoc
- **测试框架**: pytest
- **代码质量**: 
  - black (代码格式化)
  - flake8 (代码检查)
  - mypy (类型检查)

## 项目结构

```
backend/
├── api/              # API接口
│   ├── v1/          # API版本1
│   └── deps.py      # 依赖注入
├── core/            # 核心模块
│   ├── config.py    # 配置管理
│   ├── security.py  # 安全相关
│   └── events.py    # 事件处理
├── db/              # 数据库
│   ├── base.py      # 数据库基类
│   └── session.py   # 会话管理
├── models/          # 数据模型
│   └── base.py      # 基础模型
├── schemas/         # Pydantic模型
│   └── base.py      # 基础Schema
├── services/        # 业务服务
│   └── base.py      # 基础服务
├── tests/           # 测试文件
│   ├── api/        # API测试
│   └── services/   # 服务测试
├── utils/           # 工具函数
├── alembic/         # 数据库迁移
├── logs/            # 日志文件
├── .env            # 环境变量
├── main.py         # 应用入口
└── requirements.txt # 项目依赖
```

## 开发指南

### 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 开发规范

1. **代码风格**
- 使用black进行代码格式化
- 使用flake8进行代码检查
- 使用mypy进行类型检查
- 遵循PEP 8规范

2. **API开发**
- 使用FastAPI路由装饰器
- 实现请求验证
- 添加响应模型
- 编写API文档

3. **数据库操作**
- 使用SQLAlchemy ORM
- 实现数据库迁移
- 编写数据库种子
- 实现事务管理

4. **测试驱动开发**
- 编写单元测试
- 实现集成测试
- 使用测试夹具
- 生成测试报告

## API开发

### 路由定义

```python
from fastapi import APIRouter, Depends
from typing import List
from app.schemas.user import UserCreate, UserResponse
from app.services.user import UserService

router = APIRouter()

@router.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, service: UserService = Depends()):
    return await service.create(user)

@router.get("/users/", response_model=List[UserResponse])
async def list_users(service: UserService = Depends()):
    return await service.list()
```

### 依赖注入

```python
from fastapi import Depends
from app.db.session import get_db
from sqlalchemy.orm import Session

async def get_user_service(db: Session = Depends(get_db)):
    return UserService(db)
```

## 部署指南

### 环境变量配置

生产环境需要配置以下环境变量：
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://:password@host:6379/0
SECRET_KEY=your-secret-key
```

## 性能优化

1. **数据库优化**
- 使用数据库索引
- 实现查询缓存
- 优化ORM查询

2. **API优化**
- 实现响应缓存
- 使用异步处理
- 实现批量操作

3. **缓存策略**
- 使用Redis缓存
- 实现缓存预热
- 管理缓存失效

## 监控和日志

1. **应用监控**
- 使用Prometheus收集指标
- 使用Grafana展示仪表盘
- 实现健康检查接口

2. **日志管理**
- 使用结构化日志
- 实现日志轮转
- 集成ELK堆栈

## 安全措施

1. **认证授权**
- JWT认证
- OAuth2集成
- RBAC权限控制

2. **数据安全**
- 数据加密
- XSS防护
- CSRF防护

## 测试指南

1. **单元测试**
- API测试
- 服务测试
- 工具函数测试

2. **集成测试**
- 数据库集成测试
- 缓存集成测试
- 外部服务集成测试

## 常见问题

1. **开发环境问题**
- 数据库连接失败
- Redis连接错误
- 依赖冲突解决

2. **部署问题**
- Docker容器启动失败
- 数据库迁移错误
- 环境变量配置

## 贡献指南

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 创建Pull Request

## 许可证

本项目采用 [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE) 许可证。 