import { defineStore } from 'pinia'
import api from '@/utils/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('bidding_token') || '',
    user: JSON.parse(localStorage.getItem('bidding_user') || 'null')
  }),
  getters: {
    isLogin: (state) => !!state.token,
    role: (state) => state.user?.role || '',
    roleName: (state) => state.user?.role_name || '',
    username: (state) => state.user?.real_name || state.user?.username || ''
  },
  actions: {
    async login(username, password) {
      const res = await api.post('/auth/login', { username, password })
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('bidding_token', res.data.token)
      localStorage.setItem('bidding_user', JSON.stringify(res.data.user))
      return res.data
    },
    async fetchProfile() {
      const res = await api.get('/auth/profile')
      this.user = res.data
      localStorage.setItem('bidding_user', JSON.stringify(res.data))
      return res.data
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('bidding_token')
      localStorage.removeItem('bidding_user')
    },
    hasRole(...roles) {
      if (!this.user) return false
      if (this.user.role === 'admin') return true
      return roles.includes(this.user.role)
    }
  }
})
