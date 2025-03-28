# 用户中心-交易所API页面 UI 设计文档

## 页面结构

```
┌─────────────────────────────────────────────────────────────┐
│ 用户中心                                                    │
│ 管理您的交易所API密钥                                        │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                   标签页导航                            │ │
│ │ [个人资料] [交易所API] [账户余额] [偏好设置]             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                   API密钥说明                           │ │
│ │                                                         │ │
│ │ 请在交易所创建API密钥，然后添加到系统中...              │ │
│ │                                             [添加API]   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                   已添加的API密钥                       │ │
│ │ ┌─────┬────┬────┬─────┬────────┬────────┬───────────┐   │ │
│ │ │交易所│名称│权限│API Key│Secret │Pass   │操作       │   │ │
│ │ ├─────┼────┼────┼─────┼────────┼────────┼───────────┤   │ │
│ │ │Binance│主账户│交易│●●●●●●│●●●●●●●●│ -      │[编辑][删除]│   │ │
│ │ ├─────┼────┼────┼─────┼────────┼────────┼───────────┤   │ │
│ │ │OKX   │测试 │交易│●●●●●●│●●●●●●●●│●●●●●●●●│[编辑][删除]│   │ │
│ │ └─────┴────┴────┴─────┴────────┴────────┴───────────┘   │ │
│ │                                                         │ │
│ │ [+ 添加API]                                             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                   安全提示卡片                          │ │
│ │                                                         │ │
│ │ API密钥安全提示                                         │ │
│ │ • 在交易所创建API密钥时，仅启用交易权限...              │ │
│ │ • 建议在交易所设置API密钥的IP白名单...                  │ │
│ │ • 定期检查您的API密钥使用情况...                        │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 功能组件描述

### 1. 页面标题区
- 标题："用户中心"
- 副标题："管理您的交易所API密钥"

### 2. 标签页导航
- 标签页组件，包含四个选项卡：
  - 个人资料
  - 交易所API（当前选中状态）
  - 账户余额
  - 偏好设置
- 当前选中的标签页底色突出显示

### 3. API密钥说明
- 说明文本：解释API密钥用途和添加流程
- 添加API按钮：靠右对齐，点击后弹出添加API表单

### 4. 已添加的API密钥列表
- 表格组件，包含以下列：
  - 交易所：显示交易所名称，可能带有图标
  - 名称：用户自定义的API密钥名称
  - 权限：显示API权限级别（只读/交易）
  - API Key：部分隐藏的API Key
  - Secret：完全隐藏的API Secret
  - Passphrase：完全隐藏的API密码（如需）
  - 操作：编辑、删除按钮
- 行特性：
  - 鼠标悬停行高亮
  - 点击行可选中
  - 支持分页（如有多个API）
- 添加API行：表格底部的虚线框，点击后弹出添加API表单

### 5. 安全提示卡片
- 突出显示的蓝色背景卡片
- 包含API密钥安全使用建议
- 重点提示避免提现权限，设置IP白名单等

## 交互说明

1. **添加API交互**
   - 点击添加按钮弹出模态框
   - 交易所选择下拉菜单
   - 名称输入框
   - API Key/Secret输入框
   - Passphrase输入框（根据交易所需求显示）
   - 权限选择（只读/交易）
   - 添加/取消按钮

2. **编辑API交互**
   - 点击编辑按钮弹出模态框
   - 预填充现有数据
   - 部分字段可能无法修改（如API Key）
   - 更新/取消按钮

3. **删除API交互**
   - 点击删除按钮显示确认对话框
   - 确认/取消选项
   - 删除前警告可能影响运行中的策略

4. **敏感信息处理**
   - API Secret和Passphrase始终隐藏显示
   - API Key部分隐藏显示
   - 不支持查看完整信息，需要重新添加

## 数据需求

1. **API密钥数据结构**
```json
{
  "api_keys": [
    {
      "id": "api-key-uuid",
      "exchange": "binance",
      "name": "主交易账户",
      "api_key": "GHT567*********",
      "api_secret": "********************",
      "passphrase": null,
      "permission": "trade",
      "status": "active",
      "created_at": "2023-01-15T10:30:00Z",
      "last_used": "2023-05-20T14:25:30Z"
    }
  ]
}
```

2. **交易所数据结构**
```json
{
  "exchanges": [
    {
      "id": "binance",
      "name": "Binance",
      "logo_url": "https://example.com/logos/binance.png",
      "requires_passphrase": false
    },
    {
      "id": "okx",
      "name": "OKX",
      "logo_url": "https://example.com/logos/okx.png",
      "requires_passphrase": true
    }
  ]
}
```

## 状态管理

- API列表状态：加载中、加载成功、加载失败、空列表
- 添加/编辑表单状态：初始值、验证状态、提交状态
- 删除确认状态

## 响应式设计考虑

- 桌面端：完整表格布局
- 平板端：表格可横向滚动
- 移动端：卡片式布局，每个API密钥显示为卡片

## 特殊考虑

- 高度安全敏感的页面，需特别注意XSS防护
- 可能需要二次验证（如短信验证码）才能添加/编辑API
- 应考虑添加自动检测API有效性的功能
- 支持显示API最后使用时间
- 考虑添加API使用日志查看功能