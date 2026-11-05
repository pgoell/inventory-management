<template>
  <div class="demand">
    <div class="page-head">
      <h2>{{ t('demand.title') }}</h2>
      <p>{{ t('demand.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats">
        <div class="stat is-ok">
          <span class="stat-label">{{ t('demand.increasingDemand') }}</span>
          <span class="stat-value">{{ getForecastsByTrend('increasing').length }}</span>
        </div>
        <div class="stat is-info">
          <span class="stat-label">{{ t('demand.stableDemand') }}</span>
          <span class="stat-value">{{ getForecastsByTrend('stable').length }}</span>
        </div>
        <div class="stat is-bad">
          <span class="stat-label">{{ t('demand.decreasingDemand') }}</span>
          <span class="stat-value">{{ getForecastsByTrend('decreasing').length }}</span>
        </div>
      </div>

      <div class="trend-cols">
        <div class="trend-col">
          <div class="section-label">
            <span>{{ t('demand.increasingDemand') }}</span>
            <span class="aside mono">{{ t('demand.itemsCount', { count: getForecastsByTrend('increasing').length }) }}</span>
          </div>
          <ul class="trend-list">
            <li v-for="item in getForecastsByTrend('increasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="num trend-increasing">+{{ getChangePercent(item) }}%</span>
            </li>
          </ul>
          <div v-if="getForecastsByTrend('increasing').length > 5" class="more-items muted">
            +{{ getForecastsByTrend('increasing').length - 5 }} {{ t('demand.more') }}
          </div>
        </div>
        <div class="trend-col">
          <div class="section-label">
            <span>{{ t('demand.stableDemand') }}</span>
            <span class="aside mono">{{ t('demand.itemsCount', { count: getForecastsByTrend('stable').length }) }}</span>
          </div>
          <ul class="trend-list">
            <li v-for="item in getForecastsByTrend('stable').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="num trend-stable">{{ getChangePercent(item) }}%</span>
            </li>
          </ul>
          <div v-if="getForecastsByTrend('stable').length > 5" class="more-items muted">
            +{{ getForecastsByTrend('stable').length - 5 }} {{ t('demand.more') }}
          </div>
        </div>
        <div class="trend-col">
          <div class="section-label">
            <span>{{ t('demand.decreasingDemand') }}</span>
            <span class="aside mono">{{ t('demand.itemsCount', { count: getForecastsByTrend('decreasing').length }) }}</span>
          </div>
          <ul class="trend-list">
            <li v-for="item in getForecastsByTrend('decreasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="num trend-decreasing">{{ getChangePercent(item) }}%</span>
            </li>
          </ul>
          <div v-if="getForecastsByTrend('decreasing').length > 5" class="more-items muted">
            +{{ getForecastsByTrend('decreasing').length - 5 }} {{ t('demand.more') }}
          </div>
        </div>
      </div>

      <section class="section">
        <div class="section-label">
          <span>{{ t('demand.demandForecasts') }}</span>
        </div>
        <div class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>{{ t('demand.table.sku') }}</th>
                <th>{{ t('demand.table.itemName') }}</th>
                <th class="num">{{ t('demand.table.currentDemand') }}</th>
                <th class="num">{{ t('demand.table.forecastedDemand') }}</th>
                <th class="num">{{ t('demand.table.change') }}</th>
                <th>{{ t('demand.table.trend') }}</th>
                <th>{{ t('demand.table.period') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="forecast in forecasts" :key="forecast.id">
                <td class="mono sku">{{ forecast.item_sku }}</td>
                <td>{{ forecast.item_name }}</td>
                <td class="num">{{ forecast.current_demand }}</td>
                <td class="num"><strong>{{ forecast.forecasted_demand }}</strong></td>
                <td class="num" :class="getChangeClass(forecast)">{{ getChangePercent(forecast) }}%</td>
                <td>
                  <span :class="['tag', trendTag[forecast.trend]]">
                    {{ t(`trends.${forecast.trend}`) }}
                  </span>
                </td>
                <td>{{ translatePeriod(forecast.period) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Demand',
  setup() {
    const { t } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Filter forecasts based on inventory filters
    const forecasts = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allForecasts.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allForecasts.value.filter(f => validSkus.has(f.item_sku))
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadForecasts()
    })

    const getForecastsByTrend = (trend) => {
      return forecasts.value.filter(f => f.trend === trend)
    }

    const getChangePercent = (forecast) => {
      const change = ((forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand * 100).toFixed(1)
      return change > 0 ? `+${change}` : change
    }

    const trendTag = { increasing: 'tag--ok', decreasing: 'tag--bad', stable: 'tag--info' }

    // Within +/-2% counts as stable
    const getChangeClass = (forecast) => {
      const change = forecast.forecasted_demand - forecast.current_demand
      const changePercent = Math.abs((change / forecast.current_demand) * 100)
      if (changePercent <= 2) return 'change-stable'
      return change > 0 ? 'change-up' : 'change-down'
    }

    const translatePeriod = (period) => {
      // Period values like "Next 3 months", "Q1 2025", "30 days", etc.
      const { currentLocale } = useI18n()
      if (currentLocale.value === 'ja') {
        return period
          .replace(/Next\s+/i, '次の')
          .replace(/\s+months/i, 'か月')
          .replace(/\s+month/i, 'か月')
          .replace(/\s+days/i, '日間')
          .replace(/\s+day/i, '日')
          .replace('Q1', '第1四半期')
          .replace('Q2', '第2四半期')
          .replace('Q3', '第3四半期')
          .replace('Q4', '第4四半期')
      }
      return period
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      forecasts,
      getForecastsByTrend,
      getChangePercent,
      getChangeClass,
      trendTag,
      translatePeriod
    }
  }
}
</script>

<style scoped>
.sku {
  font-weight: 600;
}

.trend-cols {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
  gap: var(--s-6);
  margin-bottom: var(--s-7);
}

.trend-list {
  list-style: none;
}

.trend-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--s-4);
  padding: 6px 0;
  border-bottom: var(--hair);
  font-size: var(--fs-table);
}

.item-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-items {
  padding-top: var(--s-2);
  font-size: var(--fs-sm);
}

.trend-increasing,
.change-up {
  color: var(--ok);
}

.trend-decreasing,
.change-down {
  color: var(--bad);
}

.trend-stable,
.change-stable {
  color: var(--info);
}
</style>
