<template>
  <div class="mobile-layout">
    <div class="mobile-content">
      <router-view />
    </div>
    <van-tabbar route>
      <!-- 用 name 匹配避免父路由 /m 使首页 tab 在子页面误高亮 -->
      <van-tabbar-item replace :to="{ name: 'MobileHome' }" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item replace :to="{ name: 'MProductList' }" icon="goods-collect-o">产品</van-tabbar-item>
      <van-tabbar-item replace :to="{ name: 'MFactoryList' }" icon="shop-o">工厂</van-tabbar-item>
      <van-tabbar-item replace :to="{ name: 'MCustomerList' }" icon="contact-o">客户</van-tabbar-item>
      <van-tabbar-item replace :to="{ name: 'MOrderList' }" icon="bill-o">订单</van-tabbar-item>
      <van-tabbar-item replace :to="{ name: 'MTrackingWorkbench' }" icon="todo-list-o">跟单</van-tabbar-item>
      <van-tabbar-item replace :to="{ name: 'MFactoryPayment' }" icon="balance-list-o">工厂结算</van-tabbar-item>
      <van-tabbar-item replace :to="{ name: 'MLogisticsShipmentList' }" icon="logistics">物流</van-tabbar-item>
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
