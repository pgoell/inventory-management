<template>
  <div class="reports">
    <div class="page-head">
      <h2>Performance Reports</h2>
      <p>View quarterly performance metrics and monthly trends</p>
    </div>

    <div v-if="loading" class="loading">Loading reports...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats">
        <div class="stat">
          <span class="stat-label">Total Revenue (YTD)</span>
          <span class="stat-value">${{ formatNumber(totalRevenue) }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Avg Monthly Revenue</span>
          <span class="stat-value">${{ formatNumber(avgMonthlyRevenue) }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Total Orders (YTD)</span>
          <span class="stat-value">{{ totalOrders }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Best Performing Quarter</span>
          <span class="stat-value">{{ bestQuarter }}</span>
        </div>
      </div>

      <section class="section">
        <h3 class="section-label">Quarterly Performance</h3>
        <div class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>Quarter</th>
                <th class="num">Total Orders</th>
                <th class="num">Total Revenue</th>
                <th class="num">Avg Order Value</th>
                <th class="num">Fulfillment Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td class="num">{{ q.total_orders }}</td>
                <td class="num">${{ formatNumber(q.total_revenue) }}</td>
                <td class="num">${{ formatNumber(q.avg_order_value) }}</td>
                <td class="num">
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="section">
        <h3 class="section-label">Monthly Revenue Trend</h3>
        <svg :viewBox="`0 0 ${chart.W} ${chart.H}`" class="chart" role="img" aria-label="Monthly Revenue Trend">
          <g v-for="tick in chart.ticks" :key="tick.key">
            <line :x1="chart.L" :x2="chart.W - chart.R" :y1="tick.y" :y2="tick.y" class="grid" />
            <text :x="chart.L - 8" :y="tick.y + 4" text-anchor="end" class="axis-text">{{ tick.label }}</text>
          </g>
          <g v-for="bar in chart.bars" :key="bar.month" class="bar-group">
            <rect :x="bar.x" :y="bar.y" width="24" :height="bar.h" rx="2" class="mark">
              <title>{{ bar.title }}</title>
            </rect>
            <text :x="bar.cx" :y="chart.H - 8" text-anchor="middle" class="axis-text">{{ bar.label }}</text>
          </g>
          <line :x1="chart.L" :x2="chart.W - chart.R" :y1="chart.T + chart.plotH" :y2="chart.T + chart.plotH" class="baseline" />
        </svg>
      </section>

      <section class="section">
        <h3 class="section-label">Month-over-Month Analysis</h3>
        <div class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>Month</th>
                <th class="num">Orders</th>
                <th class="num">Revenue</th>
                <th class="num">Change</th>
                <th class="num">Growth Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td class="num">{{ month.order_count }}</td>
                <td class="num">${{ formatNumber(month.revenue) }}</td>
                <td class="num">
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getChangeValue(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else class="muted">-</span>
                </td>
                <td class="num">
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getGrowthRate(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else class="muted">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { API_BASE_URL } from '../api'

export default {
  name: 'Reports',
  data() {
    return {
      loading: true,
      error: null,
      quarterlyData: [],
      monthlyData: [],
      totalRevenue: 0,
      avgMonthlyRevenue: 0,
      totalOrders: 0,
      bestQuarter: ''
    }
  },
  mounted() {
    console.log('Reports component mounted')
    this.loadData()
  },
  computed: {
    chart() {
      var W = 960, H = 300, L = 56, R = 8, T = 8, B = 28
      var plotW = W - L - R
      var plotH = H - T - B
      var n = this.monthlyData.length || 1
      var slot = plotW / n
      var peak = 0
      for (var i = 0; i < this.monthlyData.length; i++) {
        if (this.monthlyData[i].revenue > peak) peak = this.monthlyData[i].revenue
      }
      // round the axis top up to 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8 or 10 times a power of ten
      var mag = Math.pow(10, Math.floor(Math.log10(peak || 1)))
      var steps = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]
      var max = mag
      for (var s = 0; s < steps.length; s++) {
        max = steps[s] * mag
        if (max >= peak) break
      }
      var ticks = []
      for (var k = 0; k <= 4; k++) {
        var v = (max * k) / 4
        ticks.push({
          key: k,
          y: T + plotH - (plotH * k) / 4,
          label: v === 0 ? '$0' : v >= 1000 ? '$' + v / 1000 + 'K' : '$' + v
        })
      }
      var bars = this.monthlyData.map((m, idx) => {
        var h = (m.revenue / max) * plotH
        return {
          month: m.month,
          x: L + slot * idx + slot / 2 - 12,
          y: T + plotH - h,
          h: h,
          label: this.formatMonth(m.month),
          cx: L + slot * idx + slot / 2,
          title: '$' + this.formatNumber(m.revenue)
        }
      })
      return { W, H, L, R, T, plotH, ticks, bars }
    }
  },
  methods: {
    async loadData() {
      console.log('Loading reports data...')
      try {
        this.loading = true

        // Fetch quarterly data
        console.log('Fetching quarterly data...')
        const quarterlyResponse = await axios.get(`${API_BASE_URL}/reports/quarterly`)
        this.quarterlyData = quarterlyResponse.data
        console.log('Quarterly data:', this.quarterlyData)

        // Fetch monthly data
        console.log('Fetching monthly data...')
        const monthlyResponse = await axios.get(`${API_BASE_URL}/reports/monthly-trends`)
        this.monthlyData = monthlyResponse.data
        console.log('Monthly data:', this.monthlyData)

        // Calculate summary stats
        console.log('Calculating summary stats...')
        this.calculateSummaryStats()
        console.log('Summary stats calculated')

      } catch (err) {
        console.log('Error loading reports:', err)
        this.error = 'Failed to load reports: ' + err.message
      } finally {
        this.loading = false
        console.log('Loading complete')
      }
    },

    calculateSummaryStats() {
      // Calculate total revenue
      var total = 0
      for (var i = 0; i < this.monthlyData.length; i++) {
        total = total + this.monthlyData[i].revenue
      }
      this.totalRevenue = total

      // Calculate average monthly revenue
      if (this.monthlyData.length > 0) {
        this.avgMonthlyRevenue = total / this.monthlyData.length
      } else {
        this.avgMonthlyRevenue = 0
      }

      // Calculate total orders
      var orders = 0
      for (var i = 0; i < this.monthlyData.length; i++) {
        orders = orders + this.monthlyData[i].order_count
      }
      this.totalOrders = orders

      // Find best quarter
      var bestQ = ''
      var bestRevenue = 0
      for (var i = 0; i < this.quarterlyData.length; i++) {
        if (this.quarterlyData[i].total_revenue > bestRevenue) {
          bestRevenue = this.quarterlyData[i].total_revenue
          bestQ = this.quarterlyData[i].quarter
        }
      }
      this.bestQuarter = bestQ
    },

    formatNumber(num) {
      console.log('Formatting number:', num)
      // Format number with commas
      var str = num.toString()
      var parts = str.split('.')
      var intPart = parts[0]
      var decPart = parts.length > 1 ? parts[1] : '00'

      var formatted = ''
      var count = 0
      for (var i = intPart.length - 1; i >= 0; i--) {
        if (count > 0 && count % 3 === 0) {
          formatted = ',' + formatted
        }
        formatted = intPart[i] + formatted
        count++
      }

      if (decPart.length === 1) {
        decPart = decPart + '0'
      }
      if (decPart.length > 2) {
        decPart = decPart.substring(0, 2)
      }

      return formatted + '.' + decPart
    },

    formatMonth(monthStr) {
      console.log('Formatting month:', monthStr)
      // Convert YYYY-MM to readable format
      var parts = monthStr.split('-')
      var year = parts[0]
      var month = parts[1]

      var monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      var monthIndex = parseInt(month) - 1

      return monthNames[monthIndex] + ' ' + year
    },

    getFulfillmentClass(rate) {
      if (rate >= 90) {
        return 'tag tag--ok'
      } else if (rate >= 75) {
        return 'tag tag--warn'
      } else {
        return 'tag tag--bad'
      }
    },

    getChangeValue(current, previous) {
      var change = current - previous
      if (change > 0) {
        return '+$' + this.formatNumber(change)
      } else if (change < 0) {
        return '-$' + this.formatNumber(Math.abs(change))
      } else {
        return '$0.00'
      }
    },

    getChangeClass(current, previous) {
      var change = current - previous
      if (change > 0) {
        return 'up'
      } else if (change < 0) {
        return 'down'
      } else {
        return ''
      }
    },

    getGrowthRate(current, previous) {
      if (previous === 0) {
        return 'N/A'
      }

      var rate = ((current - previous) / previous) * 100
      var sign = rate > 0 ? '+' : ''

      return sign + rate.toFixed(1) + '%'
    }
  }
}
</script>

<style scoped>
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

.mark {
  fill: var(--chart-1);
}

@media (hover: hover) and (pointer: fine) {
  .bar-group:hover .mark {
    fill: var(--chart-2);
  }
}

.up {
  color: var(--ok);
}

.down {
  color: var(--bad);
}
</style>
