<template>
  <Teleport to="body">
    <div v-if="isOpen && inventoryItem" class="modal-scrim" @click="close">
      <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="inventory-modal-title" @click.stop>
        <div class="modal-head">
          <h3 id="inventory-modal-title" class="modal-heading">Inventory Item Details</h3>
          <button class="modal-x" aria-label="Close" @click="close">&times;</button>
        </div>

        <div class="modal-content">
          <div class="item-head">
            <div class="item-title">
              <h4 class="item-name">{{ translateProductName(inventoryItem.name) }}</h4>
              <div class="mono muted">SKU: {{ inventoryItem.sku }}</div>
            </div>
            <span class="tag" :class="statusTag">{{ getStockStatus() }}</span>
          </div>

          <div class="stats">
            <div class="stat">
              <span class="stat-label">Quantity on Hand</span>
              <span class="stat-value">{{ inventoryItem.quantity_on_hand }}</span>
              <span class="stat-note">units</span>
            </div>
            <div class="stat" :class="statTone">
              <span class="stat-label">Stock Level</span>
              <span class="stat-value">{{ stockPercentage }}%</span>
              <span class="stat-note">vs. reorder point</span>
            </div>
          </div>

          <div class="fields">
            <div class="field-row">
              <span class="label">Category</span>
              <span>{{ inventoryItem.category }}</span>
            </div>
            <div class="field-row">
              <span class="label">Location</span>
              <span>{{ inventoryItem.location }}</span>
            </div>
            <div class="field-row">
              <span class="label">Reorder Point</span>
              <span class="mono">{{ inventoryItem.reorder_point }} units</span>
            </div>
            <div class="field-row">
              <span class="label">Units Remaining</span>
              <span class="mono" :class="remaining <= 0 ? 'is-bad' : 'is-ok'">{{ remaining }} units</span>
            </div>
            <div class="field-row">
              <span class="label">Unit Cost</span>
              <span class="mono">{{ currencySymbol }}{{ inventoryItem.unit_cost.toFixed(2) }}</span>
            </div>
            <div class="field-row">
              <span class="label">Total Value</span>
              <span class="mono total-value">
                {{ currencySymbol }}{{ totalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}
              </span>
            </div>
            <div class="field-row">
              <span class="label">Warehouse</span>
              <span>{{ translateWarehouse(inventoryItem.location) }}</span>
            </div>
            <div class="field-row">
              <span class="label">Status</span>
              <span><span class="tag" :class="statusTag">{{ getStockStatus() }}</span></span>
            </div>
          </div>
        </div>

        <div class="modal-foot">
          <button class="btn" @click="close">Close</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentCurrency, translateProductName, translateWarehouse } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  inventoryItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const totalValue = computed(() => {
  if (!props.inventoryItem) return 0
  return props.inventoryItem.quantity_on_hand * props.inventoryItem.unit_cost
})

const remaining = computed(() => {
  if (!props.inventoryItem) return 0
  return props.inventoryItem.quantity_on_hand - props.inventoryItem.reorder_point
})

const stockPercentage = computed(() => {
  if (!props.inventoryItem || props.inventoryItem.reorder_point === 0) return 0
  return Math.round((props.inventoryItem.quantity_on_hand / props.inventoryItem.reorder_point) * 100)
})

const close = () => {
  emit('close')
}

const getStockStatus = () => {
  if (!props.inventoryItem) return 'Unknown'
  if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point) {
    return 'Low Stock'
  } else if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point * 1.5) {
    return 'Adequate'
  } else {
    return 'In Stock'
  }
}

const statusTag = computed(() => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'tag--bad'
  if (status === 'Adequate') return 'tag--warn'
  return 'tag--ok'
})

const statTone = computed(() => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'is-bad'
  if (status === 'Adequate') return 'is-warn'
  return 'is-ok'
})
</script>

<style scoped>
.item-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--s-4);
  padding-bottom: var(--s-4);
  margin-bottom: var(--s-4);
  border-bottom: var(--hair);
}

.item-title {
  min-width: 0;
}

.item-name {
  font-size: var(--fs-lg);
  margin-bottom: var(--s-1);
}

.fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  column-gap: var(--s-5);
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: var(--s-1);
  padding: var(--s-2) 0;
  border-bottom: var(--hair);
}

.total-value {
  font-weight: 600;
}

.is-bad {
  color: var(--bad);
}

.is-ok {
  color: var(--ok);
}
</style>
