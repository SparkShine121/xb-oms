<script setup lang="ts">
withDefaults(defineProps<{
  page: number
  pageSize: number
  total: number
  pageSizes?: number[]
}>(), {
  pageSizes: () => [10, 20, 50, 100],
})

const emit = defineEmits<{
  'update:page': [value: number]
  'update:pageSize': [value: number]
  change: []
}>()

function onCurrentChange(value: number) {
  emit('update:page', value)
  emit('change')
}

function onSizeChange(value: number) {
  emit('update:pageSize', value)
  emit('update:page', 1)
  emit('change')
}
</script>

<template>
  <el-pagination
    class="app-pagination"
    background
    :current-page="page"
    :page-size="pageSize"
    :total="total"
    :page-sizes="pageSizes"
    layout="total, sizes, prev, pager, next, jumper"
    @current-change="onCurrentChange"
    @size-change="onSizeChange"
  />
</template>

<style scoped>
.app-pagination {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
