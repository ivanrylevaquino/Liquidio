<script setup>
import { ref, watch } from 'vue'
import { apiFetch } from '../services/api'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  projectId: {
    type: Number,
    default: null
  },
  lineItems: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'saved'])

const form = ref({
  line_item_id: '',
  funding_source: 'DOST_REIMBURSABLE',
  expense_date: new Date().toISOString().slice(0, 10),
  total_amount: '',
  vendor_name: '',
  vendor_tin: '',
  vendor_address: '',
  payor_type: 'INSTITUTION',
  payor_name: '',
  description: ''
})

const isSubmitting = ref(false)
const errorMessage = ref('')

watch(
  () => props.show,
  (isOpen) => {
    if (isOpen) {
      errorMessage.value = ''
      form.value = {
        line_item_id: props.lineItems.length > 0 ? props.lineItems[0].id : '',
        funding_source: 'DOST_REIMBURSABLE',
        expense_date: new Date().toISOString().slice(0, 10),
        total_amount: '',
        vendor_name: '',
        vendor_tin: '',
        vendor_address: '',
        payor_type: 'INSTITUTION',
        payor_name: '',
        description: ''
      }
    }
  }
)

function formatPhp(val) {
  return Number(val || 0).toLocaleString('en-PH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

async function handleSubmit() {
  if (!props.projectId) return
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const payload = {
      project_id: props.projectId,
      line_item_id: Number(form.value.line_item_id),
      funding_source: form.value.funding_source,
      expense_date: form.value.expense_date,
      total_amount: String(form.value.total_amount),
      vendor_name: form.value.vendor_name,
      vendor_tin: form.value.vendor_tin || null,
      vendor_address: form.value.vendor_address || null,
      payor_type: form.value.payor_type,
      payor_name: form.value.payor_name,
      description: form.value.description || null
    }

    const res = await apiFetch('/api/expenses/manual', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (!res.ok) {
      const detail = Array.isArray(data.detail)
        ? data.detail.map(d => d.msg).join('; ')
        : data.detail
      throw new Error(detail || 'Failed to record manual expense.')
    }

    emit('saved', data)
    emit('close')
  } catch (err) {
    errorMessage.value = err.message || 'Error saving manual expense.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div v-if="show" class="modal-backdrop" @click.self="emit('close')">
    <div class="modal-card">
      <div class="modal-header">
        <h3>Record Manual Expense</h3>
        <button type="button" class="btn-close" @click="emit('close')">&times;</button>
      </div>

      <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>

      <form @submit.prevent="handleSubmit" class="expense-form">
        <div class="form-group">
          <label for="line-item">Line Item Budget *</label>
          <select id="line-item" v-model="form.line_item_id" required :disabled="isSubmitting">
            <option value="" disabled>Select a line item</option>
            <option v-for="item in lineItems" :key="item.id" :value="item.id">
              {{ item.item_code }} - {{ item.category_name }} (DOST Rem: ₱{{ formatPhp(item.remaining_dost) }} | CIT-U Rem: ₱{{ formatPhp(item.remaining_citu) }})
            </option>
          </select>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="funding-source">Funding Source *</label>
            <select id="funding-source" v-model="form.funding_source" required :disabled="isSubmitting">
              <option value="DOST_REIMBURSABLE">DOST Reimbursable</option>
              <option value="CITU_COUNTERPART">CIT-U Counterpart</option>
            </select>
          </div>

          <div class="form-group">
            <label for="expense-date">Expense Date *</label>
            <input id="expense-date" type="date" v-model="form.expense_date" required :disabled="isSubmitting" />
          </div>

          <div class="form-group">
            <label for="total-amount">Total Amount (PHP) *</label>
            <input
              id="total-amount"
              type="number"
              step="0.01"
              min="0.01"
              v-model="form.total_amount"
              required
              placeholder="0.00"
              :disabled="isSubmitting"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="vendor-name">Vendor Name</label>
            <input id="vendor-name" type="text" v-model="form.vendor_name" placeholder="Supplier / Merchant" :disabled="isSubmitting" />
          </div>

          <div class="form-group">
            <label for="vendor-tin">Vendor TIN</label>
            <input id="vendor-tin" type="text" v-model="form.vendor_tin" placeholder="000-000-000-000" :disabled="isSubmitting" />
          </div>
        </div>

        <div class="form-group">
          <label for="vendor-address">Vendor Address</label>
          <input id="vendor-address" type="text" v-model="form.vendor_address" placeholder="Street, City" :disabled="isSubmitting" />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="payor-type">Payor Type *</label>
            <select id="payor-type" v-model="form.payor_type" required :disabled="isSubmitting">
              <option value="INSTITUTION">INSTITUTION (CIT-U / DOST)</option>
              <option value="BLANK">BLANK</option>
              <option value="PERSONAL">PERSONAL</option>
            </select>
          </div>

          <div class="form-group">
            <label for="payor-name">Payor Name</label>
            <input id="payor-name" type="text" v-model="form.payor_name" placeholder="Payor on receipt" :disabled="isSubmitting" />
          </div>
        </div>

        <div class="form-group">
          <label for="description">Description (Optional)</label>
          <textarea
            id="description"
            v-model="form.description"
            rows="2"
            placeholder="Brief particulars of the expense"
            :disabled="isSubmitting"
          ></textarea>
        </div>

        <div class="modal-actions">
          <button type="button" class="btn-secondary" @click="emit('close')" :disabled="isSubmitting">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="isSubmitting || !form.line_item_id">
            {{ isSubmitting ? 'Saving...' : 'Save Expense' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  z-index: 50;
}
.modal-card {
  width: 100%;
  max-width: 680px;
  max-height: 90vh;
  overflow-y: auto;
  background: #ffffff;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.75rem;
}
.modal-header h3 {
  margin: 0;
  color: #800000;
}
.btn-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: #64748b;
}
.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}
.expense-form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 0.75rem;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.form-group label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #334155;
}
.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.5rem 0.65rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
.btn-primary {
  background: #800000;
  color: #ffffff;
  border: none;
  padding: 0.55rem 1.1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-secondary {
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  padding: 0.55rem 1.1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
</style>
