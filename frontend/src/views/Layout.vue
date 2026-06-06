<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo">
        <el-icon size="28"><Tickets /></el-icon>
        <span v-if="!isCollapse" class="logo-text">招投标系统</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        router
        background-color="#1e293b"
        text-color="#cbd5e1"
        active-text-color="#38bdf8"
      >
        <el-menu-item v-for="r in menuRoutes" :key="r.path" :index="`/${r.path}`">
          <el-icon><component :is="r.meta.icon" /></el-icon>
          <template #title>{{ r.meta.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" size="20" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" /><Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="$route.meta.title">{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="msg-badge">
            <el-button type="primary" text @click="showMsgPanel = true">
              <el-icon><Bell /></el-icon>
              <span v-if="unreadCount > 0" class="unread">{{ unreadCount }}</span>
            </el-button>
          </el-badge>

          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="32" :style="{ backgroundColor: avatarColor }">
                {{ userStore.username?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="user-name">{{ userStore.username }}</span>
              <el-tag size="small" type="success" effect="plain">{{ userStore.roleName }}</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="showProfile = true">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <el-drawer v-model="showMsgPanel" title="📢 项目群消息通知" size="420px" direction="rtl">
      <div class="msg-list">
        <div v-if="msgs.length === 0" class="empty">
          <el-empty description="暂无消息" />
        </div>
        <div v-for="(m, i) in msgs" :key="i" class="msg-item" :class="{ unread: !m.read }">
          <div class="msg-header">
            <span class="msg-title">{{ m.title || m.operator || '系统通知' }}</span>
            <span class="msg-time">{{ m.time }}</span>
          </div>
          <div class="msg-content">{{ m.content || m.detail || '无详情' }}</div>
          <el-tag v-if="m.module" size="small" type="info" effect="plain">{{ m.module }}</el-tag>
        </div>
      </div>
    </el-drawer>

    <el-dialog v-model="showProfile" title="个人中心" width="420px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ userStore.user?.username }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ userStore.user?.real_name }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ userStore.roleName }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ userStore.user?.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机">{{ userStore.user?.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="最后登录">{{ userStore.user?.last_login || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getNotifications, getUnreadCount, markAllRead, connectWebSocket } from '@/utils/websocket'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isCollapse = ref(false)
const showMsgPanel = ref(false)
const showProfile = ref(false)
const msgs = ref([])
const unreadCount = ref(0)

const avatarColor = computed(() => {
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
  const idx = (userStore.user?.id || 0) % colors.length
  return colors[idx]
})

const menuRoutes = computed(() => {
  return router.options.routes
    .find(r => r.path === '/')?.children
    ?.filter(r => r.meta && !r.meta.hide && r.meta.icon && r.meta.roles)
    ?.filter(r => userStore.hasRole(...r.meta.roles)) || []
})

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

function refreshMsgs() {
  msgs.value = getNotifications()
  unreadCount.value = getUnreadCount()
}

watch(showMsgPanel, (v) => {
  if (v) {
    markAllRead()
    refreshMsgs()
  }
})

onMounted(() => {
  connectWebSocket()
  refreshMsgs()
  setInterval(refreshMsgs, 3000)
})
</script>

<style scoped>
.layout-container { height: 100vh; }
.aside { background: #1e293b; transition: width 0.3s; overflow: hidden; }
.logo { display: flex; align-items: center; gap: 10px; padding: 18px 16px; color: #38bdf8; font-weight: bold; font-size: 16px; border-bottom: 1px solid #334155; }
.logo-text { white-space: nowrap; }
.aside :deep(.el-menu) { border-right: none; }
.header { background: white; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; }
.header-left { display: flex; align-items: center; gap: 16px; }
.collapse-btn { cursor: pointer; color: #64748b; }
.header-right { display: flex; align-items: center; gap: 16px; }
.user-info { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.user-name { font-size: 14px; color: #334155; }
.main-content { background: #f1f5f9; padding: 20px; overflow: auto; }
.msg-item { padding: 12px; border-bottom: 1px solid #f1f5f9; }
.msg-item.unread { background: #eff6ff; }
.msg-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
.msg-title { font-weight: 600; color: #1e293b; font-size: 14px; }
.msg-time { color: #94a3b8; font-size: 12px; }
.msg-content { color: #475569; font-size: 13px; margin-bottom: 6px; }
.empty { padding: 40px 0; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.msg-badge :deep(.el-badge__content) { top: 4px; }
</style>
