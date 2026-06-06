<template>
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { connectWebSocket, disconnectWebSocket } from '@/utils/websocket'

const userStore = useUserStore()

onMounted(() => {
  if (userStore.isLogin) {
    connectWebSocket()
  }
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>
