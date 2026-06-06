<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-left">
        <div class="brand">
          <el-icon size="48" color="#38bdf8"><Tickets /></el-icon>
          <h1>企业级招投标<br/>全流程自动化管理系统</h1>
          <p>采购申请 · 预算审批 · 招标发布 · 专家评审 · 中标通知 · 履约监控</p>
        </div>
        <div class="features">
          <div v-for="f in features" :key="f.name" class="feature">
            <el-icon color="#38bdf8">{{ f.icon }}</el-icon>
            <span>{{ f.name }}</span>
          </div>
        </div>
      </div>

      <div class="login-right">
        <h2>欢迎登录</h2>
        <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="handleLogin">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" size="large" prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" size="large" prefix-icon="Lock" show-password />
          </el-form-item>
          <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">登 录</el-button>
        </el-form>

        <el-divider content-position="center">演示账号</el-divider>
        <div class="demo-accounts">
          <div v-for="acc in demoAccounts" :key="acc.role" class="demo-acc" @click="fillAccount(acc)">
            <strong>{{ acc.roleName }}</strong>
            <span>{{ acc.username }} / {{ acc.password }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { connectWebSocket } from '@/utils/websocket'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const features = [
  { icon: 'Document', name: '智能提取需求' },
  { icon: 'Wallet', name: '自动预算校验' },
  { icon: 'Promotion', name: '模板匹配发布' },
  { icon: 'Lock', name: '投标加密解密' },
  { icon: 'UserFilled', name: '专家回避分配' },
  { icon: 'DataAnalysis', name: '自动评分汇总' },
  { icon: 'Medal', name: '电子合同通知' },
  { icon: 'Monitor', name: '履约监控预警' }
]

const demoAccounts = [
  { role: 'admin', roleName: '系统管理员', username: 'admin', password: 'admin123' },
  { role: 'procurement', roleName: '采购员', username: 'buyer01', password: 'buyer123' },
  { role: 'manager', roleName: '部门经理', username: 'manager01', password: 'manager123' },
  { role: 'expert', roleName: '评审专家', username: 'expert01', password: 'expert123' },
  { role: 'supplier', roleName: '供应商', username: 'supplier01', password: 'supplier123' }
]

function fillAccount(acc) {
  form.username = acc.username
  form.password = acc.password
}

async function handleLogin() {
  if (!form.username || !form.password) return
  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    connectWebSocket()
    router.push(route.query.redirect || '/dashboard')
  } catch (e) {}
  finally { loading.value = false }
}

onMounted(() => {
  if (userStore.isLogin) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
.login-container { height: 100vh; background: linear-gradient(135deg, #1e3a8a 0%, #0e7490 50%, #1e40af 100%); display: flex; align-items: center; justify-content: center; padding: 20px; }
.login-box { width: 960px; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 25px 60px rgba(0,0,0,0.3); display: flex; }
.login-left { width: 55%; padding: 48px 40px; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; }
.brand h1 { font-size: 26px; margin: 16px 0 8px; line-height: 1.4; }
.brand p { color: #94a3b8; font-size: 14px; }
.features { margin-top: 32px; display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.feature { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #cbd5e1; }
.login-right { width: 45%; padding: 48px 40px; }
.login-right h2 { font-size: 22px; margin: 0 0 28px; color: #1e293b; }
.login-btn { width: 100%; margin-top: 8px; height: 44px; font-size: 16px; }
.demo-accounts { display: flex; flex-wrap: wrap; gap: 8px; }
.demo-acc { padding: 8px 12px; background: #f1f5f9; border-radius: 8px; cursor: pointer; flex: 1; min-width: 45%; transition: all 0.2s; }
.demo-acc:hover { background: #e0f2fe; }
.demo-acc strong { display: block; font-size: 13px; color: #1e40af; }
.demo-acc span { font-size: 11px; color: #64748b; }
</style>
