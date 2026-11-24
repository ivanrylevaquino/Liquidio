import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('liquidio_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('liquidio_user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || null)

  function getHomeRoute() {
    if (!user.value) return '/login'
    switch (user.value.role) {
      case 'ADMIN':
        return '/admin'
      case 'ENCODER':
        return '/expenses'
      case 'APPROVER':
        return '/dashboard'
      default:
        return '/dashboard'
    }
  }

  async function login(username, password) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })

    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed')
    }

    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('liquidio_token', data.access_token)
    localStorage.setItem('liquidio_user', JSON.stringify(data.user))
    return data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('liquidio_token')
    localStorage.removeItem('liquidio_user')
  }

  return {
    token,
    user,
    isAuthenticated,
    userRole,
    getHomeRoute,
    login,
    logout
  }
})
