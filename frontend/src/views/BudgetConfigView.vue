<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '../services/api'
import BudgetSummaryCard from '../components/BudgetSummaryCard.vue'
import LineItemEditorTable from '../components/LineItemEditorTable.vue'

const route = useRoute()
const router = useRouter()

const projects = ref([])
const selectedProjectId = ref(null)
const selectedProject = ref(null)
const lineItems = ref([])
const sumDost = ref('0.00')
const sumCitu = ref('0.00')
const warnings = ref([])

const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

async function fetchProjects() {
  try {
    const res = await apiFetch('/api/projects')
    if (res.ok) {
      projects.value = await res.json()
      // If project_id provided in query or params, select it; otherwise default to first
      const paramId = route.params.id || route.query.project_id
      if (paramId && projects.value.some(p => p.id === Number(paramId))) {
        selectedProjectId.value = Number(paramId)
      } else if (projects.value.length > 0) {
        selectedProjectId.value = projects.value[0].id
      }
    }
  } catch (err) {
    errorMessage.value = 'Failed to load projects list.'
  }
}

async function loadProjectBudget() {
  if (!selectedProjectId.value) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    // 1. Fetch project profile
    const projRes = await apiFetch(`/api/projects/${selectedProjectId.value}`)
    if (projRes.ok) {
      selectedProject.value = await projRes.json()
    } else {
      throw new Error('Project not found.')
    }

    // 2. Fetch line items
    const itemsRes = await apiFetch(`/api/projects/${selectedProjectId.value}/line-items`)
    if (itemsRes.ok) {
      const data = await itemsRes.json()
      lineItems.value = data.items
      sumDost.value = data.sum_dost_allotment
      sumCitu.value = data.sum_citu_allotment
      warnings.value = data.warnings || []
    }
  } catch (err) {
    errorMessage.value = err.message || 'Error loading budget data.'
  } finally {
    isLoading.value = false
  }
}

watch(selectedProjectId, () => {
  if (selectedProjectId.value) {
    loadProjectBudget()
  }
})

async function handleAddItem(payload) {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const res = await apiFetch(`/api/projects/${selectedProjectId.value}/line-items`, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to save line item.')
    }
    successMessage.value = `Line item '${data.line_item.item_code}' added successfully.`
    await loadProjectBudget()
  } catch (err) {
    errorMessage.value = err.message
  }
}

async function handleUpdateItem({ id, payload }) {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const res = await apiFetch(`/api/projects/${selectedProjectId.value}/line-items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to update line item.')
    }
    successMessage.value = `Line item '${data.line_item.item_code}' updated successfully.`
    await loadProjectBudget()
  } catch (err) {
    errorMessage.value = err.message
  }
}

onMounted(() => {
  fetchProjects()
})
</script>

<template>
  <div class="budget-config-container">
    <div class="view-header">
      <div>
        <h1 class="view-title">Approved Line-Item Budget Setup (LIB)</h1>
        <p class="view-subtitle">UC-1.1: Configure contractual line-item allotments and manage remaining balances</p>
      </div>

      <!-- Project Selector Dropdown -->
      <div class="project-selector-wrapper">
        <label for="project-select">Active Project:</label>
        <select id="project-select" v-model="selectedProjectId" class="project-select">
          <option v-for="p in projects" :key="p.id" :value="p.id">
            [{{ p.project_code }}] {{ p.title }}
          </option>
        </select>
      </div>
    </div>

    <!-- Alert Banners -->
    <div v-if="errorMessage" class="alert-banner alert-error">
      <span>&#9888; {{ errorMessage }}</span>
    </div>
    <div v-if="successMessage" class="alert-banner alert-success">
      <span>&#10004; {{ successMessage }}</span>
    </div>

    <div v-if="selectedProject">
      <!-- Budget Summary KPI Cards -->
      <BudgetSummaryCard
        :project="selectedProject"
        :sum-dost-allotment="sumDost"
        :sum-citu-allotment="sumCitu"
        :warnings="warnings"
      />

      <!-- Line Item Editor Table -->
      <LineItemEditorTable
        :items="lineItems"
        :is-loading="isLoading"
        @add-item="handleAddItem"
        @update-item="handleUpdateItem"
      />
    </div>

    <div v-else-if="projects.length === 0" class="empty-prompt">
      <p>No projects found. Please create a project first under <router-link to="/projects">Projects &amp; Users</router-link>.</p>
    </div>
  </div>
</template>

<style scoped>
.budget-config-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 1rem;
}
.view-title {
  color: #800000;
  font-size: 1.75rem;
  font-weight: 800;
}
.view-subtitle {
  color: #64748b;
  font-size: 0.9rem;
}
.project-selector-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.project-selector-wrapper label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
}
.project-select {
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
  font-weight: 600;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background-color: #ffffff;
  color: #1e293b;
  max-width: 320px;
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
.empty-prompt {
  background: #ffffff;
  padding: 2.5rem;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #e2e8f0;
  color: #64748b;
}
.empty-prompt a {
  color: #800000;
  font-weight: 700;
}
</style>
