# 加密货币网格交易系统API设计文档

## 1. 概述

本文档详细描述加密货币网格交易系统的API设计，包括RESTful API和WebSocket API。这些API是前端应用与后端系统之间的通信桥梁，为用户提供网格策略配置、交易执行、数据分析等功能。

### 1.1 设计原则

- **RESTful设计**：遵循RESTful API设计原则
- **版本控制**：API路径中包含版本号
- **一致性**：保持请求和响应格式一致
- **安全性**：实现多重认证和授权机制
- **可扩展性**：支持未来功能扩展
- **文档完整**：全面详细的API文档

### 1.2 基础URL

- **API基础路径**：`https://api.gridtrader.com/api/v1/`
- **WebSocket基础路径**：`wss://api.gridtrader.com/ws/v1/`

### 1.3 API版本控制

- 使用URL路径版本控制
- 当前版本：v1
- 版本变更规则：
  - 主版本变更（v1 -> v2）：不兼容的API变更
  - 次版本变更：向后兼容的功能新增（不反映在URL中）
  - 补丁版本：bug修复和功能改进（不反映在URL中）

## 2. 认证与安全

### 2.1 认证方式

系统支持两种认证方式：

#### 2.1.1 JWT令牌认证

- 主要用于前端Web应用和移动应用
- 使用`Authorization`请求头传递令牌
- 格式：`Authorization: Bearer {token}`
- 令牌有效期：访问令牌15分钟，刷新令牌7天

#### 2.1.2 API密钥认证

- 主要用于第三方系统和自动化工具
- 使用请求头传递API密钥和签名
- 请求头格式：
  ```
  X-API-KEY: {api_key}
  X-API-TIMESTAMP: {timestamp}
  X-API-SIGNATURE: {signature}
  ```
- 签名算法：HMAC-SHA256
- 签名内容：`{api_key}{timestamp}{request_method}{request_path}{request_body}`

### 2.2 授权机制

- 基于角色的访问控制（RBAC）
- 资源所有者检查
- 操作权限控制
- 多租户隔离

### 2.3 安全措施

- 强制HTTPS传输
- 请求频率限制
- JWT令牌轮换
- CSRF保护
- 访问日志审计

## 3. RESTful API端点

### 3.1 认证API

#### 3.1.1 用户登录

- **请求**：`POST /auth/login/`
- **描述**：用户登录并获取JWT令牌
- **权限**：无需认证
- **请求体**：
  ```json
  {
    "username": "user@example.com",
    "password": "secure_password"
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "username": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "created_at": "2023-01-15T12:00:00Z"
    }
  }
  ```
- **错误响应** (401 Unauthorized)：
  ```json
  {
    "error": {
      "code": "INVALID_CREDENTIALS",
      "message": "Invalid username or password"
    }
  }
  ```

#### 3.1.2 令牌刷新

- **请求**：`POST /auth/refresh/`
- **描述**：使用刷新令牌获取新的访问令牌
- **权限**：无需认证
- **请求体**：
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

#### 3.1.3 用户注册

- **请求**：`POST /auth/register/`
- **描述**：注册新用户
- **权限**：无需认证
- **请求体**：
  ```json
  {
    "username": "user@example.com",
    "password": "secure_password",
    "name": "John Doe",
    "referral_code": "ABC123"
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "user": {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "username": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "created_at": "2023-01-15T12:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

#### 3.1.4 获取当前用户信息

- **请求**：`GET /auth/user/`
- **描述**：获取当前认证用户信息
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "user": {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "username": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "created_at": "2023-01-15T12:00:00Z",
      "is_agent": false,
      "agent_level": 0,
      "balance": 1000.50,
      "active_strategies_count": 3
    }
  }
  ```

#### 3.1.5 创建API密钥

- **请求**：`POST /auth/api-keys/`
- **描述**：创建新的API密钥
- **权限**：认证用户
- **请求体**：
  ```json
  {
    "name": "Trading Bot",
    "permissions": ["read", "trade"]
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "api_key": "GHT567JHGFT56JHGFR567JHG",
    "api_secret": "JHG56JHGFT567JHGFT56JHG",
    "name": "Trading Bot",
    "permissions": ["read", "trade"],
    "created_at": "2023-01-15T12:00:00Z"
  }
  ```

### 3.2 策略管理API

#### 3.2.1 获取策略列表

- **请求**：`GET /strategies/`
- **描述**：获取用户的策略列表
- **权限**：认证用户
- **查询参数**：
  - `status`: 策略状态过滤 (running, stopped, pending, error)
  - `trading_pair`: 交易对过滤
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 10,
    "next": "https://api.gridtrader.com/api/v1/strategies/?page=2",
    "previous": null,
    "results": [
      {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "name": "BTC Grid Strategy",
        "exchange": "binance",
        "trading_pair": "BTC/USDT",
        "grid_type": "arithmetic",
        "status": "running",
        "created_at": "2023-01-15T12:00:00Z",
        "upper_price": 50000.00,
        "lower_price": 40000.00,
        "grid_levels": 10,
        "total_investment": 1000.00,
        "realized_profit": 25.50,
        "metrics": {
          "roi": 2.55,
          "annualized_roi": 21.38,
          "total_trades": 45
        }
      },
      {
        "id": "c47ac10b-58cc-4372-a567-0e02b2c3d480",
        "name": "ETH Grid Strategy",
        "exchange": "okx",
        "trading_pair": "ETH/USDT",
        "grid_type": "geometric",
        "status": "stopped",
        "created_at": "2023-01-10T10:30:00Z",
        "upper_price": 3000.00,
        "lower_price": 2000.00,
        "grid_levels": 8,
        "total_investment": 800.00,
        "realized_profit": 12.30,
        "metrics": {
          "roi": 1.54,
          "annualized_roi": 15.22,
          "total_trades": 28
        }
      }
    ]
  }
  ```

#### 3.2.2 创建策略

- **请求**：`POST /strategies/`
- **描述**：创建新的网格交易策略
- **权限**：认证用户
- **请求体**：
  ```json
  {
    "name": "BTC Grid Strategy",
    "exchange": "binance",
    "trading_pair": "BTC/USDT",
    "inst_type": "SPOT",
    "direction": "LONG",
    "grid_type": "arithmetic",
    "investment_amount": 1000.00,
    "grid_levels": 10,
    "upper_price": 50000.00,
    "lower_price": 40000.00,
    "default_grid_spread": 1.0,
    "default_take_profit": 1.0,
    "default_open_rebound": 0.5,
    "default_close_rebound": 0.3,
    "risk_controls": {
      "avg_price_tp_enabled": true,
      "avg_price_tp_percent": 5.0,
      "avg_price_sl_enabled": true,
      "avg_price_sl_percent": 3.0,
      "total_tp_enabled": false,
      "total_tp_amount": null,
      "total_sl_enabled": false,
      "total_sl_amount": null
    },
    "operations": {
      "open_enabled": true,
      "close_enabled": true
    }
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "BTC Grid Strategy",
    "exchange": "binance",
    "trading_pair": "BTC/USDT",
    "inst_type": "SPOT",
    "direction": "LONG",
    "grid_type": "arithmetic",
    "investment_amount": 1000.00,
    "grid_levels": 10,
    "upper_price": 50000.00,
    "lower_price": 40000.00,
    "default_grid_spread": 1.0,
    "default_take_profit": 1.0,
    "default_open_rebound": 0.5,
    "default_close_rebound": 0.3,
    "risk_controls": {
      "avg_price_tp_enabled": true,
      "avg_price_tp_percent": 5.0,
      "avg_price_sl_enabled": true,
      "avg_price_sl_percent": 3.0,
      "total_tp_enabled": false,
      "total_tp_amount": null,
      "total_sl_enabled": false,
      "total_sl_amount": null
    },
    "operations": {
      "open_enabled": true,
      "close_enabled": true
    },
    "status": "pending",
    "created_at": "2023-01-15T12:00:00Z",
    "updated_at": "2023-01-15T12:00:00Z"
  }
  ```

### 3.2.3 获取策略详情

- **请求**：`GET /strategies/{id}/`
- **描述**：获取特定策略的详细信息
- **权限**：策略所有者
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "BTC Grid Strategy",
    "exchange": "binance",
    "trading_pair": "BTC/USDT",
    "inst_type": "SPOT",
    "direction": "LONG",
    "grid_type": "arithmetic",
    "investment_amount": 1000.00,
    "grid_levels": 10,
    "upper_price": 50000.00,
    "lower_price": 40000.00,
    "default_grid_spread": 1.0,
    "default_take_profit": 1.0,
    "default_open_rebound": 0.5,
    "default_close_rebound": 0.3,
    "risk_controls": {
      "avg_price_tp_enabled": true,
      "avg_price_tp_percent": 5.0,
      "avg_price_sl_enabled": true,
      "avg_price_sl_percent": 3.0,
      "total_tp_enabled": false,
      "total_tp_amount": null,
      "total_sl_enabled": false,
      "total_sl_amount": null
    },
    "operations": {
      "open_enabled": true,
      "close_enabled": true
    },
    "status": "running",
    "created_at": "2023-01-15T12:00:00Z",
    "updated_at": "2023-01-15T14:30:00Z",
    "last_run_at": "2023-01-15T14:30:00Z",
    "current_price": 45250.75,
    "open_trigger_price": 44500.00,
    "tp_trigger_price": 46000.00,
    "stats": {
      "total_realized_profit": 25.50,
      "total_trades": 45,
      "profitable_trades": 30,
      "roi": 2.55,
      "annualized_roi": 21.38
    },
    "position_metrics": {
      "total_amount": 0.0225,
      "total_value": 1018.75,
      "avg_price": 45278.00,
      "current_value": 1018.14,
      "unrealized_pnl": -0.61
    }
  }
  ```

#### 3.2.4 更新策略

- **请求**：`PUT /strategies/{id}/`
- **描述**：更新策略配置
- **权限**：策略所有者
- **请求体**：
  ```json
  {
    "name": "BTC Grid Strategy Updated",
    "upper_price": 52000.00,
    "lower_price": 42000.00,
    "default_grid_spread": 1.2,
    "default_take_profit": 1.3,
    "default_open_rebound": 0.6,
    "default_close_rebound": 0.4,
    "risk_controls": {
      "avg_price_tp_enabled": true,
      "avg_price_tp_percent": 6.0,
      "avg_price_sl_enabled": true,
      "avg_price_sl_percent": 4.0,
      "total_tp_enabled": true,
      "total_tp_amount": 50.00,
      "total_sl_enabled": false,
      "total_sl_amount": null
    },
    "operations": {
      "open_enabled": true,
      "close_enabled": true
    }
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "BTC Grid Strategy Updated",
    "exchange": "binance",
    "trading_pair": "BTC/USDT",
    "inst_type": "SPOT",
    "direction": "LONG",
    "grid_type": "arithmetic",
    "investment_amount": 1000.00,
    "grid_levels": 10,
    "upper_price": 52000.00,
    "lower_price": 42000.00,
    "default_grid_spread": 1.2,
    "default_take_profit": 1.3,
    "default_open_rebound": 0.6,
    "default_close_rebound": 0.4,
    "risk_controls": {
      "avg_price_tp_enabled": true,
      "avg_price_tp_percent": 6.0,
      "avg_price_sl_enabled": true,
      "avg_price_sl_percent": 4.0,
      "total_tp_enabled": true,
      "total_tp_amount": 50.00,
      "total_sl_enabled": false,
      "total_sl_amount": null
    },
    "operations": {
      "open_enabled": true,
      "close_enabled": true
    },
    "status": "running",
    "created_at": "2023-01-15T12:00:00Z",
    "updated_at": "2023-01-15T16:45:00Z"
  }
  ```

#### 3.2.5 删除策略

- **请求**：`DELETE /strategies/{id}/`
- **描述**：删除策略
- **权限**：策略所有者
- **成功响应** (204 No Content)

#### 3.2.6 启动策略

