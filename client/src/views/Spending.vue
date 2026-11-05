<template>
  <div class="spending">
    <div class="page-head">
      <h2>{{ t('finance.title') }}</h2>
      <p>{{ t('finance.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats">
        <div class="stat">
          <span class="stat-label">{{ t('finance.totalRevenue') }}</span>
          <span class="stat-value">{{ formatCurrency(revenueMetrics.totalRevenue) }}</span>
          <span class="stat-note">{{ t('finance.fromOrders', { count: revenueMetrics.orderCount }) }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">{{ t('finance.totalCosts') }}</span>
          <span class="stat-value">{{ formatCurrency(totalCosts) }}</span>
          <span class="stat-note">{{ t('finance.costBreakdown') }}</span>
        </div>
        <div class="stat" :class="netProfit >= 0 ? 'is-ok' : 'is-bad'">
          <span class="stat-label">{{ t('finance.netProfit') }}</span>
          <span class="stat-value">{{ formatCurrency(netProfit) }}</span>
          <span class="stat-note">{{ profitMargin }}% {{ t('finance.margin') }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">{{ t('finance.avgOrderValue') }}</span>
          <span class="stat-value">{{ formatCurrency(revenueMetrics.avgOrderValue) }}</span>
          <span class="stat-note">{{ t('finance.perOrderRevenue') }}</span>
        </div>
      </div>

      <section class="section">
        <h3 class="section-label">
          <span>{{ t('finance.revenueVsCosts.title') }}</span>
          <span class="legend aside">
            <span class="legend-item"><span class="swatch" style="background: var(--chart-1)"></span>{{ t('finance.revenueVsCosts.revenue') }}</span>
            <span class="legend-item"><span class="swatch" style="background: var(--chart-2)"></span>{{ t('finance.revenueVsCosts.costs') }}</span>
          </span>
        </h3>
        <svg :viewBox="`0 0 ${CH.W} ${CH.H}`" class="chart" role="img" :aria-label="t('finance.revenueVsCosts.title')">
          <g v-for="tick in revenueChart.ticks" :key="tick.key">
            <line :x1="CH.L" :x2="CH.W - CH.R" :y1="tick.y" :y2="tick.y" class="grid" />
            <text :x="CH.L - 8" :y="tick.y + 4" text-anchor="end" class="axis-text">{{ tick.label }}</text>
          </g>
          <g v-for="bar in revenueChart.bars" :key="bar.month" class="bar-group">
            <rect :x="bar.revX" :y="bar.revY" :width="CH.BAR" :height="bar.revH" rx="2" class="mark" style="fill: var(--chart-1)">
              <title>{{ bar.revTitle }}</title>
            </rect>
            <rect :x="bar.costX" :y="bar.costY" :width="CH.BAR" :height="bar.costH" rx="2" class="mark" style="fill: var(--chart-2)">
              <title>{{ bar.costTitle }}</title>
            </rect>
            <text :x="bar.cx" :y="CH.H - 8" text-anchor="middle" class="axis-text">{{ bar.label }}</text>
          </g>
          <line :x1="CH.L" :x2="CH.W - CH.R" :y1="CH.T + CH.PLOT_H" :y2="CH.T + CH.PLOT_H" class="baseline" />
        </svg>
      </section>

      <section class="section">
        <h3 class="section-label">
          <span>{{ t('finance.monthlyCostFlow.title') }}</span>
          <span class="legend aside">
            <span class="legend-item"><span class="swatch" style="background: var(--chart-1)"></span>{{ t('finance.monthlyCostFlow.procurement') }}</span>
            <span class="legend-item"><span class="swatch" style="background: var(--chart-2)"></span>{{ t('finance.monthlyCostFlow.operational') }}</span>
            <span class="legend-item"><span class="swatch" style="background: var(--chart-3)"></span>{{ t('finance.monthlyCostFlow.labor') }}</span>
            <span class="legend-item"><span class="swatch" style="background: var(--chart-4)"></span>{{ t('finance.monthlyCostFlow.overhead') }}</span>
          </span>
        </h3>
        <svg :viewBox="`0 0 ${CH.W} ${CH.H}`" class="chart" role="img" :aria-label="t('finance.monthlyCostFlow.title')">
          <g v-for="tick in costChart.ticks" :key="tick.key">
            <line :x1="CH.L" :x2="CH.W - CH.R" :y1="tick.y" :y2="tick.y" class="grid" />
            <text :x="CH.L - 8" :y="tick.y + 4" text-anchor="end" class="axis-text">{{ tick.label }}</text>
          </g>
          <g
            v-for="bar in costChart.bars"
            :key="bar.month"
            class="bar-group is-clickable"
            tabindex="0"
            role="button"
            :aria-label="bar.label"
            @click="showCostDetail(bar.data)"
            @keydown.enter="showCostDetail(bar.data)"
          >
            <rect :x="bar.x - 8" :y="CH.T" :width="CH.STACK_BAR + 16" :height="CH.PLOT_H" class="hit" />
            <rect
              v-for="seg in bar.segments"
              :key="seg.key"
              :x="bar.x"
              :y="seg.y"
              :width="CH.STACK_BAR"
              :height="seg.h"
              class="mark"
              :style="{ fill: `var(--chart-${seg.index})` }"
            >
              <title>{{ seg.title }}</title>
            </rect>
            <text :x="bar.x + CH.STACK_BAR / 2" :y="CH.H - 8" text-anchor="middle" class="axis-text">{{ bar.label }}</text>
          </g>
          <line :x1="CH.L" :x2="CH.W - CH.R" :y1="CH.T + CH.PLOT_H" :y2="CH.T + CH.PLOT_H" class="baseline" />
        </svg>
      </section>

      <div class="two-col">
        <section class="section">
          <h3 class="section-label">{{ t('finance.categorySpending.title') }}</h3>
          <ul class="category-list">
            <li v-for="category in categorySpending" :key="category.category" class="category-item">
              <div class="category-info">
                <span class="category-name">{{ translateCategory(category.category) }}</span>
                <span class="mono">{{ currencySymbol }}{{ category.amount.toLocaleString() }}</span>
              </div>
              <div class="track"><div class="fill" :style="{ width: category.percentage + '%' }"></div></div>
              <div class="category-meta muted">
                <span>{{ category.percentage }}% {{ t('finance.categorySpending.ofTotal') }}</span>
                <span class="mono" :class="{ up: category.change > 0, down: category.change < 0 }">
                  {{ category.change > 0 ? '+' : '' }}{{ category.change }}%
                </span>
              </div>
            </li>
          </ul>
        </section>

        <section class="section">
          <h3 class="section-label">{{ t('finance.transactions.title') }}</h3>
          <div class="ledger-wrap is-scroll">
            <table class="ledger">
              <thead>
                <tr>
                  <th>{{ t('finance.transactions.id') }}</th>
                  <th>{{ t('finance.transactions.description') }}</th>
                  <th>{{ t('finance.transactions.vendor') }}</th>
                  <th>{{ t('finance.transactions.date') }}</th>
                  <th class="num">{{ t('finance.transactions.amount') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="transaction in recentTransactions"
                  :key="transaction.id"
                  class="is-clickable"
                  tabindex="0"
                  @click="handleTransactionClick(transaction)"
                  @keydown.enter="handleTransactionClick(transaction)"
                >
                  <td class="mono muted">{{ transaction.id.toString().padStart(3, '0') }}</td>
                  <td>{{ transaction.description }}</td>
                  <td class="muted">{{ transaction.vendor }}</td>
                  <td class="mono muted">{{ formatDateShort(transaction.date) }}</td>
                  <td class="num">{{ currencySymbol }}{{ transaction.amount.toLocaleString() }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>

    <CostDetailModal
      :is-open="showCostModal"
      :cost-data="selectedCostData"
      @close="showCostModal = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyUtil } from '../utils/currency'
import CostDetailModal from '../components/CostDetailModal.vue'

export default {
  name: 'Spending',
  components: {
    CostDetailModal
  },
  setup() {
    const { t, currentCurrency } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allMonthlySpending = ref([])
    const allCategorySpending = ref([])
    const allTransactions = ref([])
    const summaryData = ref({})
    const allOrders = ref([])

    // Modal state
    const showCostModal = ref(false)
    const selectedCostData = ref(null)

    // Use shared filters
    const { selectedPeriod, getCurrentFilters } = useFilters()

    // Monthly spending chart always shows all months (not filtered)
    const monthlySpending = computed(() => {
      return allMonthlySpending.value
    })

    // Filtered monthly spending for summary calculations only
    const filteredMonthlySpending = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allMonthlySpending.value
      }

      // Extract month name from YYYY-MM format
      const monthMap = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
      }
      const selectedMonth = monthMap[selectedPeriod.value.split('-')[1]]
      return allMonthlySpending.value.filter(m => m.month === selectedMonth)
    })

    const categorySpending = computed(() => {
      return allCategorySpending.value
    })

    const recentTransactions = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allTransactions.value
      }
      // Filter transactions by selected month
      return allTransactions.value.filter(t => {
        const transactionMonth = new Date(t.date).toISOString().slice(0, 7)
        return transactionMonth === selectedPeriod.value
      })
    })

    const summary = computed(() => {
      // Recalculate summary based on filteredMonthlySpending (not the chart data)
      if (filteredMonthlySpending.value.length === 0) {
        return summaryData.value
      }

      const totals = filteredMonthlySpending.value.reduce((acc, month) => ({
        procurement: acc.procurement + month.procurement,
        operational: acc.operational + month.operational,
        labor: acc.labor + month.labor,
        overhead: acc.overhead + month.overhead
      }), { procurement: 0, operational: 0, labor: 0, overhead: 0 })

      return {
        total_procurement_cost: totals.procurement,
        total_operational_cost: totals.operational,
        total_labor_cost: totals.labor,
        total_overhead: totals.overhead,
        procurement_change: summaryData.value.procurement_change || 0,
        operational_change: summaryData.value.operational_change || 0,
        labor_change: summaryData.value.labor_change || 0,
        overhead_change: summaryData.value.overhead_change || 0
      }
    })

    // Filtered orders based on selected period
    const filteredOrders = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allOrders.value
      }

      // Filter orders by selected month
      return allOrders.value.filter(order => {
        const orderMonth = new Date(order.order_date).toISOString().slice(0, 7)
        return orderMonth === selectedPeriod.value
      })
    })

    // Revenue metrics from filtered orders
    const revenueMetrics = computed(() => {
      const totalRevenue = filteredOrders.value.reduce((sum, order) => sum + (order.total_value || 0), 0)
      const orderCount = filteredOrders.value.length
      const avgOrderValue = orderCount > 0 ? totalRevenue / orderCount : 0

      return {
        totalRevenue,
        orderCount,
        avgOrderValue,
        revenueGrowth: 15.3 // Placeholder - could calculate from historical data
      }
    })

    // Total costs from summary
    const totalCosts = computed(() => {
      return summary.value.total_procurement_cost +
             summary.value.total_operational_cost +
             summary.value.total_labor_cost +
             summary.value.total_overhead
    })

    // Net profit
    const netProfit = computed(() => {
      return revenueMetrics.value.totalRevenue - totalCosts.value
    })

    // Profit margin percentage
    const profitMargin = computed(() => {
      if (revenueMetrics.value.totalRevenue === 0) return 0
      return ((netProfit.value / revenueMetrics.value.totalRevenue) * 100).toFixed(1)
    })

    // Monthly revenue data for chart
    const monthlyRevenue = computed(() => {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

      // Initialize all months
      const revenueByMonth = monthNames.map(month => ({
        month,
        revenue: 0,
        costs: 0
      }))

      // Calculate revenue from orders
      allOrders.value.forEach(order => {
        const orderDate = new Date(order.order_date)
        const monthIndex = orderDate.getMonth()
        if (monthIndex >= 0 && monthIndex < 12) {
          revenueByMonth[monthIndex].revenue += order.total_value || 0
        }
      })

      // Add costs from spending data
      allMonthlySpending.value.forEach(spending => {
        const monthIndex = monthNames.indexOf(spending.month)
        if (monthIndex >= 0) {
          revenueByMonth[monthIndex].costs = spending.procurement + spending.operational + spending.labor + spending.overhead
        }
      })

      return revenueByMonth
    })

    // Max value for chart scaling
    const maxRevenueValue = computed(() => {
      const maxRevenue = Math.max(...monthlyRevenue.value.map(m => m.revenue))
      const maxCost = Math.max(...monthlyRevenue.value.map(m => m.costs))
      const max = Math.max(maxRevenue, maxCost)
      return Math.ceil(max / 1000) // Return in K
    })

    const loadData = async () => {
      try {
        loading.value = true
        const [summaryRes, monthlyRes, categoryRes, transactionsRes, ordersRes] = await Promise.all([
          api.getSpendingSummary(),
          api.getMonthlySpending(),
          api.getCategorySpending(),
          api.getTransactions(),
          api.getOrders()
        ])

        summaryData.value = summaryRes
        allMonthlySpending.value = monthlyRes
        allCategorySpending.value = categoryRes
        allTransactions.value = transactionsRes
        allOrders.value = ordersRes
      } catch (err) {
        error.value = 'Failed to load financial data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for period filter changes
    watch([selectedPeriod], () => {
      // Data will automatically update via computed properties
    })

    const formatCurrency = (value) => {
      return formatCurrencyUtil(value, currentCurrency.value)
    }

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    }

    const formatDateShort = (dateString) => {
      const date = new Date(dateString)
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      const year = date.getFullYear().toString().slice(-2)
      return `${month}/${day}/${year}`
    }

    const translateMonth = (month) => {
      const monthMap = {
        'Jan': t('months.jan'),
        'Feb': t('months.feb'),
        'Mar': t('months.mar'),
        'Apr': t('months.apr'),
        'May': t('months.may'),
        'Jun': t('months.jun'),
        'Jul': t('months.jul'),
        'Aug': t('months.aug'),
        'Sep': t('months.sep'),
        'Oct': t('months.oct'),
        'Nov': t('months.nov'),
        'Dec': t('months.dec')
      }
      return monthMap[month] || month
    }

    const translateCategory = (category) => {
      // First try spending categories
      const spendingCategoryMap = {
        'Raw Materials': t('spendingCategories.rawMaterials'),
        'Components': t('spendingCategories.components'),
        'Equipment': t('spendingCategories.equipment'),
        'Consumables': t('spendingCategories.consumables')
      }

      // Then try product categories
      const productCategoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }

      return spendingCategoryMap[category] || productCategoryMap[category] || category
    }

    // Chart geometry (SVG user units)
    const W = 960, H = 300, L = 56, R = 8, T = 8, B = 28
    const PLOT_W = W - L - R
    const PLOT_H = H - T - B
    const GAP = 2
    const BAR = 22
    const STACK_BAR = 24

    const makeTicks = (max, steps, label) => {
      const out = []
      for (let k = 0; k <= steps; k++) {
        out.push({ key: k, y: T + PLOT_H - (PLOT_H * k) / steps, label: label((max * k) / steps) })
      }
      return out
    }

    const revenueChart = computed(() => {
      const max = Math.max(maxRevenueValue.value, 1) * 1000
      const n = monthlyRevenue.value.length || 1
      const slot = PLOT_W / n
      const sym = currencySymbol.value
      const bars = monthlyRevenue.value.map((m, i) => {
        const cx = L + slot * i + slot / 2
        const revH = (m.revenue / max) * PLOT_H
        const costH = (m.costs / max) * PLOT_H
        return {
          month: m.month,
          label: translateMonth(m.month),
          cx,
          revX: cx - BAR - GAP / 2,
          costX: cx + GAP / 2,
          revY: T + PLOT_H - revH,
          revH,
          costY: T + PLOT_H - costH,
          costH,
          revTitle: `${t('finance.revenueVsCosts.revenue')}: ${sym}${m.revenue.toLocaleString()}`,
          costTitle: `${t('finance.revenueVsCosts.costs')}: ${sym}${m.costs.toLocaleString()}`
        }
      })
      return {
        ticks: makeTicks(max, 4, (v) => (v === 0 ? `${sym}0` : `${sym}${Math.round(v / 1000)}K`)),
        bars
      }
    })

    const COST_KEYS = ['procurement', 'operational', 'labor', 'overhead']

    const costChart = computed(() => {
      const sym = currencySymbol.value
      const peak = Math.max(0, ...monthlySpending.value.map(m => COST_KEYS.reduce((s, k) => s + m[k], 0)))
      const max = Math.max(25000, Math.ceil(peak / 5000) * 5000)
      const n = monthlySpending.value.length || 1
      const slot = PLOT_W / n
      const bars = monthlySpending.value.map((m, i) => {
        const cx = L + slot * i + slot / 2
        let base = 0
        const segments = COST_KEYS.map((key, idx) => {
          const raw = (m[key] / max) * PLOT_H
          const y = T + PLOT_H - base - raw
          base += raw
          return {
            key,
            index: idx + 1,
            y: y + (raw > GAP ? GAP : 0),
            h: raw > GAP ? raw - GAP : raw,
            title: `${t('finance.monthlyCostFlow.' + key)}: ${sym}${m[key].toLocaleString()}`
          }
        })
        return { month: m.month, label: translateMonth(m.month), x: cx - STACK_BAR / 2, segments, data: m }
      })
      return {
        ticks: makeTicks(max, max / 5000, (v) => (v === 0 ? `${sym}0` : `${sym}${v / 1000}K`)),
        bars
      }
    })

    const handleTransactionClick = (transaction) => {
      console.log('Transaction clicked:', transaction)
      alert(`Transaction Details:\n\nID: ${transaction.id}\nDescription: ${transaction.description}\nVendor: ${transaction.vendor}\nDate: ${formatDateShort(transaction.date)}\nAmount: $${transaction.amount.toLocaleString()}`)
    }

    const showCostDetail = (monthData) => {
      selectedCostData.value = monthData
      showCostModal.value = true
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      summary,
      monthlySpending,
      categorySpending,
      recentTransactions,
      revenueMetrics,
      totalCosts,
      netProfit,
      profitMargin,
      monthlyRevenue,
      maxRevenueValue,
      formatCurrency,
      currencySymbol,
      revenueChart,
      costChart,
      CH: { W, H, L, R, T, B, PLOT_W, PLOT_H, BAR, STACK_BAR },
      formatDate,
      formatDateShort,
      translateMonth,
      translateCategory,
      handleTransactionClick,
      showCostModal,
      selectedCostData,
      showCostDetail,
      Math
    }
  }
}
</script>

