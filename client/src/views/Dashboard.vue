<template>
  <div class="dashboard">
    <header class="page-head">
      <h2>{{ t('dashboard.title') }}</h2>
    </header>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Key performance indicators -->
      <section class="section">
        <h3 class="section-label">{{ t('dashboard.kpi.title') }}</h3>
        <div class="stats">
          <div class="stat">
            <span class="stat-label">{{ t('dashboard.kpi.inventoryTurnover') }}</span>
            <span class="stat-value">4.2</span>
            <span class="stat-note">{{ t('dashboard.kpi.goal') }}: 4.5 (-6.67%)</span>
          </div>

          <div class="stat">
            <span class="stat-label">{{ t('dashboard.kpi.ordersFulfilled') }}</span>
            <span class="stat-value">{{ ordersData.fulfilled }}</span>
            <span class="stat-note">{{ t('dashboard.kpi.goal') }}: {{ ordersData.goal }} ({{ calculatePercentage(ordersData.fulfilled, ordersData.goal) }}%)</span>
          </div>

          <div :class="['stat', fillRate >= 95 ? 'is-ok' : 'is-warn']">
            <span class="stat-label">{{ t('dashboard.kpi.orderFillRate') }}</span>
            <span class="stat-value">{{ fillRate }}%</span>
            <span class="stat-note">{{ t('dashboard.kpi.goal') }}: 95% ({{ fillRate - 95 > 0 ? '+' : '' }}{{ (fillRate - 95).toFixed(2) }}%)</span>
          </div>

          <div class="stat">
            <span class="stat-label">{{ t(selectedPeriod === 'all' ? 'dashboard.kpi.revenueYTD' : 'dashboard.kpi.revenueMTD') }}</span>
            <span class="stat-value">{{ formatCurrency(Math.round(summary.total_orders_value), selectedCurrency) }}</span>
            <span class="stat-note">{{ t('dashboard.kpi.goal') }}: {{ formatCurrency(revenueGoal, selectedCurrency) }} ({{ summary.total_orders_value > revenueGoal ? '+' : '' }}{{ ((summary.total_orders_value / revenueGoal - 1) * 100).toFixed(1) }}%)</span>
          </div>

          <div class="stat is-ok">
            <span class="stat-label">{{ t('dashboard.kpi.avgProcessingTime') }}</span>
            <span class="stat-value">2.8</span>
            <span class="stat-note">{{ t('dashboard.kpi.goal') }}: 3.0 (-6.67%)</span>
          </div>
        </div>
      </section>

      <!-- Summary: order health and inventory value -->
      <section class="section">
        <h3 class="section-label">{{ t('dashboard.summary.title') }}</h3>
        <div class="summary-grid">
          <!-- Order health -->
          <div class="panel">
            <h4 class="label panel-title">{{ t('dashboard.orderHealth.title') }}</h4>

            <div class="status-total">
              <span class="label">{{ t('dashboard.orderHealth.total') }}</span>
              <span class="status-total-value mono">{{ orderHealthMetrics.totalOrders }}</span>
            </div>
            <svg
              class="status-bar"
              viewBox="0 0 100 12"
              preserveAspectRatio="none"
              role="img"
              :aria-label="t('dashboard.orderHealth.title')"
            >
              <rect x="0" y="0" width="100" height="12" fill="var(--paper-sunk)" />
              <rect
                v-for="seg in statusSegments"
                :key="seg.key"
                :x="seg.start"
                y="0"
                :width="seg.width"
                height="12"
                :fill="seg.color"
              />
            </svg>
            <ul class="status-legend">
              <li v-for="seg in statusSegments" :key="seg.key">
                <span class="swatch" :style="{ background: seg.color }"></span>
                <span class="status-name">{{ t('status.' + seg.key) }}</span>
                <span class="mono status-count">{{ seg.count }}</span>
                <span class="mono muted status-pct">{{ seg.pct }}%</span>
              </li>
            </ul>

            <dl class="metrics">
              <div class="metric">
                <dt class="label">{{ t('dashboard.orderHealth.revenue') }}</dt>
                <dd class="mono">{{ formatCurrency(orderHealthMetrics.totalValue, selectedCurrency) }}</dd>
              </div>
              <div class="metric">
                <dt class="label">{{ t('dashboard.orderHealth.avgOrderValue') }}</dt>
                <dd class="mono">{{ formatCurrency(orderHealthMetrics.avgOrderValue, selectedCurrency) }}</dd>
              </div>
              <div class="metric">
                <dt class="label">{{ t('dashboard.orderHealth.onTimeRate') }}</dt>
                <dd :class="['mono', onTimeTone]">{{ orderHealthMetrics.onTimeRate.toFixed(1) }}%</dd>
              </div>
              <div class="metric">
                <dt class="label">{{ t('dashboard.orderHealth.avgFulfillmentDays') }}</dt>
                <dd class="mono">{{ orderHealthMetrics.avgFulfillmentDays.toFixed(1) }}</dd>
              </div>
            </dl>
          </div>

          <!-- Inventory by category -->
          <div class="panel">
            <h4 class="label panel-title">{{ t('dashboard.inventoryValue.title') }}</h4>
            <ul v-if="categoryData.length > 0" class="bars">
              <li v-for="cat in categoryData" :key="cat.name" class="bar-row">
                <span class="bar-label">{{ translateCategory(cat.name) }}</span>
                <svg class="bar-svg" viewBox="0 0 100 14" preserveAspectRatio="none" aria-hidden="true">
                  <line x1="0" y1="7" x2="100" y2="7" stroke="var(--rule)" stroke-width="1" vector-effect="non-scaling-stroke" />
                  <rect x="0" y="1" :width="cat.value / maxCategoryValue * 100" height="12" fill="var(--chart-1)" />
                </svg>
                <span class="bar-value mono">{{ selectedCurrency === 'JPY' ? formatCurrency(cat.value, selectedCurrency) : `$${(cat.value / 1000).toFixed(1)}K` }}</span>
              </li>
            </ul>
            <div v-else class="empty">{{ t('dashboard.inventoryShortages.noData') }}</div>
          </div>
        </div>
      </section>

      <!-- Inventory shortages -->
      <section class="section">
        <h3 class="section-label">
          <span>{{ t('dashboard.inventoryShortages.title') }}</span>
          <span class="aside mono">{{ backlogItems.length }}</span>
        </h3>
        <div v-if="backlogItems.length === 0" class="empty">{{ t('dashboard.inventoryShortages.noShortages') }}</div>
        <div v-else class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>{{ t('dashboard.inventoryShortages.orderId') }}</th>
                <th>{{ t('dashboard.inventoryShortages.sku') }}</th>
                <th>{{ t('dashboard.inventoryShortages.itemName') }}</th>
                <th class="num">{{ t('dashboard.inventoryShortages.quantityNeeded') }}</th>
                <th class="num">{{ t('dashboard.inventoryShortages.quantityAvailable') }}</th>
                <th>{{ t('dashboard.inventoryShortages.shortage') }}</th>
                <th class="num">{{ t('dashboard.inventoryShortages.daysDelayed') }}</th>
                <th>{{ t('dashboard.inventoryShortages.priority') }}</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in backlogItems"
                :key="item.id"
                class="is-clickable"
                tabindex="0"
                @click="showBacklogDetail(item)"
                @keydown.enter="showBacklogDetail(item)"
              >
                <td class="mono">{{ item.order_id }}</td>
                <td class="mono">{{ item.item_sku }}</td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td class="num">{{ item.quantity_needed }}</td>
                <td class="num">{{ item.quantity_available }}</td>
                <td>
                  <span class="tag tag--bad">
                    {{ Math.abs(item.quantity_needed - item.quantity_available) }} {{ t('dashboard.inventoryShortages.unitsShort') }}
                  </span>
                </td>
                <td :class="['num', item.days_delayed > 7 ? 'tone-bad' : 'tone-warn']">
                  {{ item.days_delayed }} {{ t('dashboard.inventoryShortages.days') }}
                </td>
                <td>
                  <span :class="['tag', priorityTag(item.priority)]">
                    {{ translatePriority(item.priority) }}
                  </span>
                </td>
                <td>
                  <button
                    v-if="!item.purchase_order_id"
                    type="button"
                    class="btn btn--sm btn--primary"
                    @click.stop="openPOModal(item)"
                  >
                    Create PO
                  </button>
                  <button
                    v-else
                    type="button"
                    class="btn btn--sm"
                    @click.stop="viewPO(item)"
                  >
                    View PO
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Top products -->
      <section class="section">
        <h3 class="section-label">{{ t('dashboard.topProducts.title') }}</h3>
        <div class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>{{ t('dashboard.topProducts.product') }}</th>
                <th>{{ t('dashboard.topProducts.sku') }}</th>
                <th>{{ t('dashboard.topProducts.category') }}</th>
                <th class="num">{{ t('dashboard.topProducts.unitsOrdered') }}</th>
                <th class="num">{{ t('dashboard.topProducts.revenue') }}</th>
                <th>{{ t('dashboard.topProducts.firstOrder') }}</th>
                <th>{{ t('dashboard.topProducts.stockStatus') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in topProducts"
                :key="item.sku"
                class="is-clickable"
                tabindex="0"
                @click="showProductDetail(item)"
                @keydown.enter="showProductDetail(item)"
              >
                <td>{{ translateProductName(item.name) }}</td>
                <td class="mono">{{ item.sku }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td class="num">{{ item.unitsOrdered }}</td>
                <td class="num">{{ formatCurrency(item.revenue, selectedCurrency) }}</td>
                <td>{{ formatDate(item.firstOrderDate) }}</td>
                <td>
                  <span :class="['tag', 'tag--' + getStockBadge(item.stockLevel)]">
                    {{ translateStockLevel(item.stockLevel) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <ProductDetailModal
      :is-open="showProductModal"
      :product="selectedProduct"
      @close="showProductModal = false"
    />

    <BacklogDetailModal
      :is-open="showBacklogModal"
      :backlog-item="selectedBacklogItem"
      @close="showBacklogModal = false"
    />

    <PurchaseOrderModal
      :is-open="showPOModal"
      :backlog-item="selectedBacklogForPO"
      :mode="poModalMode"
      @close="showPOModal = false"
      @po-created="handlePOCreated"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'
import ProductDetailModal from '../components/ProductDetailModal.vue'
import BacklogDetailModal from '../components/BacklogDetailModal.vue'

export default {
  name: 'Dashboard',
  components: {
    ProductDetailModal,
    BacklogDetailModal,
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const summary = ref({})
    const allOrders = ref([])
    const inventoryItems = ref([])

    // Modal state
    const showProductModal = ref(false)
    const selectedProduct = ref(null)
    const showBacklogModal = ref(false)
    const selectedBacklogItem = ref(null)
    const showPOModal = ref(false)
    const selectedBacklogForPO = ref(null)
    const poModalMode = ref('create')

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const ordersData = ref({ fulfilled: 187, goal: 200 })
    const fillRate = ref(96.8)

    const revenueGoal = computed(() => {
      // $800K per month, so if looking at all months (12 months), goal is 12 * 800K = 9.6M
      const monthlyGoal = 800000
      if (selectedPeriod.value === 'all') {
        return monthlyGoal * 12 // $9,600,000 for the full year
      }
      return monthlyGoal // $800,000 for a single month
    })

    const statusData = computed(() => {
      const counts = { delivered: 0, shipped: 0, processing: 0, backordered: 0 }
      allOrders.value.forEach(order => {
        const status = order.status.toLowerCase()
        if (counts[status] !== undefined) counts[status]++
      })
      return counts
    })

    const orderHealthMetrics = computed(() => {
      const totalOrders = allOrders.value.length
      const totalValue = allOrders.value.reduce((sum, order) => sum + (order.total_value || 0), 0)
      const avgOrderValue = totalOrders > 0 ? totalValue / totalOrders : 0

      // Calculate on-time delivery rate (delivered orders that arrived on or before expected date)
      const deliveredOrders = allOrders.value.filter(o => o.status.toLowerCase() === 'delivered')
      const onTimeDeliveries = deliveredOrders.filter(o => {
        if (o.actual_delivery && o.expected_delivery) {
          return new Date(o.actual_delivery) <= new Date(o.expected_delivery)
        }
        return false
      }).length
      const onTimeRate = deliveredOrders.length > 0 ? (onTimeDeliveries / deliveredOrders.length) * 100 : 0

      // Calculate average fulfillment speed (days from order to delivery for delivered orders)
      let totalDays = 0
      let countWithDates = 0
      deliveredOrders.forEach(o => {
        if (o.order_date && o.actual_delivery) {
          const orderDate = new Date(o.order_date)
          const deliveryDate = new Date(o.actual_delivery)
          const days = Math.round((deliveryDate - orderDate) / (1000 * 60 * 60 * 24))
          totalDays += days
          countWithDates++
        }
      })
      const avgFulfillmentDays = countWithDates > 0 ? totalDays / countWithDates : 0

      return {
        totalOrders,
        totalValue,
        avgOrderValue,
        onTimeRate,
        avgFulfillmentDays
      }
    })

    const categoryData = computed(() => {
      // Group inventory by category and calculate values
      // Filter inventory items to only include those with orders in the selected period
      const categoryMap = {}

      // Get SKUs from orders in the filtered time period
      const orderedSkus = new Set()
      allOrders.value.forEach(order => {
        if (order.items) {
          order.items.forEach(item => {
            orderedSkus.add(item.sku)
          })
        }
      })

      // Only include inventory items that have orders in the selected period
      // If no period is selected (all), include all inventory items
      const itemsToInclude = selectedPeriod.value === 'all'
        ? inventoryItems.value
        : inventoryItems.value.filter(item => orderedSkus.has(item.sku))

      itemsToInclude.forEach(item => {
        const cat = item.category.toLowerCase()
        if (!categoryMap[cat]) {
          categoryMap[cat] = {
            name: item.category,
            value: 0,
            category: cat,
            count: 0
          }
        }
        categoryMap[cat].value += item.quantity_on_hand * item.unit_cost
        categoryMap[cat].count += 1
      })

      return Object.values(categoryMap)
    })

    const maxCategoryValue = computed(() => {
      if (categoryData.value.length === 0) return 1
      return Math.max(...categoryData.value.map(c => c.value))
    })

    const orderTrendData = computed(() => {
      // Group orders by month from the actual data
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

      // Initialize all months with 0 orders
      const monthMap = {}
      monthNames.forEach(month => {
        monthMap[month] = { month, orders: 0 }
      })

      // Count orders for each month
      if (Array.isArray(allOrders.value)) {
        allOrders.value.forEach(order => {
          if (order && order.order_date) {
            const date = new Date(order.order_date)
            const monthIndex = date.getMonth()
            // Check if monthIndex is valid (0-11)
            if (!isNaN(monthIndex) && monthIndex >= 0 && monthIndex <= 11) {
              const monthName = monthNames[monthIndex]
              monthMap[monthName].orders++
            }
          }
        })
      }

      // Return all months in order
      return monthNames.map(month => monthMap[month])
    })

    const maxOrderCount = computed(() => {
      if (orderTrendData.value.length === 0) return 10
      const max = Math.max(...orderTrendData.value.map(d => d.orders))
      // Round up to nearest 10 for cleaner axis, minimum 10
      return Math.max(10, Math.ceil(max / 10) * 10)
    })

    const topProducts = computed(() => {
      // Calculate top products from filtered order data
      const productMap = {}

      // allOrders is already filtered by API based on: month, warehouse, category, status
      allOrders.value.forEach(order => {
        if (order.items) {
          order.items.forEach(item => {
            const sku = item.sku

            // Find matching inventory item to get full product details
            // Note: inventoryItems is also filtered by API based on: warehouse, category
            const invItem = inventoryItems.value.find(i => i.sku === sku)

            // Skip products that don't match current inventory filters
            // (e.g., if filtering by warehouse A, don't show products from warehouse B)
            if (!invItem && (selectedLocation.value !== 'all' || selectedCategory.value !== 'all')) {
              return // Skip this product as it doesn't match inventory filters
            }

            if (!productMap[sku]) {
              productMap[sku] = {
                name: item.name,
                sku: sku,
                category: invItem?.category || 'Unknown',
                warehouse: invItem?.warehouse || 'Unknown',
                unitsOrdered: 0,
                revenue: 0,
                stockLevel: invItem ? (invItem.quantity_on_hand > invItem.reorder_point ? 'In Stock' : 'Low Stock') : 'Unknown',
                firstOrderDate: order.order_date
              }
            } else {
              // Update to EARLIEST order date (to show January at top when selecting All Months)
              if (order.order_date && (!productMap[sku].firstOrderDate || order.order_date < productMap[sku].firstOrderDate)) {
                productMap[sku].firstOrderDate = order.order_date
              }
            }
            productMap[sku].unitsOrdered += item.quantity
            productMap[sku].revenue += item.quantity * item.unit_price
          })
        }
      })

      // Convert to array, sort by first order date (earliest first = January at top), then by revenue, and take top 12
      return Object.values(productMap)
        .sort((a, b) => {
          // Sort by first order date (earliest first)
          // This ensures products first ordered in January appear before those first ordered in December
          const dateA = new Date(a.firstOrderDate || '9999-12-31')
          const dateB = new Date(b.firstOrderDate || '9999-12-31')
          if (dateA.getTime() !== dateB.getTime()) {
            return dateA.getTime() - dateB.getTime() // Earlier dates come first
          }
          // If dates are equal, sort by revenue (highest first)
          return b.revenue - a.revenue
        })
        .slice(0, 12)
    })

    const allBacklogItems = ref([])

    // Filter backlog based on inventory filters
    const backlogItems = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allBacklogItems.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allBacklogItems.value.filter(b => validSkus.has(b.item_sku))
    })

    const loadData = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [summaryData, ordersData, inventoryData, backlogData] = await Promise.all([
          api.getDashboardSummary(filters),
          api.getOrders(filters),
          api.getInventory(filters),
          api.getBacklog()
        ])

        summary.value = summaryData
        allOrders.value = ordersData
        inventoryItems.value = inventoryData
        allBacklogItems.value = backlogData
      } catch (err) {
        error.value = 'Failed to load dashboard data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const calculatePercentage = (value, goal) => {
      return ((value / goal) * 100).toFixed(2)
    }

    // Compute total orders once for efficiency
    const totalOrders = computed(() => {
      return statusData.value.delivered + statusData.value.shipped +
             statusData.value.processing + statusData.value.backordered
    })

    const getStockBadge = (level) => {
      if (level === 'In Stock') return 'ok'
      if (level === 'Low Stock') return 'warn'
      return 'bad'
    }

    const priorityTag = (priority) => {
      const tone = { high: 'bad', medium: 'warn', low: 'info' }[String(priority).toLowerCase()]
      return tone ? 'tag--' + tone : ''
    }

    const statusColors = {
      delivered: 'var(--chart-4)',
      shipped: 'var(--chart-3)',
      processing: 'var(--chart-5)',
      backordered: 'var(--chart-2)'
    }

    const statusSegments = computed(() => {
      const total = totalOrders.value
      let start = 0
      return Object.keys(statusColors).map(key => {
        const count = statusData.value[key]
        const width = total > 0 ? (count / total) * 100 : 0
        const seg = { key, count, start, width, pct: width.toFixed(1), color: statusColors[key] }
        start += width
        return seg
      })
    })

    const onTimeTone = computed(() => {
      const rate = orderHealthMetrics.value.onTimeRate
      if (rate >= 90) return 'tone-ok'
      if (rate >= 75) return 'tone-warn'
      return 'tone-bad'
    })

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    const translateStockLevel = (stockLevel) => {
      const stockMap = {
        'In Stock': t('status.inStock'),
        'Low Stock': t('status.lowStock')
      }
      return stockMap[stockLevel] || stockLevel
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low'),
        'High': t('priority.high'),
        'Medium': t('priority.medium'),
        'Low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      const date = new Date(dateString)
      return date.toLocaleDateString(locale, { month: 'short', day: 'numeric', year: 'numeric' })
    }

    const showProductDetail = (product) => {
      selectedProduct.value = product
      showProductModal.value = true
    }

    const showBacklogDetail = (item) => {
      selectedBacklogItem.value = item
      showBacklogModal.value = true
    }

    const openPOModal = (item) => {
      selectedBacklogForPO.value = item
      poModalMode.value = 'create'
      showPOModal.value = true
    }

    const viewPO = (item) => {
      selectedBacklogForPO.value = item
      poModalMode.value = 'view'
      showPOModal.value = true
    }

    const handlePOCreated = (poData) => {
      // Update the backlog item with the new PO ID
      const item = allBacklogItems.value.find(b => b.id === poData.backlog_item_id)
      if (item) {
        item.purchase_order_id = poData.id
        item.purchase_order = poData
      }
      showPOModal.value = false
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      summary,
      ordersData,
      fillRate,
      statusData,
      orderHealthMetrics,
      categoryData,
      maxCategoryValue,
      orderTrendData,
      maxOrderCount,
      topProducts,
      backlogItems,
      calculatePercentage,
      getStockBadge,
      priorityTag,
      statusSegments,
      onTimeTone,
      translateCategory,
      translateStockLevel,
      translatePriority,
      formatDate,
      revenueGoal,
      showProductModal,
      selectedProduct,
      showProductDetail,
      showBacklogModal,
      selectedBacklogItem,
      showBacklogDetail,
      selectedPeriod,
      selectedCurrency: currentCurrency,
      formatCurrency,
      Math,
      translateProductName,
      translateWarehouse,
      showPOModal,
      selectedBacklogForPO,
      poModalMode,
      openPOModal,
      viewPO,
      handlePOCreated
    }
  }
}
</script>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--s-6);
}

