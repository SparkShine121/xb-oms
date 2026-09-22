<template>
  <div class="search-toolbar">
    <div class="st-filters"><slot name="filters" /></div>
    <div class="st-actions"><slot name="actions" /></div>
  </div>
</template>

<style scoped>
.search-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.st-filters,
.st-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.st-actions {
  margin-left: auto;
}
/* el-upload 触发按钮与相邻按钮垂直对齐（等价于原全局 .toolbar 规则，见错题集 2026-09-07） */
.st-actions :deep(.el-upload) {
  display: inline-flex;
  align-items: center;
  height: 32px;
  margin: 0;
}
.st-actions :deep(.el-upload .el-button) {
  margin: 0;
}
</style>
