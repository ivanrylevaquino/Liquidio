import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: () => {
      const auth = useAuthStore()
      return auth.isAuthenticated ? auth.getHomeRoute() : '/login'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { guestOnly: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: {
      template: `
        <div style="background: white; padding: 2rem; border-radius: 8px; border: 1px solid #e2e8f0;">
          <h2 style="color: #800000; margin-bottom: 0.5rem;">Project &amp; Budget Setup (ADMIN)</h2>
          <p style="color: #64748b;">Admin module endpoints and UI will be connected in Steps 3 and 4.</p>
        </div>
      `
    },
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/expenses',
    name: 'Expenses',
    component: {
      template: `
        <div style="background: white; padding: 2rem; border-radius: 8px; border: 1px solid #e2e8f0;">
          <h2 style="color: #800000; margin-bottom: 0.5rem;">Manual Expense Entry (ENCODER)</h2>
          <p style="color: #64748b;">Manual expense encoding (UC-1.2) will be connected in Step 5.</p>
        </div>
      `
    },
    meta: { requiresAuth: true, roles: ['ENCODER', 'ADMIN'] }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: {
      template: `
        <div style="background: white; padding: 2rem; border-radius: 8px; border: 1px solid #e2e8f0;">
          <h2 style="color: #800000; margin-bottom: 0.5rem;">Budget Tracking Dashboard</h2>
          <p style="color: #64748b;">Budget vs. Actual monitoring (UC-1.3) will be connected in Step 6.</p>
        </div>
      `
    },
    meta: { requiresAuth: true, roles: ['ADMIN', 'ENCODER', 'APPROVER'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Global RBAC navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return next(authStore.getHomeRoute())
  }

  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }

    if (to.meta.roles && !to.meta.roles.includes(authStore.userRole)) {
      // Forbidden: redirect user to their authorized home route
      return next(authStore.getHomeRoute())
    }
  }

  next()
})

export default router