- **请求**：`POST /strategies/{id}/start/`
- **描述**：启动策略
- **权限**：策略所有者
- **请求体**：空
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "running",
    "message": "Strategy started successfully",
    "started_at": "2023-01-15T17:00:00Z"
  }
  ```

#### 3.2.7 停止策略

- **请求**：`POST /strategies/{id}/stop/`
- **描述**：停止策略
- **权限**：策略所有者
- **请求体**：空
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "stopped",
    "message": "Strategy stopped successfully",
    "stopped_at": "2023-01-15T18:30:00Z"
  }
  ```

#### 3.2.8 重置策略

- **请求**：`POST /strategies/{id}/reset/`
- **描述**：重置策略状态
- **权限**：策略所有者
- **请求体**：
  ```json
  {
    "clear_trades_history": false
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "pending",
    "message": "Strategy reset successfully",
    "reset_at": "2023-01-15T19:15:00Z"
  }
  ```

#### 3.2.9 获取策略性能指标

- **请求**：`GET /strategies/{id}/performance/`
- **描述**：获取策略性能指标
- **权限**：策略所有者
- **查询参数**：
  - `period`: 时间段 (daily, weekly, monthly, all)
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "BTC Grid Strategy",
    "period": "monthly",
    "metrics": {
      "total_realized_profit": 25.50,
      "total_trades": 45,
      "profitable_trades": 30,
      "roi": 2.55,
      "annualized_roi": 21.38,
      "avg_trade_profit": 0.57,
      "profit_factor": 1.8,
      "max_drawdown": 1.2
    },
    "time_series": [
      {
        "timestamp": "2023-01-01T00:00:00Z",
        "realized_profit": 0.00,
        "current_price": 42000.00,
        "current_value": 1000.00,
        "roi": 0.00
      },
      {
        "timestamp": "2023-01-15T00:00:00Z",
        "realized_profit": 25.50,
        "current_price": 45250.75,
        "current_value": 1018.14,
        "roi": 2.55
      }
    ]
  }
  ```

### 3.3 网格层级API

#### 3.3.1 获取网格层级列表

- **请求**：`GET /strategies/{id}/grid-levels/`
- **描述**：获取策略的网格层级列表
- **权限**：策略所有者
- **成功响应** (200 OK)：
  ```json
  {
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "grid_levels": [
      {
        "id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
        "sequence_number": 0,
        "interval_percent": 1.0,
        "take_profit_percent": 1.0,
        "open_rebound_percent": 0.5,
        "close_rebound_percent": 0.3,
        "invest_amount": 100.00,
        "upper_price": 50000.00,
        "lower_price": 49500.00,
        "is_filled": true,
        "filled_price": 49800.00,
        "filled_amount": 0.0020,
        "filled_value": 99.60,
        "filled_at": "2023-01-15T14:35:00Z"
      },
      {
        "id": "b47ac10b-58cc-4372-a567-0e02b2c3d491",
        "sequence_number": 1,
        "interval_percent": 1.0,
        "take_profit_percent": 1.0,
        "open_rebound_percent": 0.5,
        "close_rebound_percent": 0.3,
        "invest_amount": 100.00,
        "upper_price": 49500.00,
        "lower_price": 49000.00,
        "is_filled": false,
        "filled_price": null,
        "filled_amount": null,
        "filled_value": null,
        "filled_at": null
      }
    ]
  }
  ```

#### 3.3.2 更新网格层级

- **请求**：`PUT /strategies/{id}/grid-levels/{level_id}/`
- **描述**：更新特定网格层级
- **权限**：策略所有者
- **请求体**：
  ```json
  {
    "interval_percent": 1.2,
    "take_profit_percent": 1.3,
    "open_rebound_percent": 0.6,
    "close_rebound_percent": 0.4,
    "invest_amount": 120.00
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
    "sequence_number": 0,
    "interval_percent": 1.2,
    "take_profit_percent": 1.3,
    "open_rebound_percent": 0.6,
    "close_rebound_percent": 0.4,
    "invest_amount": 120.00,
    "upper_price": 50000.00,
    "lower_price": 49400.00,
    "is_filled": true,
    "filled_price": 49800.00,
    "filled_amount": 0.0020,
    "filled_value": 99.60,
    "filled_at": "2023-01-15T14:35:00Z"
  }
  ```

#### 3.3.3 重置网格层级

- **请求**：`POST /strategies/{id}/grid-levels/{level_id}/reset/`
- **描述**：重置特定网格层级状态
- **权限**：策略所有者
- **请求体**：空
- **成功响应** (200 OK)：
  ```json
  {
    "id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
    "sequence_number": 0,
    "message": "Grid level reset successfully",
    "reset_at": "2023-01-15T20:10:00Z"
  }
  ```

### 3.3.4 删除网格层级

- **请求**：`DELETE /strategies/{id}/grid-levels/{level_id}/`
- **描述**：删除特定网格层级
- **权限**：策略所有者
- **成功响应** (204 No Content)

### 3.2.11 获取策略统计概览

- **请求**：`GET /strategies/statistics/`
- **描述**：获取用户所有策略的统计概览
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "total_investment": 3000.00,
    "active_strategies_count": 2,
    "paused_strategies_count": 3,
    "today_profit": 23.80,
    "yesterday_profit": 18.50,
    "thirty_days_profit": 219.85,
    "total_return_rate": 7.33,
    "profit_trends": [
      {
        "date": "2023-01-15",
        "profit": 8.50
      },
      // ...更多日期数据
    ]
  }

### 3.4 交易记录API

#### 3.4.1 获取交易记录列表

- **请求**：`GET /trades/`
- **描述**：获取用户的所有交易记录
- **权限**：认证用户
- **查询参数**：
  - `strategy_id`: 策略ID过滤
  - `trade_type`: 交易类型过滤 (buy, sell)
  - `start_date`: 开始日期
  - `end_date`: 结束日期
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 45,
    "next": "https://api.gridtrader.com/api/v1/trades/?page=2",
    "previous": null,
    "results": [
      {
        "id": "e47ac10b-58cc-4372-a567-0e02b2c3d495",
        "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "strategy_name": "BTC Grid Strategy",
        "level_id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
        "order_id": "binance_123456789",
        "trade_type": "buy",
        "price": 49800.00,
        "amount": 0.0020,
        "value": 99.60,
        "fee": 0.0996,
        "fee_currency": "USDT",
        "profit": 0.00,
        "executed_at": "2023-01-15T14:35:00Z"
      },
      {
        "id": "d47ac10b-58cc-4372-a567-0e02b2c3d496",
        "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "strategy_name": "BTC Grid Strategy",
        "level_id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
        "order_id": "binance_123456790",
        "trade_type": "sell",
        "price": 50300.00,
        "amount": 0.0020,
        "value": 100.60,
        "fee": 0.1006,
        "fee_currency": "USDT",
        "profit": 1.00,
        "executed_at": "2023-01-15T16:20:00Z"
      }
    ]
  }
  ```

#### 3.4.2 获取策略交易记录

- **请求**：`GET /strategies/{id}/trades/`
- **描述**：获取特定策略的交易记录
- **权限**：策略所有者
- **查询参数**：
  - `trade_type`: 交易类型过滤 (buy, sell)
  - `start_date`: 开始日期
  - `end_date`: 结束日期
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应**：与获取交易记录列表相同

#### 3.4.3 获取交易统计

- **请求**：`GET /strategies/{id}/trades/stats/`
- **描述**：获取策略交易统计数据
- **权限**：策略所有者
- **查询参数**：
  - `period`: 时间段 (daily, weekly, monthly, all)
- **成功响应** (200 OK)：
  ```json
  {
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "period": "monthly",
    "total_trades": 45,
    "buy_trades": 23,
    "sell_trades": 22,
    "profitable_trades": 30,
    "loss_trades": 15,
    "total_volume": 4500.00,
    "total_profit": 25.50,
    "total_loss": 5.20,
    "net_profit": 20.30,
    "profit_factor": 4.90,
    "win_rate": 66.67,
    "avg_profit_per_trade": 0.85,
    "avg_loss_per_trade": -0.35,
    "largest_profit": 2.30,
    "largest_loss": -0.80,
    "daily_breakdown": [
      {
        "date": "2023-01-15",
        "trades": 15,
        "profit": 8.50,
        "volume": 1500.00
      },
      {
        "date": "2023-01-16",
        "trades": 12,
        "profit": 6.20,
        "volume": 1200.00
      }
    ]
  }
  ```

#### 3.4.4 记录交易（用户端同步）

- **请求**：`POST /strategies/{id}/trades/`
- **描述**：从用户端同步交易记录到中央系统
- **权限**：策略所有者
- **请求体**：
  ```json
  {
    "trades": [
      {
        "level_id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
        "order_id": "binance_123456789",
        "trade_type": "buy",
        "price": 49800.00,
        "amount": 0.0020,
        "value": 99.60,
        "fee": 0.0996,
        "fee_currency": "USDT",
        "profit": 0.00,
        "executed_at": "2023-01-15T14:35:00Z"
      }
    ]
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "success": true,
    "message": "1 trades recorded successfully",
    "trade_ids": ["e47ac10b-58cc-4372-a567-0e02b2c3d495"]
  }
  ```

### 3.5 用户与账户API

#### 3.5.1 获取用户资料

- **请求**：`GET /users/profile/`
- **描述**：获取当前用户的资料
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "username": "user@example.com",
    "name": "John Doe",
    "email": "user@example.com",
    "phone": "+1234567890",
    "role": "user",
    "is_agent": false,
    "agent_level": 0,
    "balance": 1000.50,
    "active_strategies_count": 3,
    "created_at": "2023-01-01T12:00:00Z",
    "last_login": "2023-01-15T10:30:00Z"
  }
  ```

#### 3.5.2 更新用户资料

- **请求**：`PUT /users/profile/`
- **描述**：更新当前用户的资料
- **权限**：认证用户
- **请求体**：
  ```json
  {
    "name": "John Doe Updated",
    "email": "user.updated@example.com",
    "phone": "+0987654321"
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "username": "user@example.com",
    "name": "John Doe Updated",
    "email": "user.updated@example.com",
    "phone": "+0987654321",
    "role": "user",
    "is_agent": false,
    "agent_level": 0,
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-15T22:45:00Z"
  }
  ```

#### 3.5.3 获取API密钥列表

- **请求**：`GET /users/api-keys/`
- **描述**：获取用户的API密钥列表
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "api_keys": [
      {
        "id": "g47ac10b-58cc-4372-a567-0e02b2c3d499",
        "name": "Trading Bot",
        "prefix": "GHT567",
        "permissions": ["read", "trade"],
        "last_used": "2023-01-15T20:30:00Z",
        "created_at": "2023-01-10T12:00:00Z"
      }
    ]
  }
  ```

#### 3.5.4 创建API密钥

- **请求**：`POST /users/api-keys/`
- **描述**：创建新的API密钥
- **权限**：认证用户
- **请求体**：
  ```json
  {
    "name": "Trading Bot 2",
    "permissions": ["read", "trade"]
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "id": "h47ac10b-58cc-4372-a567-0e02b2c3d500",
    "name": "Trading Bot 2",
    "api_key": "JKL890ABCDEF",
    "api_secret": "ABCDEF1234567890",
    "permissions": ["read", "trade"],
    "created_at": "2023-01-15T23:00:00Z"
  }
  ```

#### 3.5.5 删除API密钥

- **请求**：`DELETE /users/api-keys/{id}/`
- **描述**：删除API密钥
- **权限**：认证用户
- **成功响应** (204 No Content)

#### 3.5.6 获取用户偏好设置

