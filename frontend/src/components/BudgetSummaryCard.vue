<script setup>
import { computed } from 'vue'

const props = defineProps({
  project: {
    type: Object,
    required: true
  },
  sumDostAllotment: {
    type: [Number, String],
    default: 0
  },
  sumCituAllotment: {
    type: [Number, String],
    default: 0
  },
  warnings: {
    type: Array,
    default: () => []
  }
})

function formatPHP(amount) {
  const num = Number(amount) || 0
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: 'PHP',
    minimumFractionDigits: 2
  }).format(num)
}

const isDostOverrun = computed(() => {
  return Number(props.sumDostAllotment) > Number(props.project.total_dost_budget)
})

const isCituOverrun = computed(() => {
  return Number(props.sumCituAllotment) > Number(props.project.total_citu_budget)
})

const totalAllocated = computed(() => {
  return Number(props.sumDostAllotment) + Number(props.sumCituAllotment)
})

const totalProjectBudget = computed(() => {
  return Number(props.project.total_dost_budget) + Number(props.project.total_citu_budget)
})
</script>

<template>
  <div class="summary-card-wrapper">
    <div class="kpi-grid">
      <!-- DOST Card -->
      <div class="kpi-card" :class="{ 'card-overrun': isDostOverrun }">
        <div class="kpi-header">
          <span class="agency-tag tag-dost">DOST Grant</span>
          <span v-if="isDostOverrun" class="badge-warn">Overrun</span>
        </div>
        <div class="kpi-value">{{ formatPHP(sumDostAllotment) }}</div>
        <div class="kpi-subtext">
          Approved Allotments / Cap: <b>{{ formatPHP(project.total_dost_budget) }}</b>
        </div>
      </div>

      <!-- CIT-U Card -->
      <div class="kpi-card" :class="{ 'card-overrun': isCituOverrun }">
        <div class="kpi-header">
          <span class="agency-tag tag-citu">CIT-U Counterpart</span>
          <span v-if="isCituOverrun" class="badge-warn">Overrun</span>
        </div>
        <div class="kpi-value">{{ formatPHP(sumCituAllotment) }}</div>
        <div class="kpi-subtext">
          Approved Allotments / Cap: <b>{{ formatPHP(project.total_citu_budget) }}</b>
        </div>
      </div>

      <!-- Overall Card -->
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="agency-tag tag-total">Total Funding</span>
        </div>
        <div class="kpi-value">{{ formatPHP(totalAllocated) }}</div>
        <div class="kpi-subtext">
          Total Project Ceiling: <b>{{ formatPHP(totalProjectBudget) }}</b>
        </div>
      </div>
    </div>

    <!-- Warning Banner for Adviser Confirmation -->
    <div v-if="warnings && warnings.length > 0" class="budget-warning-banner">
      <div class="warn-title">&#9888; Budget Ceiling Advisory</div>
      <ul>
        <li v-for="(warn, idx) in warnings" :key="idx">{{ warn }}</li>
      </ul>
      <div class="warn-note">
        Note: The system permits saving line-item allocations exceeding project totals per current policy; pending adviser confirmation.
      </div>
    </div>
  </div>
</template>

<style scoped>
.summary-card-wrapper {
  margin-bottom: 1.5rem;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}
.kpi-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: border-color 0.15s;
}
.kpi-card.card-overrun {
  border-color: #f59e0b;
  background-color: #fffbeb;
}
.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.agency-tag {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}
.tag-dost {
  background: #eff6ff;
  color: #1d4ed8;
}
.tag-citu {
  background: #fef2f2;
  color: #800000;
}
.tag-total {
  background: #f1f5f9;
  color: #334155;
}
.badge-warn {
  background: #f59e0b;
  color: #ffffff;
  font-size: 0.7rem;
  font-weight: 800;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  text-transform: uppercase;
}
.kpi-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: #0f172a;
}
.kpi-subtext {
  font-size: 0.8rem;
  color: #64748b;
}
.budget-warning-banner {
  margin-top: 1rem;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-left: 4px solid #f59e0b;
  color: #92400e;
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
}
.warn-title {
  font-weight: 700;
  margin-bottom: 0.4rem;
}
.budget-warning-banner ul {
  padding-left: 1.25rem;
  margin-bottom: 0.4rem;
}
.warn-note {
  font-size: 0.75rem;
  color: #b45309;
  font-style: italic;
}
</style>
