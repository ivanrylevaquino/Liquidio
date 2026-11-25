<script setup>
import { computed } from 'vue'

const props = defineProps({
  burnRate: {
    type: Object,
    required: true
  },
  startDate: {
    type: String,
    default: ''
  },
  endDate: {
    type: String,
    default: ''
  }
})

const badgeClass = computed(() => {
  if (props.burnRate.pace_status === 'ahead of pace') return 'badge-ahead'
  if (props.burnRate.pace_status === 'on track') return 'badge-ontrack'
  return 'badge-neutral'
})

function clampWidth(val) {
  const num = Number(val || 0)
  return `${Math.max(0, Math.min(100, num))}%`
}
</script>

<template>
  <div class="burn-card">
    <div class="burn-header">
      <div>
        <h3>Burn-Rate Pace</h3>
        <p v-if="startDate && endDate" class="timeline-range">
          Project Timeline: {{ startDate }} to {{ endDate }}
        </p>
      </div>
      <span class="pace-badge" :class="badgeClass">
        {{ burnRate.pace_status }}
      </span>
    </div>

    <div class="meter-group">
      <div class="meter-row">
        <div class="meter-label">
          <span>Timeline Elapsed</span>
          <strong>{{ Number(burnRate.timeline_elapsed_percent).toFixed(2) }}%</strong>
        </div>
        <div class="bar-track">
          <div class="bar-fill bar-timeline" :style="{ width: clampWidth(burnRate.timeline_elapsed_percent) }"></div>
        </div>
      </div>

      <div class="meter-row">
        <div class="meter-label">
          <span>Overall Budget Spent</span>
          <strong>{{ Number(burnRate.overall_spent_percent).toFixed(2) }}%</strong>
        </div>
        <div class="bar-track">
          <div
            class="bar-fill"
            :class="burnRate.pace_status === 'ahead of pace' ? 'bar-warn' : 'bar-spent'"
            :style="{ width: clampWidth(burnRate.overall_spent_percent) }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.burn-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
}
.burn-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}
.burn-header h3 {
  margin: 0;
  color: #1e293b;
  font-size: 1rem;
}
.timeline-range {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: #64748b;
}
.pace-badge {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  white-space: nowrap;
}
.badge-ontrack {
  background: #dcfce7;
  color: #166534;
}
.badge-ahead {
  background: #fef3c7;
  color: #92400e;
}
.badge-neutral {
  background: #f1f5f9;
  color: #475569;
}
.meter-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.meter-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #334155;
  margin-bottom: 0.25rem;
}
.bar-track {
  height: 10px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.25s ease;
}
.bar-timeline {
  background: #64748b;
}
.bar-spent {
  background: #16a34a;
}
.bar-warn {
  background: #d97706;
}
</style>
