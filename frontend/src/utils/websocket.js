import { io } from 'socket.io-client'
import { ElNotification } from 'element-plus'

const socket = io({ autoConnect: false })

const notifications = []

export function connectWebSocket() {
  if (!socket.connected) {
    socket.connect()
  }
  return socket
}

export function disconnectWebSocket() {
  if (socket.connected) {
    socket.disconnect()
  }
}

socket.on('connect', () => {
  console.log('[WebSocket] 已连接')
})

socket.on('project_notification', (data) => {
  console.log('[WebSocket] 收到消息:', data)
  notifications.unshift({ ...data, read: false, time: data.time || new Date().toLocaleString() })
  if (notifications.length > 50) notifications.pop()

  const typeMap = {
    'operation_log': { type: 'info', icon: '📝' },
    'weekly_report': { type: 'success', icon: '📊' },
    'performance_warning': { type: 'warning', icon: '⚠️' },
    'test': { type: 'info', icon: '🔔' },
    'group_chat': { type: 'info', icon: '💬' },
  }
  const cfg = typeMap[data.type] || { type: 'info', icon: '📢' }

  ElNotification({
    title: `${cfg.icon} ${data.title || '系统通知'}`,
    message: data.content || data.detail || '您有新的消息',
    type: cfg.type,
    duration: 5000,
    position: 'top-right'
  })
})

socket.on('disconnect', () => {
  console.log('[WebSocket] 已断开')
})

export function getNotifications() {
  return notifications
}

export function markAllRead() {
  notifications.forEach(n => n.read = true)
}

export function getUnreadCount() {
  return notifications.filter(n => !n.read).length
}

export function useSocket() {
  return {
    socket,
    onLog(callback) {
      socket.on('project_notification', (data) => {
        if (data.type === 'operation_log') {
          callback({
            id: Date.now(),
            op_type: data.op_type || 'update',
            module: data.module || 'system',
            operator: data.operator || 'system',
            record_id: data.record_id || '',
            detail: data.content || data.detail || '',
            ip_address: '127.0.0.1',
            created_at: data.time || new Date().toLocaleString()
          })
        }
      })
    },
    connect: connectWebSocket,
    disconnect: disconnectWebSocket
  }
}

export default socket
