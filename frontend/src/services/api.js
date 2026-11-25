import router from '../router'
import { useAuthStore } from '../stores/auth'

/**
 * Centralized fetch client wrapper for Liquidio API.
 * Injects Authorization Bearer header automatically.
 * On any 401 response: immediately clears auth state and redirects to /login.
 */
export async function apiFetch(endpoint, options = {}) {
  const authStore = useAuthStore()

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  }

  if (authStore.token) {
    headers['Authorization'] = `Bearer ${authStore.token}`
  }

  const response = await fetch(endpoint, {
    ...options,
    headers
  })

  // Global 401 interceptor: clear credentials and redirect to login
  if (response.status === 401) {
    authStore.logout()
    if (router.currentRoute.value.path !== '/login') {
      router.push({
        path: '/login',
        query: { redirect: router.currentRoute.value.fullPath }
      })
    }
  }

  return response
}
