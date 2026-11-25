<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { apiFetch } from '../services/api'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('projects') // 'projects' | 'users'
const projects = ref([])
const users = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// Project Form state
const showProjectModal = ref(false)
const projectForm = ref({
  project_code: '',
  title: '',
  funding_agency: 'DOST',
  start_date: '',
  end_date: '',
  total_dost_budget: '0.00',
  total_citu_budget: '0.00'
})

// User Form state
const showUserModal = ref(false)
const userForm = ref({
  username: '',
  full_name: '',
  password: '',
  email: ''
})

const activeUserCount = computed(() => users.value.filter(u => u.is_active).length)

async function fetchProjects() {
  try {
    const res = await apiFetch('/api/projects')
    if (res.ok) {
      projects.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to load projects', err)
  }
}

async function fetchUsers() {
  try {
    const res = await apiFetch('/api/users')
    if (res.ok) {
      users.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to load users', err)
  }
}

async function handleCreateProject() {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const res = await apiFetch('/api/projects', {
      method: 'POST',
      body: JSON.stringify(projectForm.value)
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to create project')
    }
    successMessage.value = `Project '${data.project_code}' created successfully.`
    showProjectModal.value = false
    projectForm.value = {
      project_code: '',
      title: '',
      funding_agency: 'DOST',
      start_date: '',
      end_date: '',
      total_dost_budget: '0.00',
      total_citu_budget: '0.00'
    }
    await fetchProjects()
  } catch (err) {
    errorMessage.value = err.message
  }
}

async function handleCreateUser() {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const res = await apiFetch('/api/users', {
      method: 'POST',
      body: JSON.stringify(userForm.value)
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to create user')
    }
    successMessage.value = `User '${data.username}' created successfully.`
    showUserModal.value = false
    userForm.value = { username: '', full_name: '', password: '', email: '' }
    await fetchUsers()
  } catch (err) {
    errorMessage.value = err.message
  }
}

async function handleDeactivateUser(user) {
  if (user.id === authStore.user?.id) {
    alert('Cannot deactivate your own account.')
    return
  }
  if (!confirm(`Are you sure you want to deactivate user '${user.username}'?`)) {
    return
  }
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const res = await apiFetch(`/api/users/${user.id}/deactivate`, {
      method: 'POST'
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to deactivate user')
    }
    successMessage.value = `User '${user.username}' has been deactivated.`
    await fetchUsers()
  } catch (err) {
    errorMessage.value = err.message
  }
}

function formatPHP(amount) {
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: 'PHP',
    minimumFractionDigits: 2
  }).format(amount)
}

function goToBudgetConfig(projectId) {
  router.push(`/projects/${projectId}/budget`)
}

