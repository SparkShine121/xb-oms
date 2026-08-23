# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 开发流程规则（用户定义，必须遵守）

* 在**需求了解**阶段以及有任何**需要向我确认**的问题时，**必须**使用**grill-me**这个skill向我发问，直到有95%的信心能够确认需求后才能动工
* **了解需求**后，在生成代码的**全过程**中，**必须**根据**superpowers**这个skill中的规范开发项目
* 在梳理完所有功能后，**必须**将功能拆分为多个模块进行开发
* 在每个模块开发完成后，**必须**调用**neat-freak**这个skill进行代码整理
* 在每次对代码进行维护后，**必须**调用**neat-freak**这个skill进行代码整理
* 每次完成任务后都检查一遍产生的中间文件及其所在路径并向我汇报，由我决定是否需要删除这些文件
* **分支策略**：日常开发默认在 **`dev`** 分支进行；`test` 分支用于测试验证；`main` 分支保持稳定发布版本。每个模块开发时从 `dev` 拉出 `feature/<模块名>` 子分支，完成后合并回 `dev`

## 技术栈

- **后端**：Python 3.13 + Django 5.1 + DRF + SQLite（开发）/ MySQL 8（生产）
- **前端**：Vue 3 + Vite + TypeScript + Element Plus（PC/平板）+ Vant（手机）
- **认证**：JWT（djangorestframework-simplejwt）；4 角色：admin / salesman / tracker / finance
- **环境**：Windows 11 ARM64。Python 在 `D:\Pad Windows Data\Python313-arm64\`，Node 在 `D:\Pad Windows Data\nodejs\node-v22.23.2-win-arm64\`（用前 `export PATH="/d/Pad Windows Data/nodejs/node-v22.23.2-win-arm64:$PATH"`）

## 常用命令

### 后端（端口 8000）
```bash
cd backend
python -m pip install -r requirements/dev.txt   # 装依赖（不裸装单包）
python manage.py migrate                           # 迁移
python manage.py create_groups                      # 创建 4 个角色 Group（admin/salesman/tracker/finance）
python manage.py runserver                         # 启动开发服务器
python manage.py check                             # 系统检查
python -m pytest -v                                # 全量测试
python -m pytest apps/orders/tests/test_api.py::test_name -v  # 单测试
```

### 前端（端口 5173）
```bash
export PATH="/d/Pad Windows Data/nodejs/node-v22.23.2-win-arm64:$PATH"  # 挂载 Node（每次新 shell）
cd frontend
npm install --registry=https://registry.npmmirror.com   # 装依赖（中国镜像加速）
npm run dev                                               # 启动开发服务器（Vite 代理 /api → 8000）
npx vitest run --test-timeout=30000                      # 全量测试（ARM 需加长超时）
npx vitest run src/tests/orders.test.ts --test-timeout=30000  # 单测试
npm run build                                             # 构建（vue-tsc 类型检查 + vite build）
```

## 架构

### 后端（`backend/`）

Django monorepo，按业务域分 app：

- **`apps/basic_info/`**：基础信息（Category/Product/Factory/LogisticsProvider/Customer）+ Excel 批量导入（importers.py）
- **`apps/orders/`**：订单（Order/OrderItem/ExchangeRate）+ 订单 Excel 导入（importers.py，阿里小满模板）+ 毛利计算（`calc_order_profit`）+ OrderPermission（数据范围：salesman 自己客户/tracker 派给自己）
- **`apps/tracking/`**：跟单（TrackingLog/TrackingPhoto）+ 8 节点状态机（`state_machine.py`：接单→排产→生产中→质检→发货→签收→结算→回款）+ TrackingViewSet（advance/reject/timeline/my）+ TrackingPermission + MEDIA 照片上传（Pillow verify 校验 + transaction.atomic）
- **`apps/factory_payment/`**：工厂结算（FactoryPayment OneToOne→OrderItem + FactoryPaymentRecord 多次付款）+ status 自动算（未结/部分结/已结）+ 一键生成（批量创建结算单）+ 工厂对账单 + FactoryPaymentPermission
- **`apps/logistics/`**：物流管理（Logistics FK→Order 多行 + seq 自动递增 + 两段物流关联 LogisticsProvider）+ LogisticsPermission
- **`apps/finance/`**：轻财务（PaymentIn 回款模型 + 收支流水四源聚合 API + openpyxl 导出 Excel）
- **`apps/analytics/`**：数据分析（4 个聚合 API：销售结算表/工厂账单汇总/跟单信息汇总/管理人员报表，ECharts 前端渲染）
- **`apps/system_mgmt/`**：系统管理（ApprovalRequest 审批流 + OperationLog 操作日志 middleware JWT 解析 + BackupRecord 备份恢复审批后自动+滚动保留1000份）
- **`apps/accounts/`**：JWT 认证（login/me/logout）+ 用户管理 + `create_groups` 命令
- **`common/`**：通用库——`BaseModelViewSet`（统一 `{code,message,data}` CRUD 包装）、`response.py`（success_response/error_response）、`permissions.py`（RolePermission/AdminWriteOthersReadOnly）、`exceptions.py`（统一异常处理）、`pagination.py`

### 前端（`frontend/`）

Vue3 + Vite，按端分流：

- **PC/平板**（`/`）：Element Plus，`views/basic_info/`、`views/orders/`、`views/tracking/`、`views/factory_payment/`、`views/system/`
- **移动端**（`/m/`）：Vant，`views/m/`（基础信息只读 + 订单完整 + 跟单完整 + 工厂结算完整）
- **API 封装**：`src/api/{request,auth,basicInfo,orders,tracking,factoryPayment}.ts`——`request.ts` 是 axios 实例（baseURL=/api、Bearer 注入、401 跳转、非 401 全局 ElMessage.error、返回 res.data）
- **状态**：Pinia `stores/user.ts`（token/roles/username，localStorage 持久化）
- **路由**：`router/index.ts`，MainLayout（菜单）+ MobileLayout（tabbar），路由守卫登录校验
- **测试**：`src/tests/*.test.ts`（首行 `// @vitest-environment node` + `vi.mock('element-plus')` 避免 ARM jsdom 慢）

### 关键模式

- **统一响应**：所有 API 返回 `{code:0, message, data}`，前端 `request.ts` 拦截器返回 `res.data`（即 envelope），页面取 `resp.data.results`（列表）或 `resp.data`（详情）
- **权限双层**：`has_permission`（操作级）+ `has_object_permission`（对象级数据范围）；后端是安全防线，前端按角色显隐按钮是体验层
- **模块开发流程**：grilling 需求 → brainstorming 设计 → writing-plans 计划 → subagent-driven-development 逐任务 TDD（implementer/reviewer）→ neat-freak 收尾
- **TDD**：先写失败测试 → 验证失败 → 实现 → 验证通过 → 提交（每任务独立 commit）