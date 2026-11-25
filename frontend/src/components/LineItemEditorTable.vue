<script setup>
import { ref } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['add-item', 'update-item'])

const showNewRow = ref(false)
const editingId = ref(null)

const newForm = ref({
  item_code: '',
  category_name: '',
  dost_allotment: '0.00',
  citu_allotment: '0.00'
})

const editForm = ref({
  item_code: '',
  category_name: '',
  dost_allotment: '0.00',
  citu_allotment: '0.00'
})

function startEdit(item) {
  editingId.value = item.id
  editForm.value = {
    item_code: item.item_code,
    category_name: item.category_name,
    dost_allotment: item.dost_allotment,
    citu_allotment: item.citu_allotment
  }
}

function cancelEdit() {
  editingId.value = null
}

function handleSaveEdit(itemId) {
  emit('update-item', {
    id: itemId,
    payload: {
      item_code: editForm.value.item_code,
      category_name: editForm.value.category_name,
      dost_allotment: editForm.value.dost_allotment,
      citu_allotment: editForm.value.citu_allotment
    }
  })
  editingId.value = null
}

function handleAddNew() {
  emit('add-item', { ...newForm.value })
  newForm.value = {
    item_code: '',
    category_name: '',
    dost_allotment: '0.00',
    citu_allotment: '0.00'
  }
  showNewRow.value = false
}

function formatPHP(amount) {
  const num = Number(amount) || 0
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: 'PHP',
    minimumFractionDigits: 2
  }).format(num)
}
</script>

<template>
  <div class="table-card">
    <div class="table-header">
      <h3>Approved Line-Item Budget Categories</h3>
      <button @click="showNewRow = !showNewRow" class="btn-primary-sm" :disabled="isLoading">
        {{ showNewRow ? 'Cancel' : '+ Add Line Item' }}
      </button>
    </div>

    <!-- Inline Add Form -->
    <div v-if="showNewRow" class="new-row-container">
      <h4>New Category Allotment</h4>
      <form @submit.prevent="handleAddNew" class="new-row-grid">
        <div class="input-col">
          <label>Code (e.g. PS, MOOE, CO)</label>
          <input v-model="newForm.item_code" placeholder="Code" required />
        </div>
        <div class="input-col col-span-2">
          <label>Category Description</label>
          <input v-model="newForm.category_name" placeholder="Descriptive Name" required />
        </div>
        <div class="input-col">
          <label>DOST Allotment (PHP)</label>
          <input type="number" step="0.01" min="0" v-model="newForm.dost_allotment" required />
        </div>
        <div class="input-col">
          <label>CIT-U Allotment (PHP)</label>
          <input type="number" step="0.01" min="0" v-model="newForm.citu_allotment" required />
        </div>
        <div class="action-col">
          <button type="submit" class="btn-save">Save Line Item</button>
        </div>
      </form>
    </div>

    <div class="table-responsive">
      <table class="budget-table">
        <thead>
          <tr>
            <th>Item Code</th>
            <th>Category Name</th>
            <th class="text-right">Approved DOST</th>
            <th class="text-right">Remaining DOST</th>
            <th class="text-right">Approved CIT-U</th>
            <th class="text-right">Remaining CIT-U</th>
            <th class="text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id" :class="{ 'row-editing': editingId === item.id }">
            <!-- DISPLAY MODE -->
            <template v-if="editingId !== item.id">
              <td><span class="code-tag">{{ item.item_code }}</span></td>
              <td class="font-semibold">{{ item.category_name }}</td>
              <td class="text-right">{{ formatPHP(item.dost_allotment) }}</td>
              <td class="text-right text-dost-rem">{{ formatPHP(item.remaining_dost) }}</td>
              <td class="text-right">{{ formatPHP(item.citu_allotment) }}</td>
              <td class="text-right text-citu-rem">{{ formatPHP(item.remaining_citu) }}</td>
              <td class="text-center">
                <button @click="startEdit(item)" class="btn-edit">Edit</button>
              </td>
            </template>

            <!-- EDIT MODE -->
            <template v-else>
              <td>
                <input v-model="editForm.item_code" class="edit-input-sm" required />
              </td>
              <td>
                <input v-model="editForm.category_name" class="edit-input" required />
              </td>
              <td class="text-right">
                <input type="number" step="0.01" min="0" v-model="editForm.dost_allotment" class="edit-input-num" required />
              </td>
              <td class="text-right text-muted">{{ formatPHP(item.remaining_dost) }}</td>
              <td class="text-right">
                <input type="number" step="0.01" min="0" v-model="editForm.citu_allotment" class="edit-input-num" required />
              </td>
              <td class="text-right text-muted">{{ formatPHP(item.remaining_citu) }}</td>
              <td class="text-center actions-cell">
                <button @click="handleSaveEdit(item.id)" class="btn-save-sm">Save</button>
                <button @click="cancelEdit" class="btn-cancel-sm">Cancel</button>
              </td>
            </template>
          </tr>
          <tr v-if="items.length === 0">
            <td colspan="7" class="empty-cell">
              No line items configured for this project yet. Click <b>+ Add Line Item</b> to set up allotments.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  overflow: hidden;
}
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem;
  border-bottom: 1px solid #f1f5f9;
}
.table-header h3 {
  font-size: 1.15rem;
  color: #1e293b;
  margin: 0;
}
.btn-primary-sm {
  background: #800000;
  color: #ffffff;
  border: none;
  padding: 0.45rem 0.85rem;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
}
.btn-primary-sm:hover {
  background: #990000;
}
.new-row-container {
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
  padding: 1rem 1.25rem;
}
.new-row-container h4 {
  font-size: 0.9rem;
  color: #800000;
  margin-bottom: 0.75rem;
}
.new-row-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  align-items: flex-end;
}
.col-span-2 {
  grid-column: span 2;
}
.input-col {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.input-col label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
}
.input-col input {
  padding: 0.45rem 0.65rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.85rem;
}
.btn-save {
  background: #10b981;
  color: #ffffff;
  border: none;
  padding: 0.5rem 1rem;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-save:hover {
  background: #059669;
}
.table-responsive {
  overflow-x: auto;
}
.budget-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.875rem;
}
.budget-table th, .budget-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f1f5f9;
}
.budget-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
}
.code-tag {
  background: #eff6ff;
  color: #1e40af;
  font-family: monospace;
  font-weight: 700;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-size: 0.8rem;
}
.font-semibold {
  font-weight: 600;
  color: #1e293b;
}
.text-right {
  text-align: right;
}
.text-center {
  text-align: center;
}
.text-muted {
  color: #94a3b8;
}
.text-dost-rem {
  color: #1e40af;
  font-weight: 600;
}
.text-citu-rem {
  color: #991b1b;
  font-weight: 600;
}
.btn-edit {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
}
.btn-edit:hover {
  background: #e2e8f0;
}
.row-editing {
  background-color: #fefce8;
}
.edit-input-sm {
  width: 60px;
  padding: 0.25rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.8rem;
}
.edit-input {
  width: 100%;
  padding: 0.25rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.85rem;
}
.edit-input-num {
  width: 100px;
  padding: 0.25rem;
  text-align: right;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.85rem;
}
.actions-cell {
  display: flex;
  gap: 0.35rem;
  justify-content: center;
}
.btn-save-sm {
  background: #10b981;
  color: white;
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
}
.btn-cancel-sm {
  background: #64748b;
  color: white;
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
}
.empty-cell {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
}
</style>
