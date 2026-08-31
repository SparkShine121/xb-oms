# xbb印刷品定制数字化管理系统

印刷品定制企业（约 20 人，阿里国际站接外贸订单）的业务/跟单/工厂/物流协同数字化管理系统。独立 Web 系统，部署在客户本地 Windows 服务器。覆盖从订单导入到回款结算的全流程，全部 9 个功能模块已开发完成。

## 技术栈

### 后端（Python 3.13，端口 8000）

| 组件 | 版本 | 用途 |
|------|------|------|
| Django | 5.1 | Web 框架，monorepo 按业务域分 app |
| Django REST Framework | ≥3.15 | API 层，统一 `{code, message, data}` 响应包装 |
| djangorestframework-simplejwt | ≥5.3 | JWT 认证（登录/登出/用户信息） |
| django-filter | ≥24.0 | 列表过滤 |
| openpyxl | ≥3.1 | Excel 批量导入（基础信息、订单模板）与财务导出 |
| Pillow | ≥10.0 | 跟单照片上传校验（image verify） |
| SQLite / MySQL 8 | — | 开发用 SQLite（ARM64 无原生 MySQL），生产用 MySQL 8 |
| pytest + pytest-django + factory_boy | ≥8.0 | 后端测试（163 个测试全绿） |

### 前端（Node.js 22，端口 5173）

| 组件 | 版本 | 用途 |
|------|------|------|
| Vue | 3.5 | 框架 |
| Vite | 8.2 | 构建与开发服务器（代理 `/api` → 8000） |
| TypeScript | 6.0 | 类型（`npm run build` 含 vue-tsc 类型检查） |
| Element Plus | 2.14 | PC/平板端组件库 |
| Vant | 4.10 | 手机端组件库 |
| Pinia | 4.0 | 状态管理（token/角色，sessionStorage 持久化，新标签页需重新登录） |
| vue-router | 5.2 | 路由（PC `/` 与移动端 `/m/` 双端分流） |
| ECharts | 6.1 | 数据分析图表（折线/饼图/柱状图） |
| axios | 1.19 | HTTP 封装（Bearer 注入、401 跳转、全局错误提示） |
| Vitest | 4.1 | 前端测试 |

### 认证与权限

- JWT 认证，4 个角色：**admin**（管理员）/ **salesman**（业务员）/ **tracker**（跟单员）/ **finance**（财务）
- 双层权限：操作级（`has_permission`）+ 对象级数据范围（`has_object_permission`），例如业务员只能看自己客户的订单、跟单员只能操作派给自己的订单

## 功能模块（9 个，全部完成）

| # | 模块 | 后端（`backend/apps/`） | 核心能力 |
|---|------|------------------------|----------|
| 1 | 基础信息 | `basic_info` | 类目/产品库/工厂库/物流服务商/客户/客户-业务员对照 6 表单 CRUD + Excel 批量导入 |
| 2 | 订单管理 | `orders` | Order/OrderItem/ExchangeRate + 订单 Excel 导入（阿里小满模板，upsert/状态映射）+ 毛利自动计算 + 客户↔跟单员映射派单 + 汇率配置 |
| 3 | 跟单管理 | `tracking` | TrackingLog/TrackingPhoto + 8 节点状态机（接单→排产→生产中→质检→发货→签收→结算→回款，支持推进/驳回）+ 照片上传（Pillow 校验 + 事务包裹） |
| 4 | 工厂结算 | `factory_payment` | FactoryPayment（OneToOne→OrderItem）+ 多次付款记录 + 结算状态自动计算（未结/部分结/已结）+ 一键生成结算单 + 工厂对账单 |
| 5 | 物流管理 | `logistics` | Logistics 多行物流记录（FK→Order，seq 自动递增）+ 两段物流关联物流服务商 + 角色权限控制 |
| 6 | 轻财务 | `finance` | PaymentIn 回款登记 + 收支流水四源聚合（回款/工厂付款/物流费/服务费）+ Excel 导出 |
| 7 | 数据分析 | `analytics` | 4 个聚合 API（销售结算表/工厂账单汇总/跟单信息汇总/管理人员报表）+ ECharts Dashboard（admin/finance 专属） |
| 8 | 系统管理 | `system_mgmt` | ApprovalRequest 审批流（工厂结算/付款登记/订单变更/物流发货，批量导入与一键生成挂审、驳回重提）+ OperationLog 操作日志 + BackupRecord 备份恢复（滚动保留 1000 份） |
| 9 | 账号与认证 | `accounts` | JWT 登录/登出/用户信息 + 用户管理 + `create_groups` 角色初始化命令 |

