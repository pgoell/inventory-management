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
const submitted = ref([])

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

// Every item with a gap gets a line; items the budget cannot cover start unticked at quantity 0.
const recommend = () => {
  let remaining = toNumber(budget.value)
  let stopped = false
  lines.value = candidates.value.map(c => {
    let quantity = 0
    if (!stopped) {
      if (c.gap * c.unit_cost <= remaining) quantity = c.gap
      else {
        quantity = Math.floor(remaining / c.unit_cost)
        stopped = true
      }
      remaining -= quantity * c.unit_cost
    }
    return { ...c, quantity, selected: quantity > 0 }
  })
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
  line.selected = line.quantity > 0
}

const money = value =>
  `${currencySymbol.value}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

const trendClass = trend => ({ increasing: 'ok', decreasing: 'bad' }[trend] || 'neutral')
const trendLabel = trend => (['increasing', 'stable', 'decreasing'].includes(trend) ? t(`trends.${trend}`) : trend)

const loadSubmitted = async () => {
  try {
    const all = await api.getRestockOrders()
    submitted.value = [...all]
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at) || String(b.id).localeCompare(String(a.id)))
      .slice(0, 3)
  } catch (err) {
    console.error('Failed to load restock orders:', err)
  }
}

const placeOrder = async () => {
  placing.value = true
  placeError.value = null
  placedOrder.value = null
  try {
    placedOrder.value = await api.createRestockOrder({
      budget: toNumber(budget.value),
      items: activeLines.value.map(l => ({ sku: l.item_sku, quantity: l.quantity }))
    })
    await loadSubmitted()
  } catch (err) {
    placeError.value = err.response?.data?.detail || t('restocking.failed')
  } finally {
    placing.value = false
  }
}

const budgetPct = computed(() => {
  const b = toNumber(budget.value)
  return b > 0 ? (totalCost.value / b) * 100 : 0
})
const rangeFill = computed(() => `${maxBudget.value > 0 ? (toNumber(budget.value) / maxBudget.value) * 100 : 0}%`)

const formatDate = value => {
  const d = new Date(value)
  return isNaN(d.getTime()) ? '' : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}
const inTransit = order => {
  const d = new Date(order.expected_delivery)
  return !isNaN(d.getTime()) && d.getTime() > Date.now()
}

// Paired horizontal bars, one shared scale.
const CH = { w: 296, rowH: 22, top: 4, left: 58, right: 16, axisH: 16 }
const chart = computed(() => {
  const items = forecasts.value
  const peak = items.reduce((m, f) => Math.max(m, f.current_demand, f.forecasted_demand), 0)
  const step = peak > 1000 ? 500 : 250
  const max = Math.max(step, Math.ceil(peak / step) * step)
  const x = v => CH.left + (v / max) * (CH.w - CH.left - CH.right)
  const height = CH.top + items.length * CH.rowH + CH.axisH
  const ticks = []
  for (let v = 0; v <= max; v += step) ticks.push({ v, x: x(v) })
  const rows = items.map((f, i) => {
    const y = CH.top + i * CH.rowH + 4
    return {
      sku: f.item_sku,
      y,
      cur: x(f.current_demand) - CH.left,
      fc: x(f.forecasted_demand) - CH.left,
      label: t('restocking.chart.tooltip', { sku: f.item_sku, current: f.current_demand, forecast: f.forecasted_demand })
    }
  })
  return { height, ticks, rows, bottom: height - CH.axisH }
})

onMounted(async () => {
  loadSubmitted()
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
    <div v-else class="workspace">
      <div class="section panel--main">
        <div class="section-label plan-head">
          <span class="plan-title">
            {{ t('restocking.planTitle') }}
            <span class="aside">{{ t('restocking.lineCount', { count: activeLines.length, total: lines.length }) }}</span>
          </span>
          <div class="budget">
            <label for="budget-range">{{ t('restocking.budget') }}</label>
            <span class="range-end mono">{{ currencySymbol }}0</span>
            <input
              id="budget-range"
              v-model.number="budget"
              type="range"
              class="range"
              min="0"
              :max="maxBudget"
              :step="STEP"
              :style="{ '--fill': rangeFill }"
            />
            <span class="range-end mono">{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
            <label for="budget-amount" class="sr-only">{{ t('restocking.budgetInput') }}</label>
            <input
              id="budget-amount"
              v-model.number="budget"
              type="number"
              class="input mono budget-num"
              min="0"
              :step="STEP"
            />
          </div>
        </div>

        <div v-if="candidates.length === 0" class="empty">{{ t('restocking.noGaps') }}</div>
        <template v-else>
          <div class="ledger-wrap">
            <table class="ledger">
              <thead>
                <tr>
                  <th class="c-check"><span class="sr-only">{{ t('restocking.table.include') }}</span></th>
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
                <tr v-for="line in lines" :key="line.item_sku" :class="{ 'is-off': !line.selected || line.quantity === 0 }">
                  <td class="c-check">
                    <input
                      v-model="line.selected"
                      type="checkbox"
                      :aria-label="`${t('restocking.table.include')}: ${line.item_sku}`"
                    />
                  </td>
                  <td class="mono sku">{{ line.item_sku }}</td>
                  <td class="item" :title="line.item_name">{{ line.item_name }}</td>
                  <td><span :class="['tag', `tag--${trendClass(line.trend)}`]">{{ trendLabel(line.trend) }}</span></td>
                  <td class="num">{{ line.gap.toLocaleString() }}</td>
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
                  <td class="num">{{ line.selected && line.quantity > 0 ? money(lineTotal(line)) : '-' }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="8" class="foot-label">{{ t('restocking.total') }}</td>
                  <td class="num">{{ money(totalCost) }}</td>
                </tr>
                <tr class="foot-sub">
                  <td colspan="8" class="foot-label">{{ overBudget ? t('restocking.over') : t('restocking.budgetLeft') }}</td>
                  <td class="num" :class="{ over: overBudget }">{{ money(Math.abs(budgetLeft)) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div class="panel-foot">
            <span class="foot-hint muted">{{ t('restocking.hint') }}</span>
            <span v-if="placedOrder" class="confirm" role="status">
              {{ t('restocking.placed', { id: placedOrder.id, date: placedOrder.expected_delivery }) }}
              <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
            </span>
            <button type="button" class="btn btn--primary" :disabled="!canPlace" @click="placeOrder">
              {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
            </button>
          </div>
          <div v-if="placeError" class="error" role="alert">{{ placeError }}</div>
        </template>
      </div>

      <aside class="inspector" :aria-label="t('restocking.inspector')">
        <section class="section summary">
          <div class="section-label"><span>{{ t('restocking.summary') }}</span></div>
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
              <span class="stat-value">{{ longestLead ? t('restocking.days', { count: longestLead }) : '-' }}</span>
            </div>
          </div>
          <div class="meter-row">
            <span>{{ t('restocking.budgetUsed') }}</span>
            <span class="mono">{{ toNumber(budget) > 0 ? budgetPct.toFixed(1) + '%' : '-' }}</span>
          </div>
          <div class="meter" aria-hidden="true">
            <i :class="{ over: overBudget }" :style="{ width: Math.min(100, budgetPct) + '%' }"></i>
          </div>
        </section>

        <section class="section">
          <div class="section-label">
            <span>{{ t('restocking.chart.title') }}</span>
            <span class="aside">{{ t('restocking.chart.unit') }}</span>
          </div>
          <div class="legend">
            <span><i class="sw sw--current"></i>{{ t('restocking.chart.current') }}</span>
            <span><i class="sw sw--forecast"></i>{{ t('restocking.chart.forecast') }}</span>
          </div>
          <div class="chart-wrap">
            <svg
              class="chart"
              :viewBox="`0 0 ${CH.w} ${chart.height}`"
              role="img"
              :aria-label="t('restocking.chart.label')"
            >
              <g v-for="tick in chart.ticks" :key="tick.v">
                <line :x1="tick.x" :x2="tick.x" :y1="CH.top" :y2="chart.bottom" class="grid" />
                <text :x="tick.x" :y="chart.height - 4" text-anchor="middle">{{ tick.v }}</text>
              </g>
              <g v-for="row in chart.rows" :key="row.sku">
                <text x="0" :y="row.y + 9">{{ row.sku }}</text>
                <rect :x="CH.left" :y="row.y" :width="row.cur" height="6" rx="1" class="bar bar--current" />
                <rect :x="CH.left" :y="row.y + 7" :width="row.fc" height="6" rx="1" class="bar bar--forecast">
                  <title>{{ row.label }}</title>
                </rect>
              </g>
            </svg>
          </div>
        </section>

        <section class="section">
          <div class="section-label">
            <span>{{ t('restocking.submitted') }}</span>
            <span class="aside mono">{{ submitted.length }}</span>
          </div>
          <div v-if="submitted.length === 0" class="empty">{{ t('orders.submitted.empty') }}</div>
          <div v-for="order in submitted" :key="order.id" class="order">
            <div class="order-top">
              <span class="order-id">{{ t('restocking.orderNo', { id: order.id }) }}</span>
              <span :class="['tag', inTransit(order) ? 'tag--warn' : 'tag--ok']">
                {{ inTransit(order) ? t('restocking.inTransit') : t('status.delivered') }}
              </span>
            </div>
            <dl class="order-grid">
              <dt>{{ t('orders.submitted.submittedOn') }}</dt>
              <dd>{{ formatDate(order.created_at) }}</dd>
              <dt>{{ t('orders.submitted.lines') }}</dt>
              <dd>{{ order.items.length }}</dd>
              <dt>{{ t('restocking.total') }}</dt>
              <dd>{{ money(order.total_cost) }}</dd>
              <dt>{{ t('restocking.leadTime') }}</dt>
              <dd>{{ t('restocking.days', { count: order.lead_time_days }) }}</dd>
              <dt>{{ t('restocking.expected') }}</dt>
              <dd>{{ formatDate(order.expected_delivery) }}</dd>
            </dl>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 296px;
  gap: 16px;
  align-items: start;
}

.inspector {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.inspector .section {
  margin-bottom: 0;
}

.plan-head {
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
}

.plan-title .aside {
  margin-left: 6px;
}

.budget {
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
}

.budget label {
  margin-right: 2px;
}

.range-end {
  font-size: 11px;
  color: var(--ink-3);
}

.budget .range {
  width: 200px;
  background: linear-gradient(to right, var(--signal) var(--fill), var(--rule) var(--fill)) center / 100% 4px no-repeat;
}

.budget-num {
  width: 96px;
  text-align: right;
}

.ledger {
  font-size: 12.5px;
}

.ledger th,
.ledger td {
  padding: 0 8px;
  height: 36px;
  white-space: nowrap;
  vertical-align: middle;
}

.ledger th {
  height: 32px;
}

.c-check {
  width: 36px;
}

.item {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qty {
  width: 68px;
  min-height: 26px;
  height: 26px;
  padding: 0 8px;
  text-align: right;
}

.is-off td:not(.c-check) {
  color: var(--ink-3);
}

.foot-label {
  text-align: right;
  font-family: inherit;
}

.foot-sub td {
  color: var(--ink-3);
  font-weight: 400;
}

.over {
  color: var(--bad);
}

.panel-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 10px 14px;
  border-top: 1px solid var(--rule);
}

.foot-hint {
  margin-right: auto;
  font-size: 12px;
}

.confirm {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ok);
  font-weight: 500;
}

.confirm a {
  font-weight: 400;
}

.summary .stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin: 0;
  border: 0;
}

.summary .stat {
  margin: 0;
  padding: 10px 12px;
  border-left: 0;
  border-top: 1px solid var(--rule);
}

.summary .stat:nth-child(odd) {
  border-right: 1px solid var(--rule);
}

.summary .stat-value {
  font-size: 17px;
  text-align: right;
}

.meter-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 12px 6px;
  border-top: 1px solid var(--rule);
  font-size: 11px;
  color: var(--ink-3);
}

.meter-row .mono {
  color: var(--ink);
}

.meter {
  height: 4px;
  margin: 0 12px 12px;
  border-radius: 2px;
  background: var(--rule);
  overflow: hidden;
}

.meter i {
  display: block;
  height: 100%;
  background: var(--signal);
  transition: width 150ms ease-out;
}

.meter i.over {
  background: var(--bad);
}

.legend {
  display: flex;
  gap: 14px;
  padding: 8px 12px 0;
  font-size: 11px;
  color: var(--ink-3);
}

.sw {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 5px;
  border-radius: 2px;
}

.sw--current,
.bar--current {
  background: var(--rule);
  fill: var(--rule);
}

.sw--forecast,
.bar--forecast {
  background: var(--signal);
  fill: var(--signal);
}

.chart-wrap {
  padding: 8px 12px 10px;
}

.chart {
  display: block;
  width: 100%;
  height: auto;
}

.chart text {
  font-family: var(--font-mono);
  font-size: 10px;
  fill: var(--ink-3);
}

.chart .grid {
  stroke: var(--rule);
  stroke-width: 1;
}

.order {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-top: 1px solid var(--rule);
}

.order-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.order-id {
  font-weight: 600;
}

.order-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px 12px;
  font-size: 12px;
}

.order-grid dt {
  color: var(--ink-3);
}

.order-grid dd {
  margin: 0;
  text-align: right;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

@media (max-width: 1280px) {
  .workspace {
    grid-template-columns: minmax(0, 1fr);
  }
  .inspector {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    align-items: start;
  }
}

@media (max-width: 1120px) {
  .inspector {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .meter i {
    transition: none;
  }
}
</style>