- **请求**：`GET /users/preferences/`
- **描述**：获取用户的偏好设置
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "theme": "dark",
    "language": "en",
    "timezone": "UTC",
    "notification_settings": {
      "email_notifications": true,
      "trade_notifications": true,
      "strategy_alerts": true,
      "system_alerts": true
    },
    "dashboard_layout": {
      "widgets": ["performance", "strategies", "trades"]
    }
  }
  ```

#### 3.5.7 更新用户偏好设置

- **请求**：`PUT /users/preferences/`
- **描述**：更新用户的偏好设置
- **权限**：认证用户
- **请求体**：
  ```json
  {
    "theme": "light",
    "language": "zh",
    "timezone": "Asia/Shanghai",
    "notification_settings": {
      "email_notifications": false,
      "trade_notifications": true,
      "strategy_alerts": true,
      "system_alerts": false
    }
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "theme": "light",
    "language": "zh",
    "timezone": "Asia/Shanghai",
    "notification_settings": {
      "email_notifications": false,
      "trade_notifications": true,
      "strategy_alerts": true,
      "system_alerts": false
    },
    "dashboard_layout": {
      "widgets": ["performance", "strategies", "trades"]
    }
  }
  ```

### 3.6 计费与结算API

#### 3.6.1 获取账户余额

- **请求**：`GET /billing/balance/`
- **描述**：获取用户账户余额
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "balance": 1000.50,
    "currency": "USDT",
    "last_updated": "2023-01-15T23:30:00Z",
    "next_billing_date": "2023-02-01T00:00:00Z",
    "estimated_fees": 10.25
  }
  ```

#### 3.6.2 获取账单列表

- **请求**：`GET /billing/invoices/`
- **描述**：获取用户的账单列表
- **权限**：认证用户
- **查询参数**：
  - `status`: 账单状态过滤 (pending, paid, overdue)
  - `start_date`: 开始日期
  - `end_date`: 结束日期
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "i47ac10b-58cc-4372-a567-0e02b2c3d510",
        "invoice_number": "INV-2023-001",
        "billing_period_start": "2023-01-01T00:00:00Z",
        "billing_period_end": "2023-01-15T00:00:00Z",
        "total_trading_volume": 5000.00,
        "fee_rate": 5.0,
        "fee_amount": 12.50,
        "discount_amount": 0.00,
        "payable_amount": 12.50,
        "status": "paid",
        "payment_date": "2023-01-15T00:00:00Z",
        "created_at": "2023-01-15T00:00:00Z"
      },
      {
        "id": "j47ac10b-58cc-4372-a567-0e02b2c3d511",
        "invoice_number": "INV-2023-002",
        "billing_period_start": "2023-01-16T00:00:00Z",
        "billing_period_end": "2023-01-31T00:00:00Z",
        "total_trading_volume": 0.00,
        "fee_rate": 5.0,
        "fee_amount": 0.00,
        "discount_amount": 0.00,
        "payable_amount": 0.00,
        "status": "pending",
        "payment_date": null,
        "created_at": "2023-01-16T00:00:00Z"
      }
    ]
  }
  ```

#### 3.6.3 获取账单详情

- **请求**：`GET /billing/invoices/{id}/`
- **描述**：获取账单详情
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "id": "i47ac10b-58cc-4372-a567-0e02b2c3d510",
    "invoice_number": "INV-2023-001",
    "billing_period_start": "2023-01-01T00:00:00Z",
    "billing_period_end": "2023-01-15T00:00:00Z",
    "total_trading_volume": 5000.00,
    "total_trades_count": 120,
    "total_strategies_count": 3,
    "fee_rate": 5.0,
    "fee_amount": 12.50,
    "discount_percentage": 0.0,
    "discount_amount": 0.00,
    "payable_amount": 12.50,
    "status": "paid",
    "payment_method": "auto-deduction",
    "payment_date": "2023-01-15T00:00:00Z",
    "created_at": "2023-01-15T00:00:00Z",
    "strategy_breakdown": [
      {
        "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "strategy_name": "BTC Grid Strategy",
        "trading_volume": 3000.00,
        "trades_count": 75,
        "profit": 25.50,
        "fee_amount": 7.50
      },
      {
        "strategy_id": "c47ac10b-58cc-4372-a567-0e02b2c3d480",
        "strategy_name": "ETH Grid Strategy",
        "trading_volume": 2000.00,
        "trades_count": 45,
        "profit": 15.30,
        "fee_amount": 5.00
      }
    ]
  }
  ```

  #### 3.6.4 账户充值

- **请求**：`POST /billing/topup/`
- **描述**：为账户充值
- **权限**：认证用户
- **请求体**：
  ```json
  {
    "amount": 100.00,
    "payment_method": "crypto_transfer",
    "currency": "USDT"
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "transaction_id": "k47ac10b-58cc-4372-a567-0e02b2c3d520",
    "amount": 100.00,
    "currency": "USDT",
    "payment_method": "crypto_transfer",
    "status": "pending",
    "payment_instructions": {
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "network": "Ethereum",
      "memo": "USER123456"
    },
    "created_at": "2023-01-16T10:00:00Z"
  }
  ```

#### 3.6.5 获取交易流水

- **请求**：`GET /billing/transactions/`
- **描述**：获取账户交易流水记录
- **权限**：认证用户
- **查询参数**：
  - `type`: 交易类型过滤 (deposit, fee, withdrawal)
  - `start_date`: 开始日期
  - `end_date`: 结束日期
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "k47ac10b-58cc-4372-a567-0e02b2c3d520",
        "transaction_type": "deposit",
        "amount": 100.00,
        "currency": "USDT",
        "status": "completed",
        "reference": "Deposit via crypto transfer",
        "balance_after": 1100.50,
        "created_at": "2023-01-16T10:00:00Z",
        "completed_at": "2023-01-16T10:15:00Z"
      },
      {
        "id": "l47ac10b-58cc-4372-a567-0e02b2c3d521",
        "transaction_type": "fee",
        "amount": -12.50,
        "currency": "USDT",
        "status": "completed",
        "reference": "Invoice INV-2023-001",
        "balance_after": 1000.50,
        "created_at": "2023-01-15T00:00:00Z",
        "completed_at": "2023-01-15T00:00:00Z"
      }
    ]
  }
  ```

### 3.7 代理分润API

#### 3.7.1 获取代理信息

- **请求**：`GET /agents/info/`
- **描述**：获取代理信息
- **权限**：代理用户
- **成功响应** (200 OK)：
  ```json
  {
    "agent_id": "m47ac10b-58cc-4372-a567-0e02b2c3d530",
    "agent_level": 1,
    "agent_status": "active",
    "total_referrals": 25,
    "active_referrals": 18,
    "total_commission": 350.75,
    "current_period_commission": 45.30,
    "commission_rate": 30.0,
    "invitation_code": "AGENT123",
    "invitation_link": "https://gridtrader.com/ref/AGENT123",
    "created_at": "2022-12-01T00:00:00Z"
  }
  ```

#### 3.7.2 获取下线用户列表

- **请求**：`GET /agents/referrals/`
- **描述**：获取代理的下线用户列表
- **权限**：代理用户
- **查询参数**：
  - `status`: 状态过滤 (active, inactive)
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 25,
    "next": "https://api.gridtrader.com/api/v1/agents/referrals/?page=2",
    "previous": null,
    "results": [
      {
        "user_id": "n47ac10b-58cc-4372-a567-0e02b2c3d540",
        "username": "user1@example.com",
        "registration_date": "2023-01-05T00:00:00Z",
        "status": "active",
        "strategies_count": 3,
        "total_trading_volume": 5000.00,
        "total_commission_generated": 25.00,
        "custom_commission_rate": null
      },
      {
        "user_id": "o47ac10b-58cc-4372-a567-0e02b2c3d541",
        "username": "user2@example.com",
        "registration_date": "2023-01-10T00:00:00Z",
        "status": "active",
        "strategies_count": 2,
        "total_trading_volume": 3000.00,
        "total_commission_generated": 15.00,
        "custom_commission_rate": 35.0
      }
    ]
  }
  ```

#### 3.7.3 获取佣金记录

- **请求**：`GET /agents/commissions/`
- **描述**：获取代理的佣金记录
- **权限**：代理用户
- **查询参数**：
  - `status`: 状态过滤 (pending, paid)
  - `start_date`: 开始日期
  - `end_date`: 结束日期
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "p47ac10b-58cc-4372-a567-0e02b2c3d550",
        "source_user_id": "n47ac10b-58cc-4372-a567-0e02b2c3d540",
        "source_username": "user1@example.com",
        "source_billing_id": "i47ac10b-58cc-4372-a567-0e02b2c3d510",
        "commission_level": 1,
        "commission_rate": 30.0,
        "base_amount": 12.50,
        "commission_amount": 3.75,
        "status": "paid",
        "created_at": "2023-01-15T00:00:00Z",
        "paid_at": "2023-01-15T00:00:00Z"
      },
      {
        "id": "q47ac10b-58cc-4372-a567-0e02b2c3d551",
        "source_user_id": "o47ac10b-58cc-4372-a567-0e02b2c3d541",
        "source_username": "user2@example.com",
        "source_billing_id": "j47ac10b-58cc-4372-a567-0e02b2c3d511",
        "commission_level": 1,
        "commission_rate": 35.0,
        "base_amount": 10.00,
        "commission_amount": 3.50,
        "status": "pending",
        "created_at": "2023-01-16T00:00:00Z",
        "paid_at": null
      }
    ]
  }
  ```

#### 3.7.4 获取代理设置

- **请求**：`GET /agents/settings/`
- **描述**：获取代理设置
- **权限**：代理用户
- **成功响应** (200 OK)：
  ```json
  {
    "commission_rates": {
      "default": 30.0,
      "custom_rates": [
        {
          "user_id": "o47ac10b-58cc-4372-a567-0e02b2c3d541",
          "username": "user2@example.com",
          "rate": 35.0
        }
      ]
    },
    "payout_settings": {
      "payout_method": "balance_credit",
      "auto_payout": true,
      "min_payout_amount": 10.00
    },
    "invitation_settings": {
      "invitation_code": "AGENT123",
      "custom_landing_message": "Join the best grid trading platform with my invitation code!"
    }
  }
  ```

#### 3.7.5 更新代理设置

- **请求**：`PUT /agents/settings/`
- **描述**：更新代理设置
- **权限**：代理用户
- **请求体**：
  ```json
  {
    "payout_settings": {
      "payout_method": "crypto_withdrawal",
      "auto_payout": false,
      "min_payout_amount": 50.00
    },
    "invitation_settings": {
      "custom_landing_message": "Join now and get special benefits with my invitation code!"
    }
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "commission_rates": {
      "default": 30.0,
      "custom_rates": [
        {
          "user_id": "o47ac10b-58cc-4372-a567-0e02b2c3d541",
          "username": "user2@example.com",
          "rate": 35.0
        }
      ]
    },
    "payout_settings": {
      "payout_method": "crypto_withdrawal",
      "auto_payout": false,
      "min_payout_amount": 50.00
    },
    "invitation_settings": {
      "invitation_code": "AGENT123",
      "custom_landing_message": "Join now and get special benefits with my invitation code!"
    }
  }
  ```

#### 3.7.6 设置用户自定义佣金率

- **请求**：`POST /agents/custom-rates/`
- **描述**：为特定下线用户设置自定义佣金率
- **权限**：代理用户
- **请求体**：
  ```json
  {
    "user_id": "n47ac10b-58cc-4372-a567-0e02b2c3d540",
    "commission_rate": 40.0
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "user_id": "n47ac10b-58cc-4372-a567-0e02b2c3d540",
    "username": "user1@example.com",
    "commission_rate": 40.0,
    "previous_rate": 30.0,
    "updated_at": "2023-01-16T14:30:00Z"
  }
  ```

### 3.8 系统管理API

#### 3.8.1 获取系统状态

- **请求**：`GET /system/status/`
- **描述**：获取系统状态信息
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "status": "operational",
    "api_version": "1.0.0",
    "server_time": "2023-01-16T15:00:00Z",
    "components": [
      {
        "name": "API Service",
        "status": "operational"
      },
      {
        "name": "Trading Engine",
        "status": "operational"
      },
      {
        "name": "Database",
        "status": "operational"
      }
    ],
    "metrics": {
      "total_users": 1500,
      "active_strategies": 850,
      "trades_today": 12000
    }
  }
  ```

