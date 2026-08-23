# xbb印刷品定制数字化管理系统

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
- `xbb印刷品定制数字化管理系统-规划文档.md`：系统级规划（9 模块、技术栈、部署、报价复核）

## 当前状态
- **第 1 模块（基础信息）已完成**：6 表单 CRUD（类目/产品库/工厂库/物流服务商/客户/客户-业务员对照）+ 产品库/工厂库 Excel 批量导入 + 用户管理 + JWT 认证 + PC 6 管理页 + 移动端只读浏览。
- **第 2 模块（订单导入+销售订单）已完成**：Order/OrderItem/ExchangeRate 模型 + 订单 Excel 导入（upsert/关联/状态映射/毛利/未匹配清单）+ 毛利自动计算 + 客户↔跟单员映射 + 派单 + 汇率配置 + PC 4 页（列表/详情/表单/导入）+ 移动端 3 页（列表/详情/表单）。后端 54 测试 + 前端 5 测试全绿。
- 开发用 SQLite（ARM64 无原生 MySQL）；生产部署用 MySQL 8 + Windows 绿色安装包（待部署阶段）。
- **第 3 模块（跟单管理）已完成**：TrackingLog/TrackingPhoto 模型 + 8 节点状态机（接单→排产→生产中→质检→发货→签收→结算→回款，推进/驳回）+ MEDIA 照片上传（Pillow verify 校验 + 事务包裹）+ TrackingViewSet（advance/reject/timeline/my + 权限）+ PC 跟单工作台 + 移动端跟单工作台（完整功能）+ 订单详情时间线。后端 76 测试 + 前端 6 测试全绿。
- **第 4 模块（工厂结算）已完成**：FactoryPayment（OneToOne→OrderItem）+ FactoryPaymentRecord（多次付款）+ status 自动算（未结/部分结/已结）+ 一键生成（批量创建结算单）+ 工厂对账单（按工厂+日期汇总）+ 权限修复（generate 仅 admin/finance、delete 仅 admin、Record 数据范围）+ 删除回退 paid_amount + 事务包裹 + 安全测试。PC 3 页（列表/详情/对账）+ 移动端 3 页（完整功能）+ OrderDetail 结算状态区块。后端 90 测试 + 前端 7 测试全绿。
- **第 5 模块（物流管理）已完成**：Logistics 模型（FK→Order 多行 + seq 自动递增 + 两段物流关联 LogisticsProvider）+ LogisticsPermission（admin 全权/tracker 写/salesman 只读范围）+ tracker 创建限定派给自己订单 + PC 物流列表/表单 + 移动端列表/表单完整功能 + OrderDetail 物流发货区块。后端 104 测试 + 前端 8 测试全绿。
- **第 6 模块（轻财务）已完成**：PaymentIn 回款模型 + 收支流水聚合 API（四源统一：回款/工厂付款/物流费/服务费）+ openpyxl 导出 Excel + 无角色账号 qs.none() 兜底 + OrderDetail 精确 order ID 过滤。PC 收支流水页/回款登记 + 移动端列表。
- **第 7 模块（数据分析）已完成**：4 个聚合 API（销售结算表/工厂账单汇总/跟单信息汇总/管理人员报表）+ ECharts Dashboard 4 tab（折线图/饼图/柱状图）+ AnalyticsPermission（admin/finance only）+ tracking-summary 年份过滤修复 + sales 客户维度补充。
- **第 8 模块（系统管理）已完成**：ApprovalRequest 审批流（工厂结算/付款登记/订单变更/物流发货，admin 两态审批）+ is_approved 字段集成到 4 业务模型 + 批量导入/一键生成挂审 + 驳回重提路径 + OperationLog middleware JWT 解析修复 + BackupRecord 备份恢复（审批后自动+手动按钮+滚动保留1000份）。前端待审批/操作日志/备份管理三页。
- **全部 9 个模块开发完成。** 后端 163 测试全绿 + 前端 vitest 全绿 + build 成功。