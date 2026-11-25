import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import ProjectUserView from '../views/ProjectUserView.vue'
import BudgetConfigView from '../views/BudgetConfigView.vue'
import ExpenseEntryView from '../views/ExpenseEntryView.vue'
import BudgetTrackingDashboard from '../views/BudgetTrackingDashboard.vue'
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
    component: BudgetTrackingDashboard,
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
