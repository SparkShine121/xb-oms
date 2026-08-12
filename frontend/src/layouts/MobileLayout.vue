<template>
  <div class="mobile-layout">
    <div class="mobile-content">
      <router-view />
    </div>
    <van-tabbar route>
      <van-tabbar-item replace to="/m/home" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item replace to="/m/quote" icon="orders-o">报价</van-tabbar-item>
      <van-tabbar-item replace to="/m/me" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<style scoped>
.mobile-layout {
  min-height: 100vh;
  background: #f7f8fa;
}
.mobile-content {
  padding-bottom: 50px;
}
</style>
