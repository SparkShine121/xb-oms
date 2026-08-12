<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listProducts, listFactories, listCustomers } from '../../api/basicInfo'

// 概览统计：只读浏览，取 count 即可（page_size=1 减少传输）
const counts = ref<Record<string, number>>({ products: 0, factories: 0, customers: 0 })

const entries = [
  { key: 'products', name: '产品库', icon: 'goods-collect-o', to: '/m/products' },
  { key: 'factories', name: '工厂库', icon: 'shop-o', to: '/m/factories' },
  { key: 'customers', name: '客户', icon: 'contact-o', to: '/m/customers' },
]

async function loadCounts() {
  try {
    const [p, f, c]: any[] = await Promise.all([
      listProducts({ page: 1, page_size: 1 }),
      listFactories({ page: 1, page_size: 1 }),
      listCustomers({ page: 1, page_size: 1 }),
    ])
    counts.value = { products: p.data.count, factories: f.data.count, customers: c.data.count }
  } catch {
    // 只读浏览：统计失败不阻塞首页展示（错误提示由全局拦截器处理）
  }
}

onMounted(loadCounts)
</script>

<template>
  <div class="mobile-home">
    <van-nav-bar title="辛巴印刷品定制" />
    <div class="banner">
      <p class="banner-title">基础信息库</p>
      <p class="banner-sub">产品 / 工厂 / 客户 只读浏览</p>
    </div>
    <van-grid :column-num="3" :border="false" class="entries">
      <van-grid-item v-for="e in entries" :key="e.key" :to="e.to">
        <van-icon :name="e.icon" size="28" />
        <div class="entry-name">{{ e.name }}</div>
        <div class="entry-count">{{ counts[e.key] }} 条</div>
      </van-grid-item>
    </van-grid>
  </div>
</template>

<style scoped>
.banner {
  margin: 12px 16px;
  padding: 20px 16px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #1989fa, #4b8ff5);
}
.banner-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.banner-sub {
  margin: 6px 0 0;
  font-size: 13px;
  opacity: 0.85;
}
.entries {
  margin: 0 16px;
  border-radius: 12px;
  overflow: hidden;
}
.entry-name {
  margin-top: 6px;
  font-size: 14px;
  color: #323233;
}
.entry-count {
  margin-top: 2px;
  font-size: 12px;
  color: #969799;
}
</style>
