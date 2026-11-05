<template>
  <div class="orders">
    <div class="page-head">
      <h2>{{ t('orders.title') }}</h2>
      <p>{{ t('orders.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats">
        <div class="stat is-ok">
          <span class="stat-label">{{ t('status.delivered') }}</span>
          <span class="stat-value">{{ getOrdersByStatus('Delivered').length }}</span>
        </div>
        <div class="stat is-info">
          <span class="stat-label">{{ t('status.shipped') }}</span>
          <span class="stat-value">{{ getOrdersByStatus('Shipped').length }}</span>
        </div>
        <div class="stat is-warn">
          <span class="stat-label">{{ t('status.processing') }}</span>
          <span class="stat-value">{{ getOrdersByStatus('Processing').length }}</span>
        </div>
        <div class="stat is-bad">
          <span class="stat-label">{{ t('status.backordered') }}</span>
          <span class="stat-value">{{ getOrdersByStatus('Backordered').length }}</span>
        </div>
      </div>

      <div class="section">
        <div class="section-label">
          <span>{{ t('orders.allOrders') }}</span>
          <span class="aside mono">{{ orders.length }}</span>
        </div>
        <div class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>{{ t('orders.table.orderNumber') }}</th>
                <th>{{ t('orders.table.customer') }}</th>
                <th>{{ t('orders.table.items') }}</th>
                <th>{{ t('orders.table.status') }}</th>
                <th>{{ t('orders.table.orderDate') }}</th>
                <th>{{ t('orders.table.expectedDelivery') }}</th>
                <th class="num">{{ t('orders.table.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="mono">{{ order.order_number }}</td>
                <td>{{ translateCustomerName(order.customer) }}</td>
                <td>
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="item in order.items" :key="item.sku || item.name" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta mono">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ currencySymbol }}{{ item.unit_price }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td>
                  <span :class="['tag', `tag--${getOrderStatusClass(order.status)}`]">
                    {{ t(`status.${order.status.toLowerCase()}`) }}
                  </span>
                </td>
                <td>{{ formatDate(order.order_date) }}</td>
                <td>{{ formatDate(order.expected_delivery) }}</td>
                <td class="num">{{ currencySymbol }}{{ order.total_value.toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="section">
        <div class="section-label">
          <span>{{ t('orders.submitted.title') }}</span>
          <span class="aside">{{ t('orders.submitted.aside') }}</span>
        </div>
        <div v-if="restockOrders.length === 0" class="empty">{{ t('orders.submitted.empty') }}</div>
        <div v-else class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>{{ t('orders.submitted.orderId') }}</th>
                <th>{{ t('orders.submitted.submittedOn') }}</th>
                <th>{{ t('orders.submitted.lines') }}</th>
                <th class="num">{{ t('orders.submitted.totalCost') }}</th>
                <th class="num">{{ t('orders.submitted.leadTime') }}</th>
                <th>{{ t('orders.submitted.expectedDelivery') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ro in restockOrders" :key="ro.id">
                <td class="mono">{{ ro.id }}</td>
                <td>{{ formatDate(ro.created_at) }}</td>
                <td>
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: ro.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="item in ro.items" :key="item.sku" class="item-entry">
                        <span class="item-name">{{ item.name }}</span>
                        <span class="item-meta mono">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="num">{{ currencySymbol }}{{ ro.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
                <td class="num">{{ ro.lead_time_days }}</td>
                <td>{{ formatDate(ro.expected_delivery) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Orders',
  setup() {
    const { t, currentCurrency, translateProductName, translateCustomerName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })
    const loading = ref(true)
    const error = ref(null)
    const orders = ref([])
    const restockOrders = ref([])

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loadOrders = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        const fetchedOrders = await api.getOrders(filters)

        // Sort orders by order_date (earliest first)
        orders.value = fetchedOrders.sort((a, b) => {
          const dateA = new Date(a.order_date)
          const dateB = new Date(b.order_date)
          return dateA - dateB
        })
      } catch (err) {
        error.value = 'Failed to load orders: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadOrders()
    })

    const getOrdersByStatus = (status) => {
      return orders.value.filter(order => order.status === status)
    }

    const getOrderStatusClass = (status) => {
      const statusMap = {
        'Delivered': 'ok',
        'Shipped': 'info',
        'Processing': 'warn',
        'Backordered': 'bad'
      }
      return statusMap[status] || 'info'
    }

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const loadRestockOrders = async () => {
      try {
        restockOrders.value = await api.getRestockOrders()
      } catch (err) {
        console.error('Failed to load restock orders:', err)
      }
    }

    onMounted(() => {
      loadOrders()
      loadRestockOrders()
    })

    return {
      t,
      loading,
      error,
      orders,
      restockOrders,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      currencySymbol,
      translateProductName,
      translateCustomerName
    }
  }
}
</script>

<style scoped>
.items-details {
  position: relative;
}

.items-summary {
  cursor: pointer;
  color: var(--signal);
  list-style: none;
  user-select: none;
  display: inline-block;
}

.items-summary::-webkit-details-marker {
  display: none;
}

.items-summary::before {
  content: '';
  display: inline-block;
  width: 0;
  height: 0;
  margin-right: 8px;
  border-left: 5px solid currentColor;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  transition: transform 160ms ease-out;
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

@media (hover: hover) and (pointer: fine) {
  .items-summary:hover {
    text-decoration: underline;
  }
}

.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  background: var(--paper-raised);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  padding: 8px 12px;
  z-index: 10;
  min-width: 18rem;
  max-width: 25rem;
  box-shadow: 0 6px 20px color-mix(in srgb, var(--ink) 10%, transparent);
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 0;
  border-bottom: 1px solid var(--rule);
}

.item-entry:last-child {
  border-bottom: 0;
}

.item-name {
  font-size: 12.5px;
  font-weight: 600;
}

.item-meta {
  font-size: 12px;
  color: var(--ink-3);
}
</style>