<style scoped>
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-4);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: var(--s-2);
}

.swatch {
  width: 10px;
  height: 10px;
  border-radius: var(--radius);
}

.chart {
  display: block;
  width: 100%;
  height: auto;
}

.grid {
  stroke: var(--rule);
  stroke-width: 1;
}

.baseline {
  stroke: var(--ink);
  stroke-width: 1;
}

.axis-text {
  fill: var(--ink-3);
  font-family: var(--font-mono);
  font-size: 11px;
}

.hit {
  fill: transparent;
}

.bar-group.is-clickable {
  cursor: pointer;
  outline: none;
}

.bar-group.is-clickable:focus-visible .hit {
  stroke: var(--signal);
  stroke-width: 2;
}

@media (hover: hover) and (pointer: fine) {
  .bar-group.is-clickable:hover .hit {
    fill: var(--paper-sunk);
  }
}

.two-col {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(28rem, 100%), 1fr));
  gap: var(--s-6);
}

.category-list {
  list-style: none;
}

.category-item {
  padding: var(--s-3) 0;
  border-bottom: var(--hair);
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: var(--fs-table);
}

.category-name {
  font-weight: 600;
}

.track {
  height: 6px;
  margin: var(--s-2) 0;
  background: var(--paper-sunk);
  border-radius: var(--radius);
  overflow: hidden;
}

.fill {
  height: 100%;
  background: var(--chart-1);
}

.category-meta {
  display: flex;
  justify-content: space-between;
  font-size: var(--fs-sm);
}

.up {
  color: var(--ok);
}

.down {
  color: var(--bad);
}

.ledger tr:focus-visible {
  outline: 2px solid var(--signal);
  outline-offset: -2px;
}
</style>
