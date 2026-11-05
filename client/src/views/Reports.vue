<template>
  <div class="reports">
    <div class="page-head">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('reports.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="!quarterlyData.length && !monthlyData.length" class="empty">{{ t('reports.empty') }}</div>
    <div v-else>
      <div class="stats">
        <div class="stat">
          <span class="stat-label">{{ t('reports.stats.totalRevenue') }}</span>
          <span class="stat-value">{{ formatCurrency(totalRevenue, currentCurrency) }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</span>
          <span class="stat-value">{{ formatCurrency(avgMonthlyRevenue, currentCurrency) }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">{{ t('reports.stats.totalOrders') }}</span>
          <span class="stat-value">{{ totalOrders.toLocaleString('en-US') }}</span>
        </div>
        <div class="stat is-signal">
          <span class="stat-label">{{ t('reports.stats.bestQuarter') }}</span>
          <span class="stat-value">{{ bestQuarter || t('reports.notAvailable') }}</span>
        </div>
      </div>

      <!-- Quarterly Performance -->
      <div class="section">
        <div class="section-label">
          <span>{{ t('reports.quarterly.title') }}</span>
        </div>
        <div class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>{{ t('reports.quarterly.quarter') }}</th>
                <th class="num">{{ t('reports.quarterly.totalOrders') }}</th>
                <th class="num">{{ t('reports.quarterly.totalRevenue') }}</th>
                <th class="num">{{ t('reports.quarterly.avgOrderValue') }}</th>
                <th>{{ t('reports.quarterly.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td class="strong">{{ q.quarter }}</td>
                <td class="num">{{ q.total_orders.toLocaleString('en-US') }}</td>
                <td class="num">{{ formatCurrency(q.total_revenue, currentCurrency) }}</td>
                <td class="num">{{ formatCurrencyWithDecimals(q.avg_order_value, currentCurrency, 2) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">{{ q.fulfillment_rate }}%</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="section">
        <div class="section-label">
          <span>{{ t('reports.trend.title') }}</span>
        </div>
        <div class="chart">
          <svg
            :viewBox="`0 0 ${chart.width} ${chart.height}`"
            class="chart-svg"
            role="img"
            :aria-label="t('reports.trend.title')"
          >
            <line
              :x1="chart.left"
              :x2="chart.width - chart.right"
              :y1="chart.baseline"
              :y2="chart.baseline"
              class="grid-line base-line"
            />
            <g v-for="tick in chart.ticks" :key="tick.value">
              <line
                :x1="chart.left"
                :x2="chart.width - chart.right"
                :y1="tick.y"
                :y2="tick.y"
                class="grid-line"
              />
              <text :x="chart.left - 8" :y="tick.y" class="axis-text" text-anchor="end" dominant-baseline="middle">
                {{ formatCurrency(tick.value, currentCurrency) }}
              </text>
            </g>
            <g v-for="bar in chart.bars" :key="bar.month">
              <rect :x="bar.x" :y="bar.y" :width="bar.w" :height="bar.h" rx="2" class="bar">
                <title>{{ formatCurrency(bar.revenue, currentCurrency) }}</title>
              </rect>
              <text :x="bar.x + bar.w / 2" :y="chart.height - chart.bottom + 16" class="axis-text" text-anchor="middle">
                {{ formatMonth(bar.month, true) }}
              </text>
            </g>
          </svg>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="section">
        <div class="section-label">
          <span>{{ t('reports.mom.title') }}</span>
        </div>
        <div class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>{{ t('reports.mom.month') }}</th>
                <th class="num">{{ t('reports.mom.orders') }}</th>
                <th class="num">{{ t('reports.mom.revenue') }}</th>
                <th class="num">{{ t('reports.mom.change') }}</th>
                <th class="num">{{ t('reports.mom.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <td class="strong">{{ formatMonth(month.month) }}</td>
                <td class="num">{{ month.order_count.toLocaleString('en-US') }}</td>
                <td class="num">{{ formatCurrency(month.revenue, currentCurrency) }}</td>
                <td class="num">
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getChangeValue(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else class="muted">{{ t('reports.none') }}</span>
                </td>
                <td class="num">
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getGrowthRate(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else class="muted">{{ t('reports.none') }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Reports',
  setup() {
    const { t, currentCurrency, currentLocale } = useI18n()
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])
        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        error.value = t('reports.loadError')
      } finally {
        loading.value = false
      }
    }

    onMounted(loadData)

    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.revenue, 0)
    )
    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.order_count, 0)
    )
    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length ? totalRevenue.value / monthlyData.value.length : 0
    )
    const maxRevenue = computed(() =>
      Math.max(0, ...monthlyData.value.map(m => m.revenue))
    )
    const bestQuarter = computed(() => {
      let best = null
      for (const q of quarterlyData.value) {
        if (!best || q.total_revenue > best.total_revenue) best = q
      }
      return best && best.total_revenue > 0 ? best.quarter : ''
    })

    // short = month only, for chart axis labels
    const formatMonth = (monthStr, short = false) => {
      const [year, month] = monthStr.split('-').map(Number)
      const date = new Date(year, month - 1, 1)
      if (isNaN(date.getTime())) return monthStr
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, short ? { month: 'short' } : { month: 'short', year: 'numeric' })
    }

    // Round the axis top up to 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8 or 10 x a power of ten
    const niceMax = (max) => {
      if (max <= 0) return 1
      const pow = Math.pow(10, Math.floor(Math.log10(max)))
      const step = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].find(s => s * pow >= max)
      return step * pow
    }

    const chart = computed(() => {
      const width = 1100
      const height = 300
      const left = 96
      const right = 16
      const top = 12
      const bottom = 28
      const plotW = width - left - right
      const plotH = height - top - bottom
      const axisMax = niceMax(maxRevenue.value)
      const yOf = (v) => top + plotH - (v / axisMax) * plotH

      const ticks = [1, 2, 3, 4].map(i => {
        const value = (axisMax / 4) * i
        return { value, y: yOf(value) }
      })

      const n = monthlyData.value.length
      const slot = n ? plotW / n : plotW
      const barW = Math.min(slot * 0.6, 56)
      const bars = monthlyData.value.map((m, i) => {
        const y = yOf(m.revenue)
        return {
          month: m.month,
          revenue: m.revenue,
          x: left + slot * i + (slot - barW) / 2,
          w: barW,
          y,
          h: top + plotH - y
        }
      })

      return { width, height, left, right, bottom, baseline: yOf(0), ticks, bars }
    })

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'tag tag--ok'
      if (rate >= 75) return 'tag tag--warn'
      return 'tag tag--bad'
    }

    const getChangeValue = (current, previous) => {
      const change = current - previous
      const formatted = formatCurrency(Math.abs(change), currentCurrency.value)
      if (change > 0) return '+' + formatted
      if (change < 0) return '-' + formatted
      return formatted
    }

    const getChangeClass = (current, previous) => {
      const change = current - previous
      if (change > 0) return 'change-up'
      if (change < 0) return 'change-down'
      return ''
    }

    const getGrowthRate = (current, previous) => {
      if (previous === 0) return t('reports.notAvailable')
      const rate = ((current - previous) / previous) * 100
      return (rate > 0 ? '+' : '') + rate.toFixed(1) + '%'
    }

    return {
      t,
      currentCurrency,
      loading,
      error,
      quarterlyData,
      monthlyData,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      formatCurrency,
      formatCurrencyWithDecimals,
      formatMonth,
      chart,
      getFulfillmentClass,
      getChangeValue,
      getChangeClass,
      getGrowthRate
    }
  }
}
</script>

<style scoped>
.strong {
  font-weight: 600;
}

.chart {
  padding-top: var(--s-2);
}

.chart-svg {
  display: block;
  width: 100%;
  height: auto;
}

.grid-line {
  stroke: var(--rule);
  stroke-width: 1;
}

.axis-text {
  fill: var(--ink-3);
  font-family: var(--font-mono);
  font-size: 11px;
}

.base-line {
  stroke: var(--rule-strong);
}

.bar {
  fill: var(--chart-1);
}

@media (hover: hover) and (pointer: fine) {
  .bar {
    transition: fill var(--dur-ui) ease;
  }
  .bar:hover {
    fill: color-mix(in srgb, var(--chart-1) 82%, var(--ink));
  }
}

.change-up {
  color: var(--ok);
}

.change-down {
  color: var(--bad);
}
</style>
