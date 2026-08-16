# 辛巴印刷品定制数字化管理系统

印刷品定制企业（约 20 人，阿里国际站接外贸订单）的业务/跟单/工厂/物流协同数字化管理系统。独立 Web 系统，部署在客户本地 Windows 服务器。

## 技术栈
- 后端：Python 3.13 + Django 5.1 + DRF + SQLite（开发）/ MySQL 8（生产）
- 前端：Vue 3 + Vite + TypeScript + Element Plus（PC/平板）+ Vant（手机）
- 认证：JWT（djangorestframework-simplejwt）；4 角色：admin / salesman / tracker / finance
- 测试：pytest（后端 32 passed）、Vitest（前端 4 passed）

## 怎么跑

### 后端（端口 8000）
```bash
cd backend
python -m pip install -r requirements/dev.txt
python manage.py migrate
python manage.py create_groups          # 创建 4 个角色 Group
python manage.py runserver              # http://127.0.0.1:8000
```

### 前端（端口 5173，需 Node.js）
开发机为 Windows ARM64，Node.js 装在 `D:\Pad Windows Data\nodejs\node-v22.23.2-win-arm64\`，用前挂 PATH：
```bash
export PATH="/d/Pad Windows Data/nodejs/node-v22.23.2-win-arm64:$PATH"
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run dev                             # http://localhost:5173（Vite 代理 /api → 8000）
```

### 测试
```bash
cd backend && python -m pytest -v        # 32 passed
cd frontend && npx vitest run            # 4 passed
```

## 目录
- `backend/`：Django 项目（`apps/basic_info` 基础信息、`apps/accounts` 认证与用户、`common/` 通用库）
- `frontend/`：Vue3 项目（`src/views/basic_info` PC 管理页、`src/views/system` 用户管理、`src/views/m` 移动端只读）
- `docs/superpowers/specs/`：设计文档
- `docs/superpowers/plans/`：实现计划
- `辛巴印刷品定制数字化管理系统-规划文档.md`：系统级规划（9 模块、技术栈、部署、报价复核）

## 当前状态
- **第 1 模块（基础信息）已完成**：6 表单 CRUD（类目/产品库/工厂库/物流服务商/客户/客户-业务员对照）+ 产品库/工厂库 Excel 批量导入 + 用户管理 + JWT 认证 + PC 6 管理页 + 移动端只读浏览。
- **第 2 模块（订单导入+销售订单）已完成**：Order/OrderItem/ExchangeRate 模型 + 订单 Excel 导入（upsert/关联/状态映射/毛利/未匹配清单）+ 毛利自动计算 + 客户↔跟单员映射 + 派单 + 汇率配置 + PC 4 页（列表/详情/表单/导入）+ 移动端 3 页（列表/详情/表单）。后端 54 测试 + 前端 5 测试全绿。
- 开发用 SQLite（ARM64 无原生 MySQL）；生产部署用 MySQL 8 + Windows 绿色安装包（待部署阶段）。
- **第 3 模块（跟单管理）已完成**：TrackingLog/TrackingPhoto 模型 + 8 节点状态机（接单→排产→生产中→质检→发货→签收→结算→回款，推进/驳回）+ MEDIA 照片上传（Pillow verify 校验 + 事务包裹）+ TrackingViewSet（advance/reject/timeline/my + 权限）+ PC 跟单工作台 + 移动端跟单工作台（完整功能）+ 订单详情时间线。后端 76 测试 + 前端 6 测试全绿。
- 后续模块（待开发）：工厂结算、物流账单、轻财务、数据分析——见规划文档第 4 节。