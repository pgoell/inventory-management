<template>
  <Teleport to="body">
    <div v-if="isOpen && costData" class="modal-scrim" @click="close">
      <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="cost-modal-title" @click.stop>
        <div class="modal-head">
          <h3 id="cost-modal-title" class="modal-heading">{{ costData.month }} Cost Breakdown</h3>
          <button class="modal-x" aria-label="Close" @click="close">&times;</button>
        </div>

        <div class="modal-content">
          <div class="stats">
            <div class="stat">
              <span class="stat-label">Total Costs</span>
              <span class="stat-value">{{ currencySymbol }}{{ totalCosts.toLocaleString() }}</span>
            </div>
          </div>

          <div class="ledger-wrap">
            <table class="ledger">
              <thead>
                <tr>
                  <th>Category</th>
                  <th class="num">Amount</th>
                  <th class="num">Share</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in rows" :key="row.key">
                  <td>{{ row.name }}</td>
                  <td class="num">{{ currencySymbol }}{{ row.amount.toLocaleString() }}</td>
                  <td class="num">{{ row.percentage }}% of total</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td>Total</td>
                  <td class="num">{{ currencySymbol }}{{ totalCosts.toLocaleString() }}</td>
                  <td class="num"></td>
                </tr>
              </tfoot>
            </table>
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
  costData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const totalCosts = computed(() => {
  if (!props.costData) return 0
  return props.costData.procurement + props.costData.operational +
         props.costData.labor + props.costData.overhead
})

const percentageOf = (value) => {
  if (totalCosts.value === 0) return 0
  return ((value / totalCosts.value) * 100).toFixed(1)
}

const rows = computed(() => {
  if (!props.costData) return []
  return [
    { key: 'procurement', name: 'Procurement', amount: props.costData.procurement },
    { key: 'operational', name: 'Operational', amount: props.costData.operational },
    { key: 'labor', name: 'Labor', amount: props.costData.labor },
    { key: 'overhead', name: 'Overhead', amount: props.costData.overhead }
  ].map(row => ({ ...row, percentage: percentageOf(row.amount) }))
})

const close = () => {
  emit('close')
}
</script>