#### 3.8.2 获取支持的交易所

- **请求**：`GET /system/exchanges/`
- **描述**：获取系统支持的交易所列表
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "exchanges": [
      {
        "id": "binance",
        "name": "Binance",
        "logo_url": "https://api.gridtrader.com/static/exchanges/binance.png",
        "website": "https://www.binance.com",
        "status": "operational",
        "supported_features": ["spot", "futures", "margin"],
        "api_docs_url": "https://binance-docs.github.io/apidocs/"
      },
      {
        "id": "okx",
        "name": "OKX",
        "logo_url": "https://api.gridtrader.com/static/exchanges/okx.png",
        "website": "https://www.okx.com",
        "status": "operational",
        "supported_features": ["spot", "futures", "margin"],
        "api_docs_url": "https://www.okx.com/docs-v5/"
      }
    ]
  }
  ```

#### 3.8.3 获取支持的交易对

- **请求**：`GET /system/exchanges/{exchange_id}/trading-pairs/`
- **描述**：获取特定交易所支持的交易对列表
- **权限**：认证用户
- **查询参数**：
  - `market_type`: 市场类型过滤 (spot, futures, margin)
  - `quote_currency`: 计价货币过滤
- **成功响应** (200 OK)：
  ```json
  {
    "exchange": "binance",
    "market_type": "spot",
    "trading_pairs": [
      {
        "symbol": "BTC/USDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "price_precision": 2,
        "amount_precision": 6,
        "min_order_size": 0.00001,
        "min_order_value": 10.00,
        "current_price": 45250.75,
        "24h_volume": 1250000000.00,
        "24h_change": 2.5
      },
      {
        "symbol": "ETH/USDT",
        "base_asset": "ETH",
        "quote_asset": "USDT",
        "price_precision": 2,
        "amount_precision": 5,
        "min_order_size": 0.0001,
        "min_order_value": 10.00,
        "current_price": 3450.25,
        "24h_volume": 750000000.00,
        "24h_change": 1.8
      }
    ]
  }
  ```

#### 3.8.4 获取系统通知

- **请求**：`GET /system/notifications/`
- **描述**：获取系统通知
- **权限**：认证用户
- **查询参数**：
  - `is_read`: 已读状态过滤
  - `type`: 通知类型过滤 (info, success, warning, error)
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "r47ac10b-58cc-4372-a567-0e02b2c3d560",
        "type": "info",
        "title": "System Maintenance",
        "message": "Scheduled maintenance on January 20, 2023, from 02:00 UTC to 04:00 UTC.",
        "is_read": false,
        "created_at": "2023-01-16T12:00:00Z"
      },
      {
        "id": "s47ac10b-58cc-4372-a567-0e02b2c3d561",
        "type": "success",
        "title": "Strategy Started",
        "message": "Your strategy 'BTC Grid Strategy' has been started successfully.",
        "is_read": true,
        "created_at": "2023-01-15T14:30:00Z"
      }
    ]
  }
  ```

#### 3.8.5 标记通知为已读

- **请求**：`POST /system/notifications/{id}/read/`
- **描述**：标记通知为已读
- **权限**：认证用户
- **请求体**：空
- **成功响应** (200 OK)：
  ```json
  {
    "id": "r47ac10b-58cc-4372-a567-0e02b2c3d560",
    "is_read": true,
    "read_at": "2023-01-16T16:30:00Z"
  }
  ```

## 4. WebSocket API

WebSocket API提供实时数据更新，减少轮询请求的需要，适用于价格更新、交易通知等场景。

### 4.1 连接和认证

- **WebSocket URL**：`wss://api.gridtrader.com/ws/v1/`
- **认证方式**：通过发送认证消息
  ```json
  {
    "action": "authenticate",
    "payload": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
  ```
- **认证响应**：
  ```json
  {
    "event": "authenticated",
    "status": "success",
    "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
  ```

### 4.2 频道订阅

#### 4.2.1 订阅策略更新

- **订阅请求**：
  ```json
  {
    "action": "subscribe",
    "channel": "strategy",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```
- **订阅响应**：
  ```json
  {
    "event": "subscribed",
    "channel": "strategy",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```
- **数据消息**：
  ```json
  {
    "event": "strategy_update",
    "channel": "strategy",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "data": {
      "current_price": 45300.50,
      "status": "running",
      "total_realized_profit": 26.50,
      "position_metrics": {
        "total_amount": 0.0225,
        "total_value": 1019.26,
        "avg_price": 45278.00,
        "unrealized_pnl": 0.51
      }
    },
    "timestamp": "2023-01-16T16:45:00Z"
  }
  ```

#### 4.2.2 订阅交易更新

- **订阅请求**：
  ```json
  {
    "action": "subscribe",
    "channel": "trades",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```
- **数据消息**：
  ```json
  {
    "event": "trade_executed",
    "channel": "trades",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "data": {
      "trade_id": "t47ac10b-58cc-4372-a567-0e02b2c3d570",
      "level_id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
      "order_id": "binance_123456791",
      "trade_type": "buy",
      "price": 45100.00,
      "amount": 0.0022,
      "value": 99.22,
      "fee": 0.0992,
      "fee_currency": "USDT",
      "profit": 0.00,
      "executed_at": "2023-01-16T16:45:00Z"
    },
    "timestamp": "2023-01-16T16:45:00Z"
  }
  ```

#### 4.2.3 订阅价格更新

- **订阅请求**：
  ```json
  {
    "action": "subscribe",
    "channel": "price",
    "payload": {
      "exchange": "binance",
      "symbol": "BTC/USDT"
    }
  }
  ```
- **数据消息**：
  ```json
  {
    "event": "price_update",
    "channel": "price",
    "exchange": "binance",
    "symbol": "BTC/USDT",
    "data": {
      "price": 45350.25,
      "24h_high": 46000.00,
      "24h_low": 44500.00,
      "24h_volume": 1250000000.00,
      "24h_change": 2.7
    },
    "timestamp": "2023-01-16T16:45:10Z"
  }
  ```

#### 4.2.4 订阅系统通知

- **订阅请求**：
  ```json
  {
    "action": "subscribe",
    "channel": "notifications"
  }
  ```
- **数据消息**：
  ```json
  {
    "event": "notification",
    "channel": "notifications",
    "data": {
      "id": "u47ac10b-58cc-4372-a567-0e02b2c3d580",
      "type": "warning",
      "title": "Strategy Warning",
      "message": "Your BTC Grid Strategy is approaching stop loss threshold.",
      "is_read": false,
      "created_at": "2023-01-16T16:50:00Z"
    },
    "timestamp": "2023-01-16T16:50:00Z"
  }
  ```

### 4.3 取消订阅

- **取消订阅请求**：
  ```json
  {
    "action": "unsubscribe",
    "channel": "strategy",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```
- **取消订阅响应**：
  ```json
  {
    "event": "unsubscribed",
    "channel": "strategy",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```

### 4.4 心跳机制

- **客户端发送**：
  ```json
  {
    "action": "ping",
    "timestamp": 1641456789
  }
  ```
- **服务器响应**：
  ```json
  {
    "event": "pong",
    "timestamp": 1641456790
  }
  ```

## 5. 错误处理

### 5.1 错误响应格式

所有API错误使用统一的响应格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field_name": "Specific error about this field",
      "other_info": "Additional context"
    }
  }
}
```

### 5.2 常见错误代码

| 错误代码                | HTTP状态码 | 描述             |
| ----------------------- | ---------- | ---------------- |
| `AUTHENTICATION_FAILED` | 401        | 认证失败         |
| `INVALID_TOKEN`         | 401        | 无效的令牌       |
| `TOKEN_EXPIRED`         | 401        | 令牌已过期       |
| `PERMISSION_DENIED`     | 403        | 权限不足         |
| `RESOURCE_NOT_FOUND`    | 404        | 资源不存在       |
| `VALIDATION_ERROR`      | 400        | 请求参数验证失败 |
| `INVALID_REQUEST`       | 400        | 无效的请求       |
| `RATE_LIMIT_EXCEEDED`   | 429        | 请求频率超过限制 |
| `INTERNAL_SERVER_ERROR` | 500        | 服务器内部错误   |
| `SERVICE_UNAVAILABLE`   | 503        | 服务暂时不可用   |
| `INSUFFICIENT_BALANCE`  | 400        | 账户余额不足     |
| `STRATEGY_ERROR`        | 400        | 策略操作错误     |

### 5.3 字段验证错误示例

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "upper_price": "Upper price must be greater than lower price",
      "grid_levels": "Grid levels must be between 2 and 100"
    }
  }
}
```

## 6. API限流策略

为保护系统资源和确保公平使用，API实施以下限流策略：

### 6.1 基本限流规则

| 端点类型      | 普通用户限制 | VIP用户限制   | 窗口大小 |
| ------------- | ------------ | ------------- | -------- |
| 认证相关      | 10 请求/分钟 | 20 请求/分钟  | 60秒     |
| 读取操作      | 60 请求/分钟 | 120 请求/分钟 | 60秒     |
| 写入操作      | 30 请求/分钟 | 60 请求/分钟  | 60秒     |
| 批量操作      | 5 请求/分钟  | 10 请求/分钟  | 60秒     |
| WebSocket消息 | 60 消息/分钟 | 120 消息/分钟 | 60秒     |

### 6.2 限流响应

当请求超过限制时，API返回`429 Too Many Requests`状态码：

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 60,
      "reset_at": "2023-01-16T17:00:00Z",
      "retry_after": 30
    }
  }
}
```

### 6.3 限流请求头

每个API响应包含以下限流相关的HTTP头：

```
X-Rate-Limit-Limit: 60
X-Rate-Limit-Remaining: 58
X-Rate-Limit-Reset: 1673888400
```

## 7. API版本策略

### 7.1 版本控制规则

- 版本号格式：`v{major}`
- 主版本（major）：不兼容的API变更
- 次版本（minor）：向后兼容的功能新增（不反映在URL中）
- 补丁版本（patch）：bug修复（不反映在URL中）

### 7.2 版本迁移

- 主版本变更会创建新的API路径（如`/api/v2/`）
- 旧版API在新版发布后保留至少6个月
- 版本弃用计划提前3个月公布

### 7.3 版本信息获取

- API响应头包含当前版本信息：
  ```
  X-API-Version: 1.2.5
  ```
- 系统状态API返回详细版本信息

## 8. 安全最佳实践

### 8.1 客户端安全建议

- 使用HTTPS确保传输加密
- 妥善保管API密钥和JWT令牌
- 实现适当的令牌刷新机制
- 验证服务器证书
- 实现请求签名验证

### 8.2 请求签名算法

```python
# 伪代码示例 - 不作实际实现
import hmac
import hashlib
import time

