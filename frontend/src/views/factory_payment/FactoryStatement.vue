<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listPayments, getStatement } from '../../api/factoryPayment'
import { listFactories } from '../../api/basicInfo'

function statusTagType(s: string) {
  if (s === '已结') return 'success'
  if (s === '部分结') return 'warning'
  return 'danger'
}

function fmtMoney(v: any) {
  if (v == null || v === '') return '—'
  return Number(v).toFixed(2)
}

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const summary = ref({ total_amount: '0', total_paid: '0', total_unpaid: '0', count: 0 })

const factoryFilter = ref<number | null>(null)
const dateRange = ref<[string, string] | null>(null)
const factories = ref<any[]>([])

async function load() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      factory: factoryFilter.value ?? undefined,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
    }
    const [listResp, stmtResp]: any[] = await Promise.all([
      listPayments(params),
      getStatement({
        factory: factoryFilter.value ?? undefined,
        start_date: dateRange.value?.[0],
        end_date: dateRange.value?.[1],
      }),
    ])
    rows.value = listResp.data.results
    total.value = listResp.data.count
    summary.value = stmtResp.data
  } finally {
    loading.value = false
  }
}

async function loadFactories() {
  const resp: any = await listFactories({ page: 1, page_size: 200 })
  factories.value = resp.data.results
}

function query() {
  page.value = 1
  load()
}

onMounted(() => { loadFactories(); load() })
</script>

<template>
  <div class="factory-statement">
    <el-card shadow="never">
      <div class="toolbar">
        <el-select v-model="factoryFilter" clearable filterable placeholder="工厂" style="width: 200px" @change="query">
          <el-option v-for="f in factories" :key="f.id" :label="f.name" :value="f.id" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px"
          @change="query"
        />
        <el-button type="primary" @click="query">查询</el-button>
      </div>

      <div class="summary-row">
        <div class="summary-card">
          <div class="summary-label">应付总额(CNY)</div>
          <div class="summary-value">{{ fmtMoney(summary.total_amount) }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">已付总额(CNY)</div>
          <div class="summary-value paid">{{ fmtMoney(summary.total_paid) }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">未付总额(CNY)</div>
          <div class="summary-value unpaid">{{ fmtMoney(summary.total_unpaid) }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">结算单数</div>
          <div class="summary-value">{{ summary.count ?? 0 }}</div>
        </div>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column prop="order_no" label="订单号" min-width="150" show-overflow-tooltip />
        <el-table-column prop="product_no" label="产品编号" width="120" show-overflow-tooltip />
        <el-table-column prop="factory_name" label="工厂" min-width="140" show-overflow-tooltip />
        <el-table-column label="应付(CNY)" width="120" align="right">
          <template #default="{ row }">{{ fmtMoney(row.amount_cny) }}</template>
        </el-table-column>
        <el-table-column label="已付(CNY)" width="120" align="right">
          <template #default="{ row }">{{ fmtMoney(row.paid_amount) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ row.created_at || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <router-link :to="`/factory-payment/${row.id}`" class="action-link">详情</router-link>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pager"
        @current-change="load"
        @size-change="query"
      />
    </el-card>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.summary-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.summary-card {
  flex: 1;
  min-width: 160px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  background: var(--el-fill-color-light);
}
.summary-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}
.summary-value {
  font-size: 22px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.summary-value.paid {
  color: var(--el-color-success);
}
.summary-value.unpaid {
  color: var(--el-color-danger);
}
.pager {
  margin-top: 12px;
  justify-content: flex-end;
}
.action-link {
  color: var(--el-color-primary);
  text-decoration: none;
  font-size: 13px;
}
.action-link:hover {
  text-decoration: underline;
}
</style>
