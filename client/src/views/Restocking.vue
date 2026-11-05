<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

const { t, currentCurrency } = useI18n()
const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

const STEP = 100
const forecasts = ref([])
const loading = ref(true)
const error = ref(null)

const budget = ref(0)
const lines = ref([])

const placing = ref(false)
const placeError = ref(null)
const placedOrder = ref(null)

// Items whose forecast is above current demand; rising trend first, then biggest gap.
const candidates = computed(() =>
  forecasts.value
    .map(f => ({ ...f, gap: f.forecasted_demand - f.current_demand }))
    .filter(f => f.gap > 0)
    .sort((a, b) => {
      const ai = a.trend === 'increasing' ? 0 : 1
      const bi = b.trend === 'increasing' ? 0 : 1
      return ai - bi || b.gap - a.gap
    })
)

const coverAllCost = computed(() => candidates.value.reduce((sum, c) => sum + c.gap * c.unit_cost, 0))
const maxBudget = computed(() => Math.max(STEP, Math.ceil(coverAllCost.value / STEP) * STEP))

const toNumber = value => {
  const n = Number(value)
  return Number.isFinite(n) && n > 0 ? n : 0
}

const recommend = () => {
  let remaining = toNumber(budget.value)
  const result = []
  for (const c of candidates.value) {
    const fullCost = c.gap * c.unit_cost
    let qty = c.gap
    const fits = fullCost <= remaining
    if (!fits) qty = Math.floor(remaining / c.unit_cost)
    if (qty > 0) {
      result.push({ ...c, quantity: qty, selected: true })
      remaining -= qty * c.unit_cost
    }
    if (!fits) break
  }
  lines.value = result
}

// Only the budget re-runs the recommendation; line edits stay put.
watch(budget, recommend)

const lineTotal = line => Math.round(line.quantity * line.unit_cost * 100) / 100
const activeLines = computed(() => lines.value.filter(l => l.selected && l.quantity > 0))
const totalCost = computed(() => Math.round(activeLines.value.reduce((s, l) => s + lineTotal(l), 0) * 100) / 100)
const budgetLeft = computed(() => Math.round((toNumber(budget.value) - totalCost.value) * 100) / 100)
const longestLead = computed(() => activeLines.value.reduce((m, l) => Math.max(m, l.lead_time_days), 0))
const overBudget = computed(() => totalCost.value > toNumber(budget.value))
const canPlace = computed(() => activeLines.value.length > 0 && !overBudget.value && !placing.value)

const setQuantity = (line, event) => {
  const n = Math.floor(Number(event.target.value))
  line.quantity = Number.isFinite(n) && n > 0 ? n : 0
}

