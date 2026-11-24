<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

async function handleLogin() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    await authStore.login(username.value.trim(), password.value)
    // Redirect based on role per business rules:
    // Admin -> Budget/Project setup (/admin)
    // Encoder -> Manual expense recording (/expenses)
    // Approver -> Budget monitoring dashboard (/dashboard)
    const targetRoute = authStore.getHomeRoute()
    router.push(targetRoute)
  } catch (err) {
    errorMessage.value = err.message || 'Authentication failed. Please verify credentials.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-header">
        <div class="badge-logo">DOST &times; CIT-U</div>
        <h1 class="system-title">Liquidio</h1>
        <p class="system-tagline">Expense Classification &amp; Liquidation Reporting</p>
      </div>

      <div v-if="errorMessage" class="error-banner">
        <span class="error-icon">&#9888;</span>
        <span>{{ errorMessage }}</span>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            placeholder="e.g. admin or encoder1"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            placeholder="Enter your password"
            :disabled="isLoading"
          />
        </div>

        <button type="submit" class="btn-submit" :disabled="isLoading">
          <span v-if="isLoading">Signing in...</span>
          <span v-else>Sign In</span>
        </button>
      </form>

      <div class="role-hint">
        <strong>Role Access Hint:</strong>
        <p>&bull; <b>ADMIN</b>: Project setup &amp; approved Line-Item Budgets</p>
        <p>&bull; <b>ENCODER</b>: Manual expense recording &amp; verification</p>
        <p>&bull; <b>APPROVER</b>: Budget-vs-actual monitoring dashboard</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 120px);
  padding: 1rem;
}
.login-card {
  width: 100%;
  max-width: 420px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 2.25rem 2rem;
}
.login-header {
  text-align: center;
  margin-bottom: 1.75rem;
}
.badge-logo {
  display: inline-block;
  background: #fde047;
  color: #800000;
  font-weight: 800;
  font-size: 0.8rem;
  padding: 0.25rem 0.65rem;
  border-radius: 20px;
  letter-spacing: 0.5px;
  margin-bottom: 0.5rem;
}
.system-title {
  color: #800000;
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin: 0;
}
.system-tagline {
  color: #64748b;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}
.error-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}
.error-icon {
  font-weight: bold;
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
}
.form-group input {
  padding: 0.65rem 0.85rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.form-group input:focus {
  border-color: #800000;
  box-shadow: 0 0 0 3px rgba(128, 0, 0, 0.12);
}
.btn-submit {
  background-color: #800000;
  color: #ffffff;
  border: none;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s;
  margin-top: 0.5rem;
}
.btn-submit:hover:not(:disabled) {
  background-color: #990000;
}
.btn-submit:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
.role-hint {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px dashed #cbd5e1;
  font-size: 0.8rem;
  color: #475569;
}
.role-hint strong {
  display: block;
  margin-bottom: 0.35rem;
  color: #1e293b;
}
.role-hint p {
  margin: 0.2rem 0;
}
</style>
