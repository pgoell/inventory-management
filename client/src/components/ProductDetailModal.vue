<template>
  <Teleport to="body">
    <div v-if="isOpen && product" class="modal-scrim" @click="close">
      <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="product-modal-title" @click.stop>
        <div class="modal-head">
          <h3 id="product-modal-title" class="modal-heading">Product Details</h3>
          <button class="modal-x" aria-label="Close" @click="close">&times;</button>
        </div>

        <div class="modal-content">
          <div class="item-head">
            <div class="item-title">
              <h4 class="item-name">{{ product.name }}</h4>
              <div class="mono muted">SKU: {{ product.sku }}</div>
            </div>
            <span class="tag" :class="getStockTag(product.stockLevel)">{{ product.stockLevel }}</span>
          </div>

          <div class="fields">
            <div class="field-row">
              <span class="label">Category</span>
              <span>{{ product.category }}</span>
            </div>
            <div class="field-row">
              <span class="label">Warehouse</span>
              <span>{{ product.warehouse }}</span>
            </div>
            <div class="field-row">
              <span class="label">Units Ordered</span>
              <span class="mono">{{ product.unitsOrdered }}</span>
            </div>
            <div class="field-row">
              <span class="label">Total Revenue</span>
              <span class="mono">{{ currencySymbol }}{{ product.revenue.toLocaleString() }}</span>
            </div>
            <div class="field-row">
              <span class="label">Current Stock</span>
              <span class="mono">{{ product.quantityOnHand }} units</span>
            </div>
            <div class="field-row">
              <span class="label">Reorder Point</span>
              <span class="mono">{{ product.reorderPoint }} units</span>
            </div>
            <div class="field-row">
              <span class="label">First Order Date</span>
              <span>{{ formatDate(product.firstOrderDate) }}</span>
            </div>
            <div class="field-row">
              <span class="label">Stock Status</span>
              <span><span class="tag" :class="getStockTag(product.stockLevel)">{{ product.stockLevel }}</span></span>
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

const { currentCurrency } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  product: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const getStockTag = (stockLevel) => {
  if (stockLevel === 'In Stock') return 'tag--ok'
  if (stockLevel === 'Low Stock') return 'tag--warn'
  if (stockLevel === 'Out of Stock') return 'tag--bad'
  return 'tag--info'
}
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
</style>