def generate_signature(api_secret, method, path, body):
    timestamp = str(int(time.time() * 1000))
    message = api_key + timestamp + method + path + (body or '')
    signature = hmac.new(
        api_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return timestamp, signature
```

### 8.3 JWT安全使用

- 令牌过期时间设置合理（访问令牌15分钟、刷新令牌7天）
- 实现令牌轮换机制
- 验证令牌签发者和受众
- 在需要更高安全级别的操作中使用附加验证

## 9. 附录

### 9.1 状态码列表（续）

| 状态码 | 描述                  | 使用场景                   |
| ------ | --------------------- | -------------------------- |
| 200    | OK                    | 成功的GET、PUT、PATCH请求  |
| 201    | Created               | 成功的POST请求，创建新资源 |
| 204    | No Content            | 成功的DELETE请求           |
| 400    | Bad Request           | 请求参数错误或无效         |
| 401    | Unauthorized          | 认证失败或缺少认证信息     |
| 403    | Forbidden             | 权限不足                   |
| 404    | Not Found             | 请求的资源不存在           |
| 409    | Conflict              | 资源冲突                   |
| 422    | Unprocessable Entity  | 请求格式正确但语义错误     |
| 429    | Too Many Requests     | 请求频率超过限制           |
| 500    | Internal Server Error | 服务器内部错误             |
| 503    | Service Unavailable   | 服务暂时不可用             |

### 9.2 API查询参数规范

| 参数            | 描述                      | 示例                      |
| --------------- | ------------------------- | ------------------------- |
| `page`          | 分页页码，从1开始         | `?page=2`                 |
| `page_size`     | 每页记录数，默认20        | `?page_size=50`           |
| `sort`          | 排序字段，前缀`-`表示降序 | `?sort=-created_at`       |
| `fields`        | 返回指定字段              | `?fields=id,name,status`  |
| `filter[field]` | 按字段过滤                | `?filter[status]=running` |
| `search`        | 全局搜索关键词            | `?search=bitcoin`         |
| `start_date`    | 日期范围起始              | `?start_date=2023-01-01`  |
| `end_date`      | 日期范围结束              | `?end_date=2023-01-31`    |

### 9.3 常用枚举值

#### 9.3.1 策略状态

| 值          | 描述           |
| ----------- | -------------- |
| `running`   | 策略正在运行中 |
| `stopped`   | 策略已停止     |
| `paused`    | 策略已暂停     |
| `pending`   | 策略待配置     |
| `error`     | 策略出现错误   |
| `completed` | 策略已完成     |

#### 9.3.2 交易类型

| 值     | 描述     |
| ------ | -------- |
| `buy`  | 买入交易 |
| `sell` | 卖出交易 |

#### 9.3.3 网格类型

| 值           | 描述       |
| ------------ | ---------- |
| `arithmetic` | 等差网格   |
| `geometric`  | 等比网格   |
| `custom`     | 自定义网格 |

#### 9.3.4 账单状态

| 值         | 描述   |
| ---------- | ------ |
| `pending`  | 待支付 |
| `paid`     | 已支付 |
| `overdue`  | 逾期   |
| `canceled` | 已取消 |

### 9.4 WebSocket事件列表

| 事件                | 描述             | 频道            |
| ------------------- | ---------------- | --------------- |
| `strategy_update`   | 策略状态更新     | `strategy`      |
| `trade_executed`    | 交易执行完成     | `trades`        |
| `price_update`      | 价格更新         | `price`         |
| `notification`      | 用户通知         | `notifications` |
| `grid_level_update` | 网格级别状态更新 | `grid_levels`   |
| `order_update`      | 订单状态更新     | `orders`        |
| `balance_update`    | 账户余额更新     | `balance`       |
| `system_alert`      | 系统警报         | `system`        |

### 9.5 API密钥权限说明

| 权限      | 描述         | 适用端点           |
| --------- | ------------ | ------------------ |
| `read`    | 只读权限     | GET请求端点        |
| `trade`   | 交易权限     | 策略和订单管理端点 |
| `account` | 账户管理权限 | 用户资料和设置端点 |
| `billing` | 账单管理权限 | 充值和账单端点     |
| `admin`   | 管理权限     | 管理级别端点       |

## 10. API变更管理

### 10.1 兼容性保障

为确保API变更不会破坏现有客户端应用，我们遵循以下兼容性准则：

1. **字段添加**：可随时添加新字段，不视为破坏性变更
2. **废弃而非删除**：不直接删除字段，先标记为废弃
3. **保留行为**：维持现有端点的基本行为
4. **扩展而非修改**：通过添加新端点扩展功能，而非修改现有端点

### 10.2 废弃流程

对于需要废弃的API特性：

1. **通知**：至少提前3个月通知用户
2. **标记**：在响应中添加废弃警告
   ```
   X-API-Deprecated: "This field will be removed in v2 (2023-06-01)"
   ```
3. **文档**：在API文档中明确标记废弃内容
4. **迁移指南**：提供详细的迁移方案

### 10.3 版本共存

主要版本更新时：

1. **并行运行**：新旧版本并行运行至少6个月
2. **重定向支持**：提供从旧版到新版的重定向机制
3. **转换层**：在服务器端实现版本转换，减少客户端负担

## 11. API文档与工具

### 11.1 文档格式

API文档采用OpenAPI 3.0规范编写，提供：

1. **人类可读文档**：包含详细说明和示例
2. **机器可读规范**：支持自动化工具和代码生成
3. **交互式文档**：通过Swagger UI提供可交互测试

### 11.2 文档访问

- **开发文档**：`https://docs.gridtrader.com/api/`
- **OpenAPI规范**：`https://api.gridtrader.com/api/v1/openapi.json`
- **Swagger UI**：`https://api.gridtrader.com/api/v1/docs/`

### 11.3 开发工具与SDK

- **官方SDK**：
  - JavaScript: `gridtrader-js`
  - Python: `gridtrader-python`
  - Java: `gridtrader-java`
  
- **工具和示例**：
  - Postman集合：`https://www.postman.com/gridtrader/workspace`
  - 示例应用：`https://github.com/gridtrader/examples`
  - 命令行工具：`gridtrader-cli`

## 12. 结论

本API设计文档详细描述了加密货币网格交易系统的API接口，包括RESTful API和WebSocket API。这些接口提供了用户认证、策略管理、交易执行、数据分析等功能，是前端应用与后端系统之间通信的基础。

API设计遵循RESTful原则，采用统一的请求和响应格式，实现版本控制和安全保障。通过WebSocket提供实时数据更新，减少轮询需求。文档详细说明了各端点的功能、参数和响应格式，为开发者提供了全面的参考。

随着系统的演进，API将继续发展和优化，但会遵循兼容性原则，确保现有客户端应用不受影响。未来的扩展将通过新端点和字段添加实现，同时保持现有功能的稳定性和可靠性。

## 2. WebSocket扩展设计

### 2.1 错误通知格式

WebSocket错误响应使用如下统一格式:

```json
{
  "event": "error",
  "channel": "channel_name",
  "error": {
    "code": "ERROR_CODE",
    "message": "人类可读的错误消息",
    "details": {
      "field_name": "字段相关的错误详情",
      "context": "错误发生的上下文"
    },
    "timestamp": "2023-01-15T12:00:00Z",
    "request_id": "unique-request-id",
    "suggested_action": "建议用户采取的操作"
  }
}
```

### 2.2 网格层状态更新频道

#### 2.2.1 订阅网格层状态更新

- **订阅请求**:
  ```json
  {
    "action": "subscribe",
    "channel": "grid_levels",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```
- **订阅响应**:
  ```json
  {
    "event": "subscribed",
    "channel": "grid_levels",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```

#### 2.2.2 单个网格层更新消息

- **数据消息**:
  ```json
  {
    "event": "grid_level_update",
    "channel": "grid_levels",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "data": {
      "level_id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
      "sequence_number": 2,
      "status": "filled",
      "upper_price": 45000.00,
      "lower_price": 44000.00,
      "interval_percent": 1.0,
      "take_profit_percent": 1.0,
      "open_rebound_percent": 0.5,
      "close_rebound_percent": 0.3,
      "invest_amount": 100.00,
      "filled_price": 44500.00,
      "filled_amount": 0.0022,
      "filled_value": 97.90,
      "unrealized_profit": 1.25,
      "profit_percent": 1.28,
      "filled_at": "2023-01-15T14:35:00Z",
      "updated_at": "2023-01-15T14:35:00Z"
    },
    "timestamp": "2023-01-15T14:35:00Z"
  }
  ```

#### 2.2.3 批量网格层更新消息

- **数据消息**:
  ```json
  {
    "event": "grid_levels_batch_update",
    "channel": "grid_levels",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "data": [
      {
        "level_id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
        "sequence_number": 1,
        "status": "filled",
        "upper_price": 49000.00,
        "lower_price": 48000.00,
        "filled_price": 48500.00,
        "filled_amount": 0.0020,
        "filled_value": 97.00,
        "unrealized_profit": 0.75,
        "profit_percent": 0.77,
        "updated_at": "2023-01-15T14:35:00Z"
      },
      {
        "level_id": "a47ac10b-58cc-4372-a567-0e02b2c3d491",
        "sequence_number": 2,
        "status": "pending_tp",
        "upper_price": 48000.00,
        "lower_price": 47000.00,
        "filled_price": 47500.00,
        "filled_amount": 0.0021,
        "filled_value": 99.75,
        "unrealized_profit": 1.05,
        "profit_percent": 1.05,
        "updated_at": "2023-01-15T14:35:00Z"
      }
    ],
    "timestamp": "2023-01-15T14:35:00Z"
  }
  ```

#### 2.3.3 风控条件状态更新消息

- **数据消息**:
  ```json
  {
    "event": "risk_control_update",
    "channel": "risk_controls",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "data": {
      "risk_control_id": "r47ac10b-58cc-4372-a567-0e02b2c3d601",
      "name": "均价止盈",
      "is_enabled": false,
      "updated_at": "2023-01-15T15:35:00Z",
      "updated_by": "user",
      "update_reason": "manual_disable"
    },
    "timestamp": "2023-01-15T15:35:00Z"
  }
  ```

### 2.4 状态变更通知频道

#### 2.4.1 订阅状态变更通知

- **订阅请求**:
  ```json
  {
    "action": "subscribe",
    "channel": "status_changes",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```
- **订阅响应**:
  ```json
  {
    "event": "subscribed",
    "channel": "status_changes",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```

#### 2.4.2 状态变更消息

- **数据消息**:
  ```json
  {
    "event": "status_change",
    "channel": "status_changes",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "data": {
      "entity_type": "grid_level",
      "entity_id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
      "old_status": "unfilled",
      "new_status": "filled",
      "reason": "order_executed",
      "details": {
        "order_id": "binance_123456789",
        "price": 44500.00,
        "amount": 0.0022,
        "value": 97.90,
        "fee": 0.0979
      },
      "changed_at": "2023-01-15T14:35:00Z"
    },
    "timestamp": "2023-01-15T14:35:00Z"
  }
  ```

## 3. 枚举值定义

### 3.1 风控相关枚举

#### 3.1.1 风控动作类型

| 值      | 描述     |
| ------- | -------- |
| `open`  | 开仓操作 |
| `close` | 平仓操作 |

#### 3.1.2 风控方向

| 值            | 描述             |
| ------------- | ---------------- |
| `long`        | 做多方向（开仓） |
| `short`       | 做空方向（开仓） |
| `take_profit` | 止盈方向（平仓） |
| `stop_loss`   | 止损方向（平仓） |

#### 3.1.3 风控范围

| 值              | 描述       |
| --------------- | ---------- |
| `current_level` | 当前网格层 |
| `all_levels`    | 所有网格层 |

#### 3.1.4 风控指标类型

| 值          | 描述       |
| ----------- | ---------- |
| `avg_price` | 均价指标   |
| `amount`    | 金额指标   |
| `technical` | 技术指标   |
| `custom`    | 自定义指标 |

#### 3.1.5 风控条件

| 值             | 描述         |
| -------------- | ------------ |
| `greater_than` | 大于         |
| `less_than`    | 小于         |
| `equal`        | 等于         |
| `between`      | 介于两值之间 |

### 3.2 网格层状态枚举

| 值             | 描述   |
| -------------- | ------ |
| `unfilled`     | 未开仓 |
| `pending_open` | 待开仓 |
| `filled`       | 已开仓 |
| `pending_tp`   | 待止盈 |
| `closed`       | 已平仓 |

## 4. 错误码定义

| 错误代码                           | HTTP状态码 | 描述                               |
| ---------------------------------- | ---------- | ---------------------------------- |
| `RISK_CONTROL_NOT_FOUND`           | 404        | 风控条件不存在                     |
| `RISK_CONTROL_VALIDATION_ERROR`    | 400        | 风控条件验证错误                   |
| `RISK_TEMPLATE_NOT_FOUND`          | 404        | 风控模板不存在                     |
| `RISK_CONTROL_BATCH_ACTION_FAILED` | 400        | 批量操作失败                       |
| `GRID_LEVEL_NOT_FOUND`             | 404        | 网格层不存在                       |
| `GRID_LEVEL_UPDATE_FORBIDDEN`      | 403        | 网格层更新被禁止（已触发不可修改） |
| `GRID_LEVEL_STATUS_INVALID`        | 400        | 网格层状态无效                     |
| `WEBSOCKET_SUBSCRIPTION_FAILED`    | 400        | WebSocket订阅失败                  |
| `WEBSOCKET_INVALID_PAYLOAD`        | 400        | WebSocket无效载荷                  |

这些补充的API端点和WebSocket功能完全支持风控设置界面的所有功能，包括创建、编辑和删除风控条件，应用风控模板，以及实时监控网格层状态变化。同时，改进后的错误通知格式提供了更详细的上下文信息，有助于用户快速理解和解决问题。


# API 设计文档修改与补充建议

我将按照前面分析的问题点，逐一提供详细的补充和修改建议，明确指出在原文档中需要添加或替换的内容。

## A. 批量操作相关API

在原文档的**3.2 策略管理API**部分，在"3.2.9 获取策略性能指标"之后添加以下内容：

### 3.2.10 批量策略操作

- **请求**：`POST /strategies/batch-action/`
- **描述**：对多个策略执行批量操作（启动、停止、删除等）
- **权限**：认证用户
- **请求体**：
  ```json
  {
    "action": "start",  // 可选值: "start", "stop", "delete", "pause"
    "strategy_ids": [
      "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "c47ac10b-58cc-4372-a567-0e02b2c3d480"
    ]
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "success": true,
    "message": "批量操作已成功执行",
    "results": [
      {
        "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "status": "success",
        "message": "策略已启动"
      },
      {
        "strategy_id": "c47ac10b-58cc-4372-a567-0e02b2c3d480",
        "status": "success",
        "message": "策略已启动"
      }
    ],
    "failed_count": 0,
    "success_count": 2
  }
  ```
- **错误响应** (400 Bad Request)：
  ```json
  {
    "error": {
      "code": "INVALID_ACTION",
      "message": "指定的操作无效",
      "details": {
        "valid_actions": ["start", "stop", "delete", "pause"]
      }
    }
  }
  ```

## B. 网格层级管理API不完整

在原文档的**3.3 网格层级API**部分，"3.3.1 获取网格层级列表"之后添加以下内容（并将原有的后续小节序号顺序后移）：

### 3.3.2 创建网格层级

- **请求**：`POST /strategies/{id}/grid-levels/`
- **描述**：为特定策略创建新的网格层级
- **权限**：策略所有者
- **请求体**：
  ```json
  {
    "sequence_number": 5,
    "interval_percent": 1.0,
    "take_profit_percent": 1.0,
    "open_rebound_percent": 0.5,
    "close_rebound_percent": 0.3,
    "invest_amount": 100.00,
    "upper_price": 45000.00,
    "lower_price": 44550.00
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "id": "a47ac10b-58cc-4372-a567-0e02b2c3d495",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "sequence_number": 5,
    "interval_percent": 1.0,
    "take_profit_percent": 1.0,
    "open_rebound_percent": 0.5,
    "close_rebound_percent": 0.3,
    "invest_amount": 100.00,
    "upper_price": 45000.00,
    "lower_price": 44550.00,
    "is_filled": false,
    "filled_price": null,
    "filled_amount": null,
    "filled_value": null,
    "filled_at": null,
    "created_at": "2023-01-16T10:30:00Z"
  }
  ```

### 3.3.3 批量创建网格层级

- **请求**：`POST /strategies/{id}/grid-levels/batch/`
- **描述**：为特定策略批量创建多个网格层级
- **权限**：策略所有者
- **请求体**：
  ```json
  {
    "grid_levels": [
      {
        "sequence_number": 5,
        "interval_percent": 1.0,
        "take_profit_percent": 1.0,
        "open_rebound_percent": 0.5,
        "close_rebound_percent": 0.3,
        "invest_amount": 100.00,
        "upper_price": 45000.00,
        "lower_price": 44550.00
      },
      {
        "sequence_number": 6,
        "interval_percent": 1.0,
        "take_profit_percent": 1.0,
        "open_rebound_percent": 0.5,
        "close_rebound_percent": 0.3,
        "invest_amount": 100.00,
        "upper_price": 44550.00,
        "lower_price": 44104.50
      }
    ]
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "success": true,
    "message": "已成功创建2个网格层级",
    "grid_levels": [
      {
        "id": "a47ac10b-58cc-4372-a567-0e02b2c3d495",
        "sequence_number": 5,
        "upper_price": 45000.00,
        "lower_price": 44550.00
      },
      {
        "id": "a47ac10b-58cc-4372-a567-0e02b2c3d496",
        "sequence_number": 6,
        "upper_price": 44550.00,
        "lower_price": 44104.50
      }
    ]
  }
  ```

## C. 管理中心API不足

在原文档的最后，添加以下新的章节：

## 13. 管理中心API

### 13.1 代理管理API

#### 13.1.1 获取所有代理列表

- **请求**：`GET /admin/agents/`
- **描述**：获取系统中所有代理用户列表
- **权限**：管理员
- **查询参数**：
  - `status`: 代理状态过滤 (active, inactive, pending)
  - `level`: 代理级别过滤 (1, 2, 3)
  - `search`: 搜索关键词
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 15,
    "next": "https://api.gridtrader.com/api/v1/admin/agents/?page=2",
    "previous": null,
    "results": [
      {
        "id": "m47ac10b-58cc-4372-a567-0e02b2c3d530",
        "username": "agent1@example.com",
        "name": "王经理",
        "email": "agent1@example.com",
        "phone": "+8613800138000",
        "agent_level": 1,
        "agent_status": "active",
        "total_referrals": 25,
        "active_referrals": 18,
        "total_commission": 350.75,
        "invitation_code": "AGENT123",
        "created_at": "2022-12-01T00:00:00Z",
        "custom_commission_rate": 30.0
      },
      {
        "id": "m47ac10b-58cc-4372-a567-0e02b2c3d531",
        "username": "agent2@example.com",
        "name": "李总",
        "email": "agent2@example.com",
        "phone": "+8613900139000",
        "agent_level": 1,
        "agent_status": "active",
        "total_referrals": 18,
        "active_referrals": 15,
        "total_commission": 280.50,
        "invitation_code": "AGENT456",
        "created_at": "2022-12-05T00:00:00Z",
        "custom_commission_rate": null
      }
    ]
  }
  ```

#### 13.1.2 更新代理状态和权限

- **请求**：`PUT /admin/agents/{id}/`
- **描述**：更新特定代理的状态和权限
- **权限**：管理员
- **请求体**：
  ```json
  {
    "agent_status": "inactive",
    "agent_level": 2,
    "custom_commission_rate": 35.0,
    "is_suspended": false
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "id": "m47ac10b-58cc-4372-a567-0e02b2c3d530",
    "username": "agent1@example.com",
    "name": "王经理",
    "agent_level": 2,
    "agent_status": "inactive",
    "custom_commission_rate": 35.0,
    "is_suspended": false,
    "updated_at": "2023-01-16T15:30:00Z",
    "updated_by": "admin@example.com"
  }
  ```

#### 13.1.3 批准代理申请

- **请求**：`POST /admin/agents/applications/{id}/approve/`
- **描述**：批准用户的代理申请
- **权限**：管理员
- **请求体**：
  ```json
  {
    "agent_level": 1,
    "custom_commission_rate": 30.0,
    "notes": "审核通过，表现良好的用户"
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "success": true,
    "message": "代理申请已批准",
    "agent_id": "m47ac10b-58cc-4372-a567-0e02b2c3d532",
    "username": "agent3@example.com",
    "invitation_code": "AGENT789",
    "approved_at": "2023-01-16T16:00:00Z"
  }
  ```

### 13.2 用户管理API

#### 13.2.1 获取所有用户列表

- **请求**：`GET /admin/users/`
- **描述**：获取系统中所有用户列表
- **权限**：管理员
- **查询参数**：
  - `status`: 用户状态过滤 (active, inactive, suspended)
  - `role`: 用户角色过滤 (user, agent, admin)
  - `search`: 搜索关键词
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 50,
    "next": "https://api.gridtrader.com/api/v1/admin/users/?page=2",
    "previous": null,
    "results": [
      {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "username": "user1@example.com",
        "name": "John Doe",
        "email": "user1@example.com",
        "phone": "+1234567890",
        "role": "user",
        "status": "active",
        "is_agent": false,
        "agent_level": 0,
        "balance": 1000.50,
        "active_strategies_count": 3,
        "created_at": "2023-01-01T12:00:00Z",
        "last_login": "2023-01-15T10:30:00Z",
        "referrer_id": "m47ac10b-58cc-4372-a567-0e02b2c3d530"
      }
    ]
  }
  ```

