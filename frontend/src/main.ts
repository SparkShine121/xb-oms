import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElMessage } from 'element-plus'
import { closeToast, setToastDefaultOptions } from 'vant'
import App from './App.vue'
import router from './router'
import './style.css'
// Vant 函数式 API 的样式需手动引入（VantResolver 只覆盖模板组件）
import 'vant/es/toast/style'
import 'vant/es/image-preview/style'

// Vant toast 默认时长统一为 3 秒（Element Plus 默认即 3000ms，无需设置）
setToastDefaultOptions({ duration: 3000 })

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

// 全局 toast 遮罩：出现任意 .el-message / .van-toast 时遮住页面，全部消失后移除。
// 点击遮罩立即关闭所有 toast；样式（居中、白底黑字）见 style.css。
const toastMask = document.createElement('div')
toastMask.className = 'global-toast-mask'
toastMask.addEventListener('click', () => {
  ElMessage.closeAll()
  closeToast()
})
const toastObserver = new MutationObserver(() => {
  const has = document.querySelector('.el-message, .van-toast') != null
  if (has && !toastMask.isConnected) document.body.appendChild(toastMask)
  if (!has && toastMask.isConnected) toastMask.remove()
})
toastObserver.observe(document.body, { childList: true, subtree: true })
