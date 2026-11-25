<script setup>
import { ref, onMounted, watch } from 'vue'
import { apiFetch } from '../services/api'
import BurnRateIndicator from '../components/BurnRateIndicator.vue'

const projects = ref([])
const selectedProjectId = ref(null)
const summary = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')

function formatPhp(val) {
  return '₱' + Number(val || 0).toLocaleString('en-PH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function barWidth(pct) {
  const num = Number(pct || 0)
  return `${Math.max(0, Math.min(100, num))}%`
}

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
    errorMessage.value = 'Failed to load projects list.'
  }
}

async function loadSummary() {
  if (!selectedProjectId.value) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    const res = await apiFetch(`/api/projects/${selectedProjectId.value}/budget-summary`)
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || 'Failed to load budget summary.')
    }
    summary.value = await res.json()
  } catch (err) {
    errorMessage.value = err.message || 'Error loading budget summary.'
    summary.value = null
  } finally {
    isLoading.value = false
  }
}

watch(selectedProjectId, () => {
  if (selectedProjectId.value) {
    loadSummary()
  }
})

onMounted(fetchProjects)
</script>

<template>
  <div class="dashboard-page">
    <div class="page-header">
      <div>
        <h2>Budget Tracking Dashboard</h2>
        <p class="subtitle">Budget vs. Actual monitoring, burn-rate pace, and receipt quality (UC-1.3).</p>
      </div>

      <div class="header-controls">
        <select v-model="selectedProjectId" class="project-select" :disabled="projects.length === 0">
          <option v-for="proj in projects" :key="proj.id" :value="proj.id">
            {{ proj.project_code }} &mdash; {{ proj.title }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>

    <div v-if="projects.length === 0 && !isLoading" class="empty-card">
      No projects found. Create a project in <strong>Projects &amp; Users</strong> to view budget tracking.
    </div>

    <div v-else-if="isLoading" class="empty-card">Loading budget summary...</div>

    <template v-else-if="summary">
      <div class="summary-grid">
        <div class="summary-card">
          <h3>DOST Reimbursable</h3>
          <div class="metric-row">
            <span>Project Approved Budget</span>
            <strong>{{ formatPhp(summary.totals.total_dost_budget) }}</strong>
          </div>
          <div class="metric-row">
            <span>Total Line-Item Allotment</span>
            <strong>{{ formatPhp(summary.totals.total_dost_allotment) }}</strong>
          </div>
          <div class="metric-row">
            <span>Total Spent</span>
            <strong>{{ formatPhp(summary.totals.total_dost_spent) }}</strong>
          </div>
          <div class="metric-row">
            <span>Total Remaining</span>
            <strong :class="{ 'text-danger': Number(summary.totals.total_dost_remaining) < 0 }">
              {{ formatPhp(summary.totals.total_dost_remaining) }}
            </strong>
          </div>
        </div>

        <div class="summary-card">
          <h3>CIT-U Counterpart</h3>
          <div class="metric-row">
            <span>Project Approved Budget</span>
            <strong>{{ formatPhp(summary.totals.total_citu_budget) }}</strong>
          </div>
          <div class="metric-row">
            <span>Total Line-Item Allotment</span>
            <strong>{{ formatPhp(summary.totals.total_citu_allotment) }}</strong>
          </div>
          <div class="metric-row">
            <span>Total Spent</span>
            <strong>{{ formatPhp(summary.totals.total_citu_spent) }}</strong>
          </div>
          <div class="metric-row">
            <span>Total Remaining</span>
            <strong :class="{ 'text-danger': Number(summary.totals.total_citu_remaining) < 0 }">
              {{ formatPhp(summary.totals.total_citu_remaining) }}
            </strong>
          </div>
        </div>

        <div class="summary-card">
          <h3>Receipt Quality Summary</h3>
          <div class="metric-row">
            <span>Invalid / Flagged Receipts</span>
            <strong :class="{ 'text-danger': summary.receipt_quality.invalid_receipt_count > 0 }">
              {{ summary.receipt_quality.invalid_receipt_count }}
            </strong>
          </div>
          <div class="metric-row">
            <span>Invalid Receipts Total Amount</span>
            <strong>{{ formatPhp(summary.receipt_quality.invalid_receipt_total_amount) }}</strong>
          </div>
          <div class="metric-row">
            <span>Pending Review Expenses</span>
            <strong>{{ summary.receipt_quality.pending_review_count }}</strong>
          </div>
        </div>
      </div>

      <BurnRateIndicator
        :burn-rate="summary.burn_rate"
        :start-date="summary.start_date"
        :end-date="summary.end_date"
      />

      <div class="table-card">
        <h3>Line-Item Budget Breakdown</h3>
        <div v-if="summary.line_items.length === 0" class="empty-inline">
          No line-item budgets configured for this project yet.
        </div>
        <table v-else class="budget-table">
          <thead>
            <tr>
              <th>Item Code</th>
              <th>Category</th>
              <th>DOST (Spent / Allotment)</th>
              <th>DOST Remaining</th>
              <th>CIT-U (Spent / Allotment)</th>
              <th>CIT-U Remaining</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in summary.line_items" :key="item.line_item_id">
              <td><strong>{{ item.item_code }}</strong></td>
              <td>{{ item.category_name }}</td>
              <td>
                <div class="cell-amounts">
                  <span>{{ formatPhp(item.dost_spent) }} / {{ formatPhp(item.dost_allotment) }}</span>
                  <span class="pct-label">{{ Number(item.percent_spent_dost).toFixed(2) }}%</span>
                </div>
                <div class="progress-track">
                  <div
                    class="progress-fill"
                    :class="item.is_over_budget_dost ? 'fill-over' : 'fill-ok'"
                    :style="{ width: barWidth(item.percent_spent_dost) }"
                  ></div>
                </div>
              </td>
              <td class="num-col" :class="{ 'text-danger': Number(item.remaining_dost) < 0 }">
                {{ formatPhp(item.remaining_dost) }}
              </td>
              <td>
                <div class="cell-amounts">
                  <span>{{ formatPhp(item.citu_spent) }} / {{ formatPhp(item.citu_allotment) }}</span>
                  <span class="pct-label">{{ Number(item.percent_spent_citu).toFixed(2) }}%</span>
                </div>
                <div class="progress-track">
                  <div
                    class="progress-fill"
                    :class="item.is_over_budget_citu ? 'fill-over' : 'fill-ok'"
                    :style="{ width: barWidth(item.percent_spent_citu) }"
                  ></div>
                </div>
              </td>
              <td class="num-col" :class="{ 'text-danger': Number(item.remaining_citu) < 0 }">
                {{ formatPhp(item.remaining_citu) }}
              </td>
              <td>
                <span
                  v-if="item.is_over_budget_dost || item.is_over_budget_citu"
                  class="warn-badge"
                >
                  Over Budget
                </span>
                <span v-else class="ok-badge">Within Budget</span>
                <span v-if="item.data_mismatch" class="mismatch-badge" title="Remaining balance differs from allotment minus spent">
                  Data Mismatch
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page {
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
.project-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  min-width: 240px;
}
.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  padding: 0.75rem 1rem;
  border-radius: 6px;
}
.empty-card,
.table-card {
  background: #ffffff;
  padding: 1.25rem 1.5rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.empty-card,
.empty-inline {
  color: #64748b;
  text-align: center;
  padding: 1.5rem 0;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}
.summary-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.15rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.summary-card h3 {
  margin: 0 0 0.25rem;
  font-size: 0.95rem;
  color: #800000;
}
.metric-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #334155;
}
.text-danger {
  color: #b91c1c;
}
.table-card {
  overflow-x: auto;
}
.table-card h3 {
  margin: 0 0 1rem;
  color: #1e293b;
}
.budget-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.budget-table th,
.budget-table td {
  text-align: left;
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
}
.budget-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
}
.cell-amounts {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
  font-size: 0.8rem;
}
.pct-label {
  font-weight: 600;
  color: #475569;
}
.progress-track {
  height: 8px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
  min-width: 140px;
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
}
.fill-ok {
  background: #16a34a;
}
.fill-over {
  background: #dc2626;
}
.num-col {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}
.warn-badge,
.ok-badge,
.mismatch-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  margin-right: 0.25rem;
}
.warn-badge {
  background: #fee2e2;
  color: #991b1b;
}
.ok-badge {
  background: #dcfce7;
  color: #166534;
}
.mismatch-badge {
  background: #fef3c7;
  color: #92400e;
}
</style>