const money = value =>
  `${currencySymbol.value}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

const trendClass = trend => ({ increasing: 'ok', decreasing: 'bad' }[trend] || 'neutral')
const trendLabel = trend => (['increasing', 'stable', 'decreasing'].includes(trend) ? t(`trends.${trend}`) : trend)

const placeOrder = async () => {
  placing.value = true
  placeError.value = null
  placedOrder.value = null
  try {
    placedOrder.value = await api.createRestockOrder({
      budget: toNumber(budget.value),
      items: activeLines.value.map(l => ({ sku: l.item_sku, quantity: l.quantity }))
    })
  } catch (err) {
    placeError.value = err.response?.data?.detail || t('restocking.failed')
  } finally {
    placing.value = false
  }
}

onMounted(async () => {
  try {
    forecasts.value = await api.getDemandForecasts()
    budget.value = Math.round(maxBudget.value / 2 / STEP) * STEP
    recommend()
  } catch (err) {
    error.value = 'Failed to load demand forecasts: ' + err.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="restocking">
    <div class="page-head">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats">
        <div class="stat">
          <span class="stat-label">{{ t('restocking.budget') }}</span>
          <span class="stat-value">{{ money(toNumber(budget)) }}</span>
        </div>
        <div class="stat" :class="{ 'is-bad': overBudget }">
          <span class="stat-label">{{ t('restocking.plannedSpend') }}</span>
          <span class="stat-value">{{ money(totalCost) }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">{{ t('restocking.lines') }}</span>
          <span class="stat-value">{{ activeLines.length }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">{{ t('restocking.longestLead') }}</span>
          <span class="stat-value">{{ t('restocking.days', { count: longestLead }) }}</span>
        </div>
      </div>

      <div class="section">
        <div class="section-label">
          <span>{{ t('restocking.budget') }}</span>
        </div>
        <div class="budget">
          <div class="budget-figure mono">{{ money(toNumber(budget)) }}</div>
          <input
            v-model.number="budget"
            type="range"
            class="range"
            min="0"
            :max="maxBudget"
            :step="STEP"
            :aria-label="t('restocking.budget')"
          />
          <div class="field budget-input">
            <label for="budget-amount">{{ t('restocking.budgetInput') }}</label>
            <input
              id="budget-amount"
              v-model.number="budget"
              type="number"
              class="input mono"
              min="0"
              :step="STEP"
            />
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-label">
          <span>{{ t('restocking.planTitle') }}</span>
          <span class="aside">{{ t('restocking.planAside') }}</span>
        </div>

        <div v-if="candidates.length === 0" class="empty">{{ t('restocking.noGaps') }}</div>
        <div v-else-if="lines.length === 0" class="empty">{{ t('restocking.empty') }}</div>
        <div v-else class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>{{ t('restocking.table.include') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.gap') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="line in lines" :key="line.item_sku" :class="{ 'is-off': !line.selected }">
                <td>
                  <input
                    v-model="line.selected"
                    type="checkbox"
                    :aria-label="`${t('restocking.table.include')}: ${line.item_sku}`"
                  />
                </td>
                <td class="mono">{{ line.item_sku }}</td>
                <td>{{ line.item_name }}</td>
                <td><span :class="['tag', `tag--${trendClass(line.trend)}`]">{{ trendLabel(line.trend) }}</span></td>
                <td class="num">{{ line.gap }}</td>
                <td class="num">
                  <input
                    :value="line.quantity"
                    type="number"
                    min="0"
                    step="1"
                    class="input mono qty"
                    :aria-label="`${t('restocking.table.quantity')}: ${line.item_sku}`"
                    @input="setQuantity(line, $event)"
                  />
                </td>
                <td class="num">{{ money(line.unit_cost) }}</td>
                <td class="num">{{ line.lead_time_days }}</td>
                <td class="num">{{ line.selected ? money(lineTotal(line)) : '' }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="8">{{ t('restocking.total') }}</td>
                <td class="num">{{ money(totalCost) }}</td>
              </tr>
              <tr>
                <td colspan="8">{{ overBudget ? t('restocking.over') : t('restocking.budgetLeft') }}</td>
                <td class="num" :class="{ over: overBudget }">{{ money(Math.abs(budgetLeft)) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div class="toolbar actions">
          <button type="button" class="btn btn--signal" :disabled="!canPlace" @click="placeOrder">
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="placeError" class="error" role="alert">{{ placeError }}</div>
        <p v-if="placedOrder" class="confirm" role="status">
          {{ t('restocking.placed', { id: placedOrder.id, date: placedOrder.expected_delivery }) }}
          <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.budget {
  display: grid;
  grid-template-columns: auto 1fr 10rem;
  align-items: center;
  gap: var(--s-5);
}

.budget-figure {
  font-size: var(--fs-xl);
  font-weight: 500;
  letter-spacing: -0.02em;
  min-width: 8ch;
}

.qty {
  width: 6rem;
  text-align: right;
}

.is-off td:not(:first-child) {
  color: var(--ink-3);
}

.over {
  color: var(--bad);
}

.actions {
  margin-top: var(--s-4);
}

.confirm {
  margin-top: var(--s-2);
  color: var(--ok);
  font-weight: 600;
}

.confirm a {
  margin-left: var(--s-2);
}

@media (max-width: 720px) {
  .budget {
    grid-template-columns: 1fr;
    gap: var(--s-3);
  }
}
</style>
