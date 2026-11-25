<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const currentUser = computed(() => authStore.user)

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="layout-container">
    <header class="app-header">
      <div class="header-inner">
        <div class="brand">
          <router-link to="/" class="brand-link">
            <span class="brand-title">Liquidio</span>
            <span class="brand-subtitle">DOST &times; CIT-U</span>
          </router-link>
        </div>

        <nav class="nav-links" v-if="currentUser">
          <router-link to="/projects" class="nav-item">Projects &amp; Users</router-link>
          <router-link to="/budgets" class="nav-item">Line-Item Budgets</router-link>
          <router-link to="/expenses" class="nav-item">Encode Expense</router-link>
          <router-link to="/dashboard" class="nav-item">Dashboard</router-link>

          <div class="user-badge">
            <span class="user-name">{{ currentUser.full_name }}</span>
            <button @click="handleLogout" class="btn-logout" title="Sign out">Logout</button>
          </div>
        </nav>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-header {
  background-color: #800000;
  color: #ffffff;
  padding: 0.75rem 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}
.brand-link {
  text-decoration: none;
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}
.brand-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.5px;
}
.brand-subtitle {
  font-size: 0.85rem;
  color: #fde047;
  font-weight: 600;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.nav-item {
  color: #f1f5f9;
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  padding: 0.35rem 0.65rem;
  border-radius: 4px;
  transition: background 0.15s;
}
.nav-item:hover, .nav-item.router-link-active {
  background-color: rgba(255,255,255,0.15);
}
.user-badge {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(0,0,0,0.25);
  padding: 0.3rem 0.75rem;
  border-radius: 6px;
  margin-left: 0.5rem;
}
.user-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #f8fafc;
}
.btn-logout {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.4);
  color: #ffffff;
  border-radius: 4px;
  padding: 0.2rem 0.5rem;
  font-size: 0.75rem;
  cursor: pointer;
}
.btn-logout:hover {
  background: rgba(255,255,255,0.2);
}
.main-content {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem;
}
@media (max-width: 640px) {
  .header-inner {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