#### 13.2.2 更新用户状态

- **请求**：`PUT /admin/users/{id}/`
- **描述**：更新特定用户的状态
- **权限**：管理员
- **请求体**：
  ```json
  {
    "status": "suspended",
    "notes": "违反平台规则，暂时封禁",
    "suspension_end_date": "2023-02-16T00:00:00Z"
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "username": "user1@example.com",
    "name": "John Doe",
    "status": "suspended",
    "suspension_end_date": "2023-02-16T00:00:00Z",
    "updated_at": "2023-01-16T16:30:00Z",
    "updated_by": "admin@example.com"
  }
  ```

### 13.3 系统配置API

#### 13.3.1 获取系统配置

- **请求**：`GET /admin/system/config/`
- **描述**：获取系统全局配置
- **权限**：管理员
- **成功响应** (200 OK)：
  ```json
  {
    "system_settings": {
      "default_commission_rate": 25.0,
      "minimum_deposit_amount": 10.0,
      "maximum_strategies_per_user": 20,
      "maintenance_mode": false,
      "registration_enabled": true,
      "require_email_verification": true
    },
    "fee_settings": {
      "base_fee_rate": 5.0,
      "vip_fee_rate": 3.0,
      "minimum_fee_amount": 0.1,
      "settlement_days": [1, 15]
    },
    "agent_settings": {
      "default_commission_rates": {
        "level_1": 30.0,
        "level_2": 20.0, 
        "level_3": 10.0
      },
      "auto_approval": false,
      "minimum_active_users": 5
    }
  }
  ```

#### 13.3.2 更新系统配置

- **请求**：`PUT /admin/system/config/`
- **描述**：更新系统全局配置
- **权限**：管理员
- **请求体**：
  ```json
  {
    "system_settings": {
      "default_commission_rate": 20.0,
      "minimum_deposit_amount": 20.0
    },
    "fee_settings": {
      "base_fee_rate": 4.5
    }
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "success": true,
    "message": "系统配置已更新",
    "updated_fields": ["default_commission_rate", "minimum_deposit_amount", "base_fee_rate"],
    "updated_at": "2023-01-16T17:00:00Z"
  }
  ```

## D. 代理数据统计API不全面

在原文档的**3.7 代理分润API**部分，在"3.7.4 获取代理设置"之后添加以下内容：

#### 3.7.5 获取佣金统计数据

- **请求**：`GET /agents/commissions/statistics/`
- **描述**：获取代理佣金的统计数据和趋势
- **权限**：代理用户
- **查询参数**：
  - `period`: 统计周期 (daily, weekly, monthly)
  - `start_date`: 开始日期
  - `end_date`: 结束日期
- **成功响应** (200 OK)：
  ```json
  {
    "summary": {
      "total_commission": 350.75,
      "current_period_commission": 45.30,
      "previous_period_commission": 38.20,
      "growth_rate": 18.59,
      "average_commission_per_user": 14.03,
      "active_users_count": 18,
      "inactive_users_count": 7
    },
    "trends": [
      {
        "period": "2023-01",
        "commission": 35.50,
        "users_count": 22,
        "active_users_count": 15,
        "average_per_user": 2.37
      },
      {
        "period": "2023-02",
        "commission": 38.20,
        "users_count": 24,
        "active_users_count": 16,
        "average_per_user": 2.39
      },
      {
        "period": "2023-03",
        "commission": 45.30,
        "users_count": 25,
        "active_users_count": 18,
        "average_per_user": 2.52
      }
    ],
    "user_performance": [
      {
        "user_id": "n47ac10b-58cc-4372-a567-0e02b2c3d540",
        "username": "user1@example.com",
        "total_commission": 25.00,
        "active_strategies": 3,
        "last_activity": "2023-03-15T14:30:00Z"
      },
      {
        "user_id": "o47ac10b-58cc-4372-a567-0e02b2c3d541",
        "username": "user2@example.com",
        "total_commission": 15.00,
        "active_strategies": 2,
        "last_activity": "2023-03-14T10:15:00Z"
      }
    ]
  }
  ```

