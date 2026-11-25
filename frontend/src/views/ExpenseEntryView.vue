<script setup>
import { ref, onMounted, watch } from 'vue'
import { apiFetch } from '../services/api'
import ManualExpenseModal from '../components/ManualExpenseModal.vue'
import ExpenseValidationBanner from '../components/ExpenseValidationBanner.vue'

const projects = ref([])
const selectedProjectId = ref(null)
const lineItems = ref([])
const expenses = ref([])

const showModal = ref(false)
const lastSavedExpense = ref(null)
const lastValidation = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')

async function fetchProjects() {
  try {
    const res = await apiFetch('/api/projects')
    if (res.ok) {
      projects.value = await res.json()
      if (projects.value.length > 0 && !selectedProjectId.value) {
        selectedProjectId.value = projects.value[0].id
      }
    }
  } catch (err) {
    errorMessage.value = 'Failed to load projects.'
  }
}

async function loadProjectData() {
  if (!selectedProjectId.value) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    const [itemsRes, expRes] = await Promise.all([
      apiFetch(`/api/projects/${selectedProjectId.value}/line-items`),
      apiFetch(`/api/projects/${selectedProjectId.value}/expenses`)
    ])

    if (itemsRes.ok) {
      const itemsData = await itemsRes.json()
      lineItems.value = itemsData.items || []
    }
    if (expRes.ok) {
      const expData = await expRes.json()
      expenses.value = expData.items || []
    }
  } catch (err) {
    errorMessage.value = 'Failed to load project expenses and line items.'
  } finally {
    isLoading.value = false
  }
}

watch(selectedProjectId, () => {
  lastSavedExpense.value = null
  lastValidation.value = null
  if (selectedProjectId.value) {
    loadProjectData()
  }
})

async function handleExpenseSaved(result) {
  lastSavedExpense.value = result.expense
  lastValidation.value = result.validation
  await loadProjectData()
}

function formatPhp(val) {
  return Number(val || 0).toLocaleString('en-PH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

onMounted(fetchProjects)
</script>

<template>
  <div class="expense-page">
    <div class="page-header">
      <div>
        <h2>Manual Expense Entry</h2>
        <p class="subtitle">Record project expenses against approved line-item budgets (UC-1.2).</p>
      </div>
      <div class="header-controls">
        <select v-model="selectedProjectId" class="project-select" :disabled="projects.length === 0">
          <option v-for="proj in projects" :key="proj.id" :value="proj.id">
            {{ proj.project_code }} &mdash; {{ proj.title }}
          </option>
        </select>
        <button
          type="button"
          class="btn-primary"
          @click="showModal = true"
          :disabled="!selectedProjectId || lineItems.length === 0"
        >
          + Record Manual Expense
        </button>
      </div>
    </div>

    <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>

    <div v-if="selectedProjectId && lineItems.length === 0 && !isLoading" class="info-banner">
      This project has no line-item budgets yet. Configure line-item budgets before encoding expenses.
    </div>

    <ExpenseValidationBanner :validation="lastValidation" :expense="lastSavedExpense" />

    <div class="table-card">
      <h3>Recorded Expenses</h3>
      <div v-if="isLoading" class="empty-state">Loading expenses...</div>
      <div v-else-if="expenses.length === 0" class="empty-state">No expenses recorded for this project yet.</div>
      <table v-else class="expense-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Vendor</th>
            <th>Description</th>
            <th>Funding Source</th>
            <th>Payor Type</th>
            <th>Amount (PHP)</th>
            <th>Receipt</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="exp in expenses" :key="exp.id">
            <td>{{ exp.expense_date }}</td>
            <td>{{ exp.vendor_name || '(Blank)' }}</td>
            <td>{{ exp.description || '-' }}</td>
            <td>{{ exp.funding_source || '-' }}</td>
            <td>{{ exp.payor_type }}</td>
            <td class="num-col">{{ formatPhp(exp.total_amount) }}</td>
            <td>
              <span class="badge" :class="exp.is_valid_receipt ? 'badge-ok' : 'badge-flag'">
                {{ exp.is_valid_receipt ? 'Valid' : 'Flagged' }}
              </span>
            </td>
            <td>{{ exp.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ManualExpenseModal
      :show="showModal"
      :project-id="selectedProjectId"
      :line-items="lineItems"
      @close="showModal = false"
      @saved="handleExpenseSaved"
    />
  </div>
</template>

<style scoped>
.expense-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  background: #ffffff;
  padding: 1.25rem 1.5rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.page-header h2 {
  margin: 0;
  color: #800000;
}
.subtitle {
  margin: 0.25rem 0 0;
  color: #64748b;
  font-size: 0.875rem;
}
.header-controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}
.project-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  min-width: 240px;
}
.btn-primary {
  background: #800000;
  color: #ffffff;
  border: none;
  padding: 0.55rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  padding: 0.75rem 1rem;
  border-radius: 6px;
}
.info-banner {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
  padding: 0.75rem 1rem;
  border-radius: 6px;
}
.table-card {
  background: #ffffff;
  padding: 1.25rem 1.5rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow-x: auto;
}
.table-card h3 {
  margin: 0 0 1rem;
  color: #1e293b;
}
.empty-state {
  color: #64748b;
  padding: 1.5rem 0;
  text-align: center;
}
.expense-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.expense-table th,
.expense-table td {
  text-align: left;
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}
.expense-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
}
.num-col {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
}
.badge-ok {
  background: #dcfce7;
  color: #166534;
}
.badge-flag {
  background: #fee2e2;
  color: #991b1b;
}
</style>
