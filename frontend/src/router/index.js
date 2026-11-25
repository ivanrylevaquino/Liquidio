import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import ProjectUserView from '../views/ProjectUserView.vue'
import BudgetConfigView from '../views/BudgetConfigView.vue'
import ExpenseEntryView from '../views/ExpenseEntryView.vue'
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
    path: '/projects',
    name: 'Projects',
    component: ProjectUserView,
    meta: { requiresAuth: true }
  },
  {
    path: '/budgets',
    name: 'Budgets',
    component: BudgetConfigView,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:id/budget',
    name: 'ProjectBudget',
    component: BudgetConfigView,
    meta: { requiresAuth: true }
  },
  {
    path: '/expenses',
    name: 'Expenses',
    component: ExpenseEntryView,
    meta: { requiresAuth: true }
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
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard ensuring only authenticated active users access protected routes
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return next(authStore.getHomeRoute())
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  next()
})

export default router
