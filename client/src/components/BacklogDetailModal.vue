<template>
  <Teleport to="body">
    <div v-if="isOpen && backlogItem" class="modal-scrim" @click="close">
      <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="backlog-modal-title" @click.stop>
        <div class="modal-head">
          <h3 id="backlog-modal-title" class="modal-heading">Inventory Shortage Details</h3>
          <button class="modal-x" aria-label="Close" @click="close">&times;</button>
        </div>

        <div class="modal-content">
          <div class="item-head">
            <div class="item-title">
              <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
              <div class="mono muted">SKU: {{ backlogItem.item_sku }}</div>
            </div>
            <span class="tag" :class="priorityTag">{{ backlogItem.priority }} Priority</span>
          </div>

          <div class="stats">
            <div class="stat is-bad">
              <span class="stat-label">Shortage Amount</span>
              <span class="stat-value">{{ shortage }}</span>
              <span class="stat-note">units</span>
            </div>
            <div class="stat is-warn">
              <span class="stat-label">Days Delayed</span>
              <span class="stat-value">{{ backlogItem.days_delayed }}</span>
              <span class="stat-note">days</span>
            </div>
          </div>

          <div class="fields">
            <div class="field-row">
              <span class="label">Order ID</span>
              <span class="mono">{{ backlogItem.order_id }}</span>
            </div>
            <div class="field-row">
              <span class="label">Item SKU</span>
              <span class="mono">{{ backlogItem.item_sku }}</span>
            </div>
            <div class="field-row">
              <span class="label">Quantity Needed</span>
              <span class="mono">{{ backlogItem.quantity_needed }} units</span>
            </div>
            <div class="field-row">
              <span class="label">Quantity Available</span>
              <span class="mono">{{ backlogItem.quantity_available }} units</span>
            </div>
            <div class="field-row">
              <span class="label">Expected Date</span>
              <span>{{ formatDate(backlogItem.expected_date) }}</span>
            </div>
            <div class="field-row">
              <span class="label">Status</span>
              <span><span class="tag tag--bad">Backordered</span></span>
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

const { translateProductName } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const priorityTag = computed(() => {
  const map = { high: 'tag--bad', medium: 'tag--warn', low: 'tag--info' }
  return map[props.backlogItem?.priority] || ''
})

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