#### 3.7.6 获取下线用户统计数据

- **请求**：`GET /agents/referrals/statistics/`
- **描述**：获取代理下线用户的统计数据
- **权限**：代理用户
- **成功响应** (200 OK)：
  ```json
  {
    "summary": {
      "total_users": 25,
      "active_users": 18,
      "inactive_users": 7,
      "new_users_this_month": 3,
      "average_activity_days": 15.3,
      "average_strategies_per_user": 2.4,
      "total_trading_volume": 32500.00
    },
    "activity_trends": [
      {
        "period": "2023-01",
        "new_users": 10,
        "active_users": 10,
        "inactive_users": 0,
        "total_volume": 12500.00
      },
      {
        "period": "2023-02",
        "new_users": 12,
        "active_users": 15,
        "inactive_users": 7,
        "total_volume": 18500.00
      },
      {
        "period": "2023-03",
        "new_users": 3,
        "active_users": 18,
        "inactive_users": 7, 
        "total_volume": 32500.00
      }
    ],
    "user_categories": {
      "by_strategy_count": {
        "0": 5,
        "1-2": 10,
        "3-5": 7,
        ">5": 3
      },
      "by_trading_volume": {
        "<100": 6,
        "100-500": 9,
        "500-1000": 7,
        ">1000": 3
      }
    }
  }
  ```

## E. 风控设置UI与API不完全匹配

在原文档中添加新的章节：

## 14. 风控设置API

### 14.1 风控条件管理API

#### 14.1.1 获取风控条件列表

- **请求**：`GET /risk-controls/`
- **描述**：获取用户所有风控条件
- **权限**：认证用户
- **查询参数**：
  - `strategy_id`: 策略ID过滤
  - `action_type`: 动作类型过滤 (open, close)
  - `is_enabled`: 是否启用 (true, false)
  - `page`: 页码
  - `page_size`: 每页条数
- **成功响应** (200 OK)：
  ```json
  {
    "count": 15,
    "next": "https://api.gridtrader.com/api/v1/risk-controls/?page=2",
    "previous": null,
    "results": [
      {
        "id": "r47ac10b-58cc-4372-a567-0e02b2c3d601",
        "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "strategy_name": "BTC网格策略",
        "name": "均价止盈",
        "weight": 1,
        "action_type": "close",
        "direction": "take_profit",
        "scope": "all_levels",
        "indicator": "avg_price",
        "indicator_params": {},
        "condition": "greater_than",
        "threshold": 5.0,
        "threshold2": null,
        "is_enabled": true,
        "created_at": "2023-01-15T12:00:00Z",
        "updated_at": "2023-01-15T12:00:00Z"
      },
      {
        "id": "r47ac10b-58cc-4372-a567-0e02b2c3d602",
        "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "strategy_name": "BTC网格策略",
        "name": "总资金止损",
        "weight": 2,
        "action_type": "close",
        "direction": "stop_loss",
        "scope": "all_levels",
        "indicator": "amount",
        "indicator_params": {},
        "condition": "less_than",
        "threshold": -50.0,
        "threshold2": null,
        "is_enabled": true,
        "created_at": "2023-01-15T12:15:00Z",
        "updated_at": "2023-01-15T12:15:00Z"
      }
    ]
  }
  ```

#### 14.1.2 创建风控条件

- **请求**：`POST /risk-controls/`
- **描述**：创建新的风控条件
- **权限**：认证用户
- **请求体**：
  ```json
  {
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "CCI指标过滤",
    "weight": 1,
    "action_type": "open",
    "direction": "long",
    "scope": "current_level",
    "indicator": "technical",
    "indicator_params": {
      "indicator_name": "cci",
      "period": 14
    },
    "condition": "less_than",
    "threshold": 100,
    "is_enabled": true
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "id": "r47ac10b-58cc-4372-a567-0e02b2c3d603",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "strategy_name": "BTC网格策略",
    "name": "CCI指标过滤",
    "weight": 1,
    "action_type": "open",
    "direction": "long",
    "scope": "current_level",
    "indicator": "technical",
    "indicator_params": {
      "indicator_name": "cci",
      "period": 14
    },
    "condition": "less_than",
    "threshold": 100,
    "threshold2": null,
    "is_enabled": true,
    "created_at": "2023-01-15T14:30:00Z",
    "updated_at": "2023-01-15T14:30:00Z"
  }
  ```

#### 14.1.3 获取风控条件详情

- **请求**：`GET /risk-controls/{id}/`
- **描述**：获取特定风控条件详情
- **权限**：条件所有者
- **成功响应** (200 OK)：与创建响应格式相同

#### 14.1.4 更新风控条件

- **请求**：`PUT /risk-controls/{id}/`
- **描述**：更新风控条件
- **权限**：条件所有者
- **请求体**：与创建请求格式相同
- **成功响应** (200 OK)：与创建响应格式相同

#### 14.1.5 删除风控条件

- **请求**：`DELETE /risk-controls/{id}/`
- **描述**：删除风控条件
- **权限**：条件所有者
- **成功响应** (204 No Content)

### 14.2 风控模板API

#### 14.2.1 获取风控模板列表