### 双端界面

- **PC/平板端**（`/`，Element Plus）：基础信息、订单、跟单工作台、工厂结算、物流、财务流水、数据分析、系统管理全功能管理页
- **移动端**（`/m/`，Vant）：基础信息只读浏览 + 订单/跟单/工厂结算完整操作 + 物流/财务列表，移动端跟拍照片上传

### 关键架构模式

- **统一响应**：所有 API 返回 `{code: 0, message, data}`，前端 axios 拦截器统一解包；401 时非登录页跳登录、登录页弹居中错误提示；token 存 sessionStorage
- **`common/` 通用库**：`BaseModelViewSet`（统一 CRUD 包装）、`response`、`permissions`（RolePermission/AdminWriteOthersReadOnly）、统一异常处理、分页
- **TDD 开发流程**：每任务先写失败测试 → 实现 → 验证 → 独立 commit

## 目录结构

```
├── backend/                      # Django 项目
│   ├── apps/                     # 9 个业务 app（见上表）
│   ├── common/                   # 通用库（ViewSet 包装/响应/权限/异常/分页）
│   ├── xb_project/               # 项目配置（settings 按环境分包）
│   ├── requirements/             # 依赖清单（dev.txt）
│   └── media/                    # 跟单照片上传目录
├── frontend/                     # Vue3 项目
│   └── src/
│       ├── views/                # PC 端页面（按业务域分目录）+ m/ 移动端页面
│       ├── api/                  # axios 实例与各业务 API 封装
│       ├── stores/               # Pinia（user：token/角色）
│       ├── router/               # 路由（MainLayout + MobileLayout）
│       └── tests/                # Vitest 测试（@vitest-environment node）
├── docs/superpowers/
│   ├── specs/                    # 设计文档
│   └── plans/                    # 实现计划
└── xbb印刷品定制数字化管理系统-规划文档.md   # 系统级规划（9 模块/技术栈/部署/报价复核）
```

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
cd backend && python -m pytest -v        # 163 passed
cd frontend && npx vitest run --test-timeout=30000   # 15 个测试全绿（ARM64 需加长超时）
npm run build                            # 构建（vue-tsc 类型检查 + vite build）
```

## 当前状态

全部 9 个模块开发完成：后端 163 个测试全绿、前端 15 个测试全绿、`npm run build` 通过。开发用 SQLite（ARM64 无原生 MySQL），生产部署计划用 MySQL 8 + Windows 绿色安装包（待部署阶段）。

近期 UI/UX 增强：

- **浅色专业企业风全局主题**：Element Plus / Vant 设计令牌统一换肤（深蓝主色、8px 圆角、柔阴影，表格/卡片/按钮/菜单统一）
- **登录体验优化**：登录失败弹居中 toast；token 改用 `sessionStorage`（关标签页/新标签页需重新登录）
- **列表多选/全选 + 批量删除**：类目/产品/工厂/物流服务商/客户/订单/工厂结算/物流/用户 9 个列表支持多选与批量删除（后端 `BaseModelViewSet` 新增 `bulk-delete`，逐个做对象级权限校验）
- **客户业务员指派限制**：客户仅能被指派给 **salesman 角色且非 admin** 的业务员（前端下拉过滤 + 后端校验，防止把客户派给管理员/跟单/财务）

## 分支策略

- `dev`：日常开发
- `test`：测试验证
- `main`：稳定发布版本
- 每个模块开发时从 `dev` 拉出 `feature/<模块名>` 子分支，完成后合并回 `dev`
