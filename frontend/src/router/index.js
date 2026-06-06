import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '工作台', icon: 'Odometer' }
      },
      {
        path: 'procurement',
        name: 'Procurement',
        component: () => import('@/views/Procurement.vue'),
        meta: { title: '采购申请', icon: 'Document', roles: ['admin', 'procurement', 'manager'] }
      },
      {
        path: 'budget',
        name: 'Budget',
        component: () => import('@/views/Budget.vue'),
        meta: { title: '预算审批看板', icon: 'Wallet', roles: ['admin', 'manager', 'procurement'] }
      },
      {
        path: 'tender',
        name: 'Tender',
        component: () => import('@/views/Tender.vue'),
        meta: { title: '招标项目', icon: 'Promotion', roles: ['admin', 'procurement', 'manager', 'expert', 'supplier'] }
      },
      {
        path: 'tender/:id',
        name: 'TenderDetail',
        component: () => import('@/views/TenderDetail.vue'),
        meta: { title: '招标详情', hide: true }
      },
      {
        path: 'bid',
        name: 'Bid',
        component: () => import('@/views/Bid.vue'),
        meta: { title: '投标管理', icon: 'Tickets', roles: ['admin', 'procurement', 'supplier'] }
      },
      {
        path: 'expert',
        name: 'Expert',
        component: () => import('@/views/Expert.vue'),
        meta: { title: '专家分配', icon: 'UserFilled', roles: ['admin', 'procurement'] }
      },
      {
        path: 'review',
        name: 'Review',
        component: () => import('@/views/Review.vue'),
        meta: { title: '评审打分', icon: 'EditPen', roles: ['admin', 'procurement', 'expert', 'manager'] }
      },
      {
        path: 'award',
        name: 'Award',
        component: () => import('@/views/Award.vue'),
        meta: { title: '中标通知', icon: 'Medal', roles: ['admin', 'procurement', 'manager', 'supplier'] }
      },
      {
        path: 'performance',
        name: 'Performance',
        component: () => import('@/views/Performance.vue'),
        meta: { title: '履约监控看板', icon: 'Monitor', roles: ['admin', 'procurement', 'manager'] }
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/views/Statistics.vue'),
        meta: { title: '周统计报告', icon: 'DataAnalysis', roles: ['admin', 'procurement', 'manager'] }
      },
      {
        path: 'search',
        name: 'Search',
        component: () => import('@/views/Search.vue'),
        meta: { title: '全网检索', icon: 'Search', roles: ['admin', 'procurement', 'manager'] }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue'),
        meta: { title: '操作日志', icon: 'Notebook', roles: ['admin', 'manager'] }
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 招投标管理系统` : '招投标管理系统'
  const userStore = useUserStore()

  if (to.meta.public) {
    next()
    return
  }

  if (!userStore.isLogin) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.roles && !to.meta.roles.includes(userStore.role) && userStore.role !== 'admin') {
    next('/dashboard')
    return
  }

  next()
})

export default router