onMounted(async () => {
  isLoading.value = true
  await Promise.all([fetchProjects(), fetchUsers()])
  isLoading.value = false
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Management Console</h1>
        <p class="page-subtitle">Configure research projects and institutional user accounts</p>
      </div>

      <div class="tab-controls">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'projects' }"
          @click="activeTab = 'projects'"
        >
          Projects ({{ projects.length }})
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'users' }"
          @click="activeTab = 'users'"
        >
          Users ({{ users.length }})
        </button>
      </div>
    </div>

    <!-- Alert Banners -->
    <div v-if="errorMessage" class="alert-banner alert-error">
      <span>&#9888; {{ errorMessage }}</span>
    </div>
    <div v-if="successMessage" class="alert-banner alert-success">
      <span>&#10004; {{ successMessage }}</span>
    </div>

    <!-- PROJECTS TAB -->
    <div v-if="activeTab === 'projects'" class="tab-content">
      <div class="section-actions">
        <h2>Research Projects</h2>
        <button @click="showProjectModal = !showProjectModal" class="btn-primary">
          {{ showProjectModal ? 'Cancel' : '+ New Project' }}
        </button>
      </div>

      <!-- New Project Form Card -->
      <div v-if="showProjectModal" class="form-card">
        <h3>Create New Project Profile</h3>
        <form @submit.prevent="handleCreateProject" class="grid-form">
          <div class="form-group">
            <label>Project Code *</label>
            <input v-model="projectForm.project_code" placeholder="e.g. DOST-CITU-2026-01" required />
          </div>
          <div class="form-group">
            <label>Funding Agency *</label>
            <input v-model="projectForm.funding_agency" placeholder="DOST" required />
          </div>
          <div class="form-group full-width">
            <label>Project Title *</label>
            <input v-model="projectForm.title" placeholder="Full research project title" required />
          </div>
          <div class="form-group">
            <label>Start Date *</label>
            <input type="date" v-model="projectForm.start_date" required />
          </div>
          <div class="form-group">
            <label>End Date *</label>
            <input type="date" v-model="projectForm.end_date" required />
          </div>
          <div class="form-group">
            <label>Approved DOST Budget (PHP) *</label>
            <input type="number" step="0.01" min="0" v-model="projectForm.total_dost_budget" required />
          </div>
          <div class="form-group">
            <label>CIT-U Counterpart Budget (PHP) *</label>
            <input type="number" step="0.01" min="0" v-model="projectForm.total_citu_budget" required />
          </div>
          <div class="full-width form-actions">
            <button type="submit" class="btn-primary">Save Project</button>
          </div>
        </form>
      </div>

      <!-- Project List Table -->
      <div class="card table-container">
        <table class="data-table" v-if="projects.length > 0">
          <thead>
            <tr>
              <th>Project Code</th>
              <th>Title</th>
              <th>Timeline</th>
              <th>DOST Budget</th>
              <th>CIT-U Budget</th>
              <th class="text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in projects" :key="p.id">
              <td><span class="code-badge">{{ p.project_code }}</span></td>
              <td class="font-bold">{{ p.title }}</td>
              <td class="text-sm text-muted">{{ p.start_date }} &rarr; {{ p.end_date }}</td>
              <td class="text-right">{{ formatPHP(p.total_dost_budget) }}</td>
              <td class="text-right">{{ formatPHP(p.total_citu_budget) }}</td>
              <td class="text-center">
                <button @click="goToBudgetConfig(p.id)" class="btn-lib" title="Configure Approved Line-Item Budget">
                  Setup LIB &rarr;
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">
          <p>No projects registered yet. Click <b>+ New Project</b> to register your first project profile.</p>
        </div>
      </div>
    </div>

    <!-- USERS TAB -->
    <div v-if="activeTab === 'users'" class="tab-content">
      <div class="section-actions">
        <h2>Institutional Accounts</h2>
        <button @click="showUserModal = !showUserModal" class="btn-primary">
          {{ showUserModal ? 'Cancel' : '+ New User' }}
        </button>
      </div>

      <!-- New User Form Card -->
      <div v-if="showUserModal" class="form-card">
        <h3>Create New User Account</h3>
        <p class="form-hint">All users share unified permissions. Minimum password length is 8 characters.</p>
        <form @submit.prevent="handleCreateUser" class="grid-form">
          <div class="form-group">
            <label>Username *</label>
            <input v-model="userForm.username" placeholder="e.g. jdelacruz" required minlength="3" />
          </div>
          <div class="form-group">
            <label>Full Name *</label>
            <input v-model="userForm.full_name" placeholder="e.g. Juan Dela Cruz" required />
          </div>
          <div class="form-group">
            <label>Password (min 8 chars) *</label>
            <input type="password" v-model="userForm.password" required minlength="8" />
          </div>
          <div class="form-group">
            <label>Email (optional)</label>
            <input type="email" v-model="userForm.email" placeholder="user@cit.edu" />
          </div>
          <div class="full-width form-actions">
            <button type="submit" class="btn-primary">Create User Account</button>
          </div>
        </form>
      </div>

      <!-- User List Table -->
      <div class="card table-container">
        <table class="data-table" v-if="users.length > 0">
          <thead>
            <tr>
              <th>Username</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="font-bold">{{ u.username }}</td>
              <td>{{ u.full_name }}</td>
              <td class="text-sm text-muted">{{ u.email || '—' }}</td>
              <td>
                <span class="status-badge" :class="u.is_active ? 'badge-active' : 'badge-inactive'">
                  {{ u.is_active ? 'Active' : 'Deactivated' }}
                </span>
              </td>
              <td>
                <button
                  v-if="u.is_active"
                  @click="handleDeactivateUser(u)"
                  class="btn-danger-sm"
                  :disabled="u.id === authStore.user?.id || activeUserCount <= 1"
                  :title="u.id === authStore.user?.id ? 'Cannot deactivate self' : (activeUserCount <= 1 ? 'Cannot deactivate last active user' : 'Deactivate user')"
                >
                  Deactivate
                </button>
                <span v-else class="text-muted text-sm">Inactive</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 1rem;
}
.page-title {
  color: #800000;
  font-size: 1.75rem;
  font-weight: 800;
}
.page-subtitle {
  color: #64748b;
  font-size: 0.9rem;
}
.tab-controls {
  display: flex;
  gap: 0.5rem;
}
.tab-btn {
  padding: 0.5rem 1rem;
  font-size: 0.95rem;
  font-weight: 600;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #475569;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}
.tab-btn.active {
  background: #800000;
  color: #ffffff;
  border-color: #800000;
}
.section-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.section-actions h2 {
  font-size: 1.25rem;
  color: #1e293b;
}
.btn-primary {
  background: #800000;
  color: #ffffff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-primary:hover {
  background: #990000;
}
.btn-lib {
  background: #f1f5f9;
  color: #800000;
  border: 1px solid #cbd5e1;
  padding: 0.35rem 0.65rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-lib:hover {
  background: #800000;
  color: #ffffff;
  border-color: #800000;
}
.form-card {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.form-card h3 {
  color: #800000;
  margin-bottom: 0.5rem;
}
.form-hint {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 1rem;
}
.grid-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}
.full-width {
  grid-column: 1 / -1;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
}
.form-group input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
}
.form-group input:focus {
  border-color: #800000;
  outline: none;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
}
.card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  overflow: hidden;
}
.table-container {
  overflow-x: auto;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.9rem;
}
.data-table th, .data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f1f5f9;
}
.data-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
}
.code-badge {
  background: #eff6ff;
  color: #1d4ed8;
  font-family: monospace;
  font-weight: 600;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
}
.status-badge {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
}
.badge-active {
  background: #dcfce7;
  color: #15803d;
}
.badge-inactive {
  background: #fee2e2;
  color: #b91c1c;
}
.btn-danger-sm {
  background: #fee2e2;
  color: #b91c1c;
  border: 1px solid #fca5a5;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-danger-sm:hover:not(:disabled) {
  background: #ef4444;
  color: #ffffff;
}
.btn-danger-sm:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.alert-banner {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
}
.alert-error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}
.alert-success {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}
.font-bold {
  font-weight: 600;
}
.text-right {
  text-align: right;
}
.text-center {
  text-align: center;
}
.text-sm {
  font-size: 0.8rem;
}
.text-muted {
  color: #64748b;
}
.empty-state {
  padding: 2.5rem;
  text-align: center;
  color: #64748b;
}
</style>
