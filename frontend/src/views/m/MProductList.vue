<script setup lang="ts">
import { ref } from 'vue'
import { listProducts } from '../../api/basicInfo'

const rows = ref<any[]>([])
const loading = ref(false)
const finished = ref(false)
const page = ref(1)
const pageSize = 20

async function onLoad() {
  try {
    const resp: any = await listProducts({ page: page.value, page_size: pageSize })
    const data = resp.data
    rows.value = rows.value.concat(data.results)
    if (data.next) page.value += 1
    else finished.value = true
  } catch {
    // 加载失败停止自动重试（错误提示由全局拦截器处理）
    finished.value = true
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="m-list">
    <van-nav-bar title="产品库" />
    <van-list
      v-model:loading="loading"
      :finished="finished"
      :finished-text="rows.length ? '没有更多了' : ''"
      @load="onLoad"
    >
      <van-cell
        v-for="item in rows"
        :key="item.id"
        :title="`${item.product_no} · ${item.name}`"
        :label="`型号：${item.model || '—'}　规格：${item.spec || '—'}`"
      />
    </van-list>
    <van-empty v-if="finished && !rows.length" description="暂无产品数据" />
  </div>
</template>
