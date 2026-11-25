<script setup>
defineProps({
  validation: {
    type: Object,
    default: null
  },
  expense: {
    type: Object,
    default: null
  }
})
</script>

<template>
  <div v-if="validation" class="validation-banner" :class="validation.is_valid_receipt ? 'banner-ok' : 'banner-flagged'">
    <div class="banner-header">
      <span class="status-pill" :class="validation.is_valid_receipt ? 'pill-valid' : 'pill-invalid'">
        {{ validation.is_valid_receipt ? 'Valid Receipt' : 'Flagged Receipt' }}
      </span>
      <span v-if="expense" class="saved-note">
        Saved Expense #{{ expense.id }} &mdash; {{ expense.vendor_name || '(Blank Vendor)' }} (PHP {{ Number(expense.total_amount).toLocaleString('en-PH', { minimumFractionDigits: 2 }) }})
      </span>
    </div>

    <div v-if="validation.errors && validation.errors.length > 0" class="flag-section">
      <strong>Validation Flags:</strong>
      <ul>
        <li v-for="(err, idx) in validation.errors" :key="'err-' + idx">{{ err }}</li>
      </ul>
    </div>

    <div v-if="validation.warnings && validation.warnings.length > 0" class="warn-section">
      <strong>Warnings:</strong>
      <ul>
        <li v-for="(warn, idx) in validation.warnings" :key="'warn-' + idx">{{ warn }}</li>
      </ul>
    </div>

    <div
      v-if="(!validation.errors || validation.errors.length === 0) && (!validation.warnings || validation.warnings.length === 0)"
      class="clean-msg"
    >
      All compliance checks passed with no warnings.
    </div>
  </div>
</template>

<style scoped>
.validation-banner {
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  border: 1px solid #cbd5e1;
}
.banner-ok {
  background-color: #f0fdf4;
  border-color: #bbf7d0;
  color: #166534;
}
.banner-flagged {
  background-color: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}
.banner-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.status-pill {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  text-transform: uppercase;
}
.pill-valid {
  background: #dcfce7;
  color: #166534;
}
.pill-invalid {
  background: #fee2e2;
  color: #991b1b;
}
.saved-note {
  font-size: 0.9rem;
  font-weight: 600;
}
.flag-section, .warn-section {
  margin-top: 0.5rem;
  font-size: 0.875rem;
}
.warn-section {
  color: #92400e;
}
ul {
  margin: 0.25rem 0 0 1.25rem;
  padding: 0;
}
.clean-msg {
  font-size: 0.875rem;
}
</style>