.panel-title {
  margin-bottom: var(--s-3);
}

/* order status bar */
.status-total {
  display: flex;
  align-items: baseline;
  gap: var(--s-3);
  margin-bottom: var(--s-2);
}

.status-total-value {
  font-size: var(--fs-lg);
}

.status-bar {
  display: block;
  width: 100%;
  height: 12px;
}

.status-legend {
  list-style: none;
  margin: var(--s-3) 0 var(--s-5);
  font-size: var(--fs-table);
}

.status-legend li {
  display: grid;
  grid-template-columns: 10px 1fr auto 3.5rem;
  align-items: baseline;
  gap: var(--s-3);
  padding: 4px 0;
  border-bottom: var(--hair);
}

.swatch {
  width: 10px;
  height: 10px;
  align-self: center;
}

.status-pct {
  text-align: right;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--s-4) var(--s-5);
}

.metric dd {
  font-size: var(--fs-md);
  margin-top: 2px;
}

.tone-ok {
  color: var(--ok);
}
.tone-warn {
  color: var(--warn);
}
.tone-bad {
  color: var(--bad);
}

/* category bars */
.bars {
  list-style: none;
}

.bar-row {
  display: grid;
  grid-template-columns: 8rem minmax(0, 1fr) 5.5rem;
  align-items: center;
  gap: var(--s-3);
  padding: 6px 0;
  border-bottom: var(--hair);
}

.bar-label {
  font-size: var(--fs-table);
}

.bar-svg {
  display: block;
  width: 100%;
  height: 14px;
}

.bar-value {
  text-align: right;
  font-size: var(--fs-table);
}

.ledger tr.is-clickable:focus-visible {
  outline-offset: -2px;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