- **请求**：`GET /risk-control-templates/`
- **描述**：获取系统预定义和用户自定义的风控模板
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "system_templates": [
      {
        "id": "s47ac10b-58cc-4372-a567-0e02b2c3d701",
        "name": "保守风控模板",
        "description": "适合风险偏好低的用户，提供强力止损保护",
        "template_type": "system",
        "conditions_count": 5
      },
      {
        "id": "s47ac10b-58cc-4372-a567-0e02b2c3d702",
        "name": "平衡风控模板",
        "description": "平衡风险和收益的风控模板",
        "template_type": "system",
        "conditions_count": 4
      }
    ],
    "user_templates": [
      {
        "id": "u47ac10b-58cc-4372-a567-0e02b2c3d801",
        "name": "我的自定义模板",
        "description": "个人定制的风控规则集",
        "template_type": "user",
        "conditions_count": 3,
        "created_at": "2023-01-15T18:30:00Z"
      }
    ]
  }
  ```

#### 14.2.2 获取风控模板详情

- **请求**：`GET /risk-control-templates/{id}/`
- **描述**：获取风控模板详情，包括所有条件
- **权限**：认证用户
- **成功响应** (200 OK)：
  ```json
  {
    "id": "s47ac10b-58cc-4372-a567-0e02b2c3d701",
    "name": "保守风控模板",
    "description": "适合风险偏好低的用户，提供强力止损保护",
    "template_type": "system",
    "conditions": [
      {
        "name": "均价止盈",
        "weight": 1,
        "action_type": "close",
        "direction": "take_profit",
        "scope": "all_levels",
        "indicator": "avg_price",
        "indicator_params": {},
        "condition": "greater_than",
        "threshold": 3.0,
        "threshold2": null
      },
      {
        "name": "均价止损",
        "weight": 2,
        "action_type": "close",
        "direction": "stop_loss",
        "scope": "all_levels",
        "indicator": "avg_price",
        "indicator_params": {},
        "condition": "less_than",
        "threshold": -2.0,
        "threshold2": null
      }
    ]
  }
  ```

#### 14.2.3 创建风控模板

- **请求**：`POST /risk-control-templates/`
- **描述**：创建新的用户自定义风控模板
- **权限**：认证用户
- **请求体**：
  ```json
  {
    "name": "我的趋势跟踪模板",
    "description": "结合技术指标的趋势跟踪风控规则",
    "conditions": [
      {
        "name": "RSI过滤开仓",
        "weight": 1,
        "action_type": "open",
        "direction": "long",
        "scope": "current_level",
        "indicator": "technical",
        "indicator_params": {
          "indicator_name": "rsi",
          "period": 14
        },
        "condition": "greater_than",
        "threshold": 30
      }
    ]
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "id": "u47ac10b-58cc-4372-a567-0e02b2c3d802",
    "name": "我的趋势跟踪模板",
    "description": "结合技术指标的趋势跟踪风控规则",
    "template_type": "user",
    "conditions_count": 1,
    "created_at": "2023-01-16T19:30:00Z"
  }
  ```

#### 14.2.4 应用风控模板

- **请求**：`POST /strategies/{id}/apply-risk-template/`
- **描述**：将风控模板应用到特定策略
- **权限**：策略所有者
- **请求体**：
  ```json
  {
    "template_id": "s47ac10b-58cc-4372-a567-0e02b2c3d701",
    "replace_existing": true
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "success": true,
    "message": "风控模板已成功应用",
    "applied_conditions_count": 5,
    "replaced_conditions_count": 3
  }
  ```

## F. WebSocket实时数据接口需要扩展

在原文档的**4. WebSocket API**部分的末尾，添加以下内容：

### 4.5 网格层状态频道

#### 4.5.1 订阅网格层状态

- **订阅请求**:
  ```json
  {
    "action": "subscribe",
    "channel": "grid_levels",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```
- **订阅响应**:
  ```json
  {
    "event": "subscribed",
    "channel": "grid_levels",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```

#### 4.5.2 网格层状态更新消息

- **数据消息**:
  ```json
  {
    "event": "grid_level_update",
    "channel": "grid_levels",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "data": {
      "level_id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
      "sequence_number": 2,
      "status": "filled",
      "upper_price": 45000.00,
      "lower_price": 44000.00,
      "interval_percent": 1.0,
      "take_profit_percent": 1.0,
      "open_rebound_percent": 0.5,
      "close_rebound_percent": 0.3,
      "invest_amount": 100.00,
      "filled_price": 44500.00,
      "filled_amount": 0.0022,
      "filled_value": 97.90,
      "unrealized_profit": 1.25,
      "profit_percent": 1.28,
      "filled_at": "2023-01-15T14:35:00Z",
      "updated_at": "2023-01-15T14:35:00Z"
    },
    "timestamp": "2023-01-15T14:35:00Z"
  }
  ```

### 4.6 风控通知频道

#### 4.6.1 订阅风控通知

- **订阅请求**:
  ```json
  {
    "action": "subscribe",
    "channel": "risk_controls",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```
- **订阅响应**:
  ```json
  {
    "event": "subscribed",
    "channel": "risk_controls",
    "payload": {
      "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```

#### 4.6.2 风控条件触发消息

- **数据消息**:
  ```json
  {
    "event": "risk_control_triggered",
    "channel": "risk_controls",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "data": {
      "risk_control_id": "r47ac10b-58cc-4372-a567-0e02b2c3d601",
      "name": "均价止盈",
      "action_type": "close",
      "direction": "take_profit",
      "scope": "all_levels",
      "indicator": "avg_price",
      "condition": "greater_than",
      "threshold": 5.0,
      "current_value": 5.2,
      "affected_levels": [1, 2, 3],
      "triggered_at": "2023-01-15T15:30:00Z"
    },
    "timestamp": "2023-01-15T15:30:00Z"
  }
  ```

### 4.7 账户余额频道

#### 4.7.1 订阅账户余额

- **订阅请求**:
  ```json
  {
    "action": "subscribe",
    "channel": "balance"
  }
  ```
- **订阅响应**:
  ```json
  {
    "event": "subscribed",
    "channel": "balance"
  }
  ```

#### 4.7.2 余额更新消息

- **数据消息**:
  ```json
  {
    "event": "balance_update",
    "channel": "balance",
    "data": {
      "previous_balance": 1000.50,
      "current_balance": 990.25,
      "change_amount": -10.25,
      "change_type": "fee",
      "reference": "账单 INV-2023-004",
      "transaction_id": "t47ac10b-58cc-4372-a567-0e02b2c3d590",
      "updated_at": "2023-01-16T20:00:00Z"
    },
    "timestamp": "2023-01-16T20:00:00Z"
  }
  ```

# 加密货币网格交易系统开发规划与问题修正方案

基于对所有上传文件的全面分析，我已发现多个需要修正的关键问题，并将提供详细的解决方案。

## 1. 系统架构与职责分离问题

### 1.1 客户端-服务端职责分离调整

**问题**: 客户端和服务端职责边界模糊，特别是在风控处理和数据同步方面。

**解决方案**:

在**API设计文档**中修改以下端点:
- 移除所有`/strategies/{id}/risk-controls/`和`/risk-controls/`端点，因为风控应完全由客户端处理
- 添加仅用于数据分析的统计端点，例如`/analytics/risk-controls-performance`

在**数据模型设计**中明确数据存储职责:
1. **客户端专属数据**:
   - 风控条件配置(local_risk_controls)
   - 网格层详细配置(local_grid_levels)
   - API密钥(local_exchange_accounts)
   
2. **客户端上报到服务端的结果数据**:
   - 交易记录(用于计费和分析)
   - 盈亏统计(用于业绩分析)
   
3. **服务端专属数据**:
   - 用户资料
   - 账单和费用
   - 代理关系

### 1.2 添加状态恢复数据结构

在**数据模型设计**文档中添加以下表结构:

```sql
CREATE TABLE local_recovery_points (
    id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    snapshot TEXT NOT NULL, -- JSON格式的完整策略状态
    status TEXT NOT NULL,
    metadata TEXT, -- 额外信息
    FOREIGN KEY (strategy_id) REFERENCES local_strategies(id)
);

CREATE INDEX idx_recovery_points_strategy ON local_recovery_points(strategy_id);
CREATE INDEX idx_recovery_points_timestamp ON local_recovery_points(timestamp);
```

这个表将用于在客户端存储策略状态快照，实现断线重连后的精确恢复。

## 2. 实时数据流与同步机制增强

### 2.1 增强WebSocket设计

在**API设计文档**的WebSocket部分添加以下内容:

```
### 4.8 策略状态变更通知

#### 4.8.1 客户端状态变更报告
- **客户端发送**:
  ```json
  {
    "action": "status_update",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "running",
    "current_price": 45300.50,
    "last_trade_time": "2023-01-16T16:45:00Z",
    "performance_metrics": {
      "total_profit": 26.50,
      "trades_count": 45
    },
    "client_timestamp": 1641456789,
    "sync_token": "abcd1234"
  }
  ```

- **服务器响应**:
  ```json
  {
    "event": "status_acknowledged",
    "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "sync_token": "abcd1234",
    "server_timestamp": 1641456790
  }
  ```

### 4.9 断线重连同步机制

#### 4.9.1 断线重连请求
- **客户端发送**:
  ```json
  {
    "action": "reconnect_sync",
    "last_sync_token": "abcd1234",
    "strategies": [
      {
        "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "last_update_timestamp": 1641456789
      }
    ]
  }
  ```

- **服务器响应**:
  ```json
  {
    "event": "sync_status",
    "sync_required": true,
    "strategies": [
      {
        "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "server_last_update": 1641456795,
        "status": "server_ahead"
      }
    ]
  }
  ```
```

### 2.2 参数调整与历史追踪

在**数据模型设计**中添加以下表结构:

```sql
CREATE TABLE local_parameter_changes (
    id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    parameter_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP NOT NULL,
    changed_by TEXT NOT NULL,
    is_effective BOOLEAN NOT NULL DEFAULT 1,
    affected_grid_levels TEXT, -- 逗号分隔的层级ID列表
    synchronized BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (strategy_id) REFERENCES local_strategies(id)
);

CREATE INDEX idx_parameter_changes_strategy ON local_parameter_changes(strategy_id);
CREATE INDEX idx_parameter_changes_parameter ON local_parameter_changes(strategy_id, parameter_name);
```

在**API设计文档**中添加增量更新端点:

```
#### 3.2.5 增量更新策略参数

- **请求**：`PATCH /strategies/{id}/parameters/`
- **描述**：增量更新特定策略参数，无需替换整个配置
- **权限**：策略所有者
- **请求体**：
  ```json
  {
    "parameters": {
      "default_grid_spread": 1.2,
      "risk_controls.avg_price_tp_percent": 6.0
    },
    "affected_grid_levels": ["all", "unfilled"]
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "updated_parameters": ["default_grid_spread", "risk_controls.avg_price_tp_percent"],
    "effective_immediately": true,
    "affected_grid_levels_count": 3,
    "updated_at": "2023-01-15T16:45:00Z"
  }
  ```
```

## 3. 代理邀请链接功能设计

在**API设计文档**中添加:

```
### 3.7.7 生成邀请链接

- **请求**：`POST /agents/invitation-links/`
- **描述**：生成新的邀请链接
- **权限**：代理用户
- **请求体**：
  ```json
  {
    "expire_days": 30,
    "custom_message": "加入最佳网格交易平台，享受专属优惠",
    "max_uses": 100,
    "commission_override": 35.0
  }
  ```
- **成功响应** (201 Created)：
  ```json
  {
    "id": "t47ac10b-58cc-4372-a567-0e02b2c3d580",
    "invitation_code": "AG7X9P",
    "full_link": "https://gridtrader.com/register?ref=AG7X9P",
    "custom_message": "加入最佳网格交易平台，享受专属优惠",
    "expire_at": "2023-02-16T00:00:00Z",
    "max_uses": 100,
    "used_count": 0,
    "commission_override": 35.0,
    "created_at": "2023-01-16T00:00:00Z"
  }
  ```

### 3.7.8 获取邀请链接列表

- **请求**：`GET /agents/invitation-links/`
- **描述**：获取代理创建的所有邀请链接
- **权限**：代理用户
- **成功响应** (200 OK)：
  ```json
  {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "t47ac10b-58cc-4372-a567-0e02b2c3d580",
        "invitation_code": "AG7X9P",
        "full_link": "https://gridtrader.com/register?ref=AG7X9P",
        "custom_message": "加入最佳网格交易平台，享受专属优惠",
        "expire_at": "2023-02-16T00:00:00Z",
        "max_uses": 100,
        "used_count": 5,
        "active": true,
        "created_at": "2023-01-16T00:00:00Z"
      }
    ]
  }
  ```

### 3.7.9 更新或禁用邀请链接

- **请求**：`PATCH /agents/invitation-links/{id}/`
- **描述**：更新或禁用特定邀请链接
- **权限**：邀请链接所有者
- **请求体**：
  ```json
  {
    "active": false,
    "custom_message": "新的邀请信息"
  }
  ```
- **成功响应** (200 OK)：
  ```json
  {
    "id": "t47ac10b-58cc-4372-a567-0e02b2c3d580",
    "active": false,
    "custom_message": "新的邀请信息",
    "updated_at": "2023-01-16T10:00:00Z"
  }
  ```
```

在**数据模型设计**中添加:

```sql
CREATE TABLE agent_invitation_links (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL,
    invitation_code VARCHAR(20) NOT NULL UNIQUE,
    custom_message TEXT,
    expire_at TIMESTAMP,
    max_uses INTEGER,
    used_count INTEGER NOT NULL DEFAULT 0,
    commission_override DECIMAL(5,2),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_invitation_links_agent ON agent_invitation_links(agent_id);
CREATE INDEX idx_invitation_links_code ON agent_invitation_links(invitation_code);
```

## 4. 风控模型和UI一致性修正

针对**数据模型设计**文档中的风控表结构，修改为:

```sql
CREATE TABLE local_risk_controls (
    id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    name TEXT NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT 1,
    weight INTEGER NOT NULL,
    action_type TEXT NOT NULL,   -- "open"/"close"
    direction TEXT NOT NULL,     -- 开仓:"long"/"short", 平仓:"take_profit"/"stop_loss"
    scope TEXT NOT NULL,         -- "current_level"/"all_levels"
    range TEXT,                  -- UI中的"范围"字段
    indicator TEXT NOT NULL,     -- "avg_price"/"amount"/"technical"/"custom"
    indicator_params TEXT,       -- JSON格式的指标参数
    condition TEXT NOT NULL,     -- "greater_than"/"less_than"/"equal"/"between"
    threshold REAL NOT NULL,
    threshold2 REAL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES local_strategies(id)
);
```

这样设计与UI中的字段完全对应。

## 5. 数据模型与API统一化

为统一命名和结构:

1. 修改**数据模型设计**的表名:
   - 将`local_grid_levels`重命名为`local_grid_levels`保持一致
   - 确保所有API路径和数据库表名使用一致的命名模式

2. 修改**API设计文档**的返回结构，确保与数据模型一致:
   - 统一使用`grid_type`字段
   - 确保所有嵌套结构一致

3. 在服务层明确定义转换规则:
   ```python
   # 服务层转换示例
   def map_db_to_api_model(db_strategy):
       """将数据库模型转换为API响应模型"""
       return {
           "id": db_strategy.id,
           "name": db_strategy.name,
           "grid_type": db_strategy.grid_type,  # 确保字段名一致
           # ... 其他字段映射
       }
   ```

## 6. 技术栈和开发规划

根据实现指南和上述修改，推荐以下技术栈和开发计划:

### 6.1 技术栈确认

1. **客户端**:
   - 核心引擎: Python (异步架构)
   - UI: Electron + Vue.js
   - 本地数据库: SQLite
   - 网络库: aiohttp, websockets
   - 加密货币交易所API: ccxt
   
2. **服务端**:
   - Web框架: Django + Django REST Framework
   - 数据库: PostgreSQL
   - 缓存: Redis
   - WebSocket: Django Channels
   - 部署: Docker + Kubernetes

### 6.2 开发规划调整

1. **阶段一: 基础架构 (3周)**
   - 创建客户端和服务端代码仓库
   - 实现基础框架和目录结构
   - 设计数据模型和API接口
   - 配置开发环境和CI/CD流程

2. **阶段二: 核心功能开发 (10周)**
   - 客户端交易引擎实现
   - 风控系统开发
   - 交易所API集成
   - 本地数据管理
   - 服务端用户和权限系统
   - 计费和代理系统

3. **阶段三: UI开发 (6周)**
   - 策略管理界面
   - 网格配置界面
   - 风控设置界面
   - 用户中心和代理中心
   - 数据可视化组件

4. **阶段四: 系统集成与测试 (5周)**
   - 客户端与服务端集成
   - 单元测试和集成测试
   - 性能和安全测试
   - 用户体验测试

5. **阶段五: 优化与部署 (4周)**
   - 性能优化
   - 安全加固
   - 文档完善
   - 部署自动化

## 7. 实施建议

1. **强化分离式架构**:
   - 重新审视所有API和数据流，确保职责清晰
   - 建立严格的安全边界，敏感操作只在客户端执行
   - 保障API密钥等敏感信息只在客户端加密存储

2. **优化实时同步机制**:
   - 实现双向WebSocket通信
   - 设计健壮的断线重连和状态同步机制
   - 支持参数实时调整并追踪变更历史

3. **提升数据一致性**:
   - 客户端和服务端数据同步采用版本控制机制
   - 实现冲突检测和解决策略
   - 定期状态核对机制

4. **确保安全性**:
   - 客户端加密存储敏感信息
   - 服务端实现细粒度权限控制
   - 全面审计日志记录关键操作

5. **用户体验优化**:
   - 简化复杂功能的操作流程
   - 提供清晰的数据可视化
   - 实现响应式设计，适应不同设备

按照这个修正方案，系统将能够实现高度灵活的网格交易功能，同时保持客户端和服务端职责清晰分离，确保系统安全和高效运行。建议首先完成数据模型和API设计的修正，然后按照调整后的开发规划逐步实现各功能模块。



