<template>
  <div class="backlog">
    <div class="page-head">
      <h2>{{ t('backlog.title') }}</h2>
      <p>{{ t('backlog.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('backlog.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats">
        <div class="stat is-bad">
          <span class="stat-label">{{ t('backlog.highPriority') }}</span>
          <span class="stat-value">{{ getBacklogByPriority('high').length }}</span>
        </div>
        <div class="stat is-warn">
          <span class="stat-label">{{ t('backlog.mediumPriority') }}</span>
          <span class="stat-value">{{ getBacklogByPriority('medium').length }}</span>
        </div>
        <div class="stat is-info">
          <span class="stat-label">{{ t('backlog.lowPriority') }}</span>
          <span class="stat-value">{{ getBacklogByPriority('low').length }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">{{ t('backlog.totalItems') }}</span>
          <span class="stat-value">{{ backlogItems.length }}</span>
        </div>
      </div>

      <div class="section">
        <div class="section-label">
          <span>{{ t('backlog.items') }}</span>
          <span class="aside mono">{{ backlogItems.length }}</span>
        </div>
        <div v-if="backlogItems.length === 0" class="empty">{{ t('backlog.empty') }}</div>
        <div v-else class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>{{ t('backlog.orderId') }}</th>
                <th>{{ t('backlog.sku') }}</th>
                <th>{{ t('backlog.itemName') }}</th>
                <th class="num">{{ t('backlog.quantityNeeded') }}</th>
                <th class="num">{{ t('backlog.quantityAvailable') }}</th>
                <th>{{ t('backlog.shortage') }}</th>
                <th class="num">{{ t('backlog.daysDelayed') }}</th>
                <th>{{ t('backlog.priority') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in backlogItems" :key="item.id">
                <td class="strong">{{ item.order_id }}</td>
                <td class="strong">{{ item.item_sku }}</td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td class="num">{{ item.quantity_needed }}</td>
                <td class="num">{{ item.quantity_available }}</td>
                <td>
                  <span class="tag tag--bad">
                    {{ t('backlog.unitsShort', { count: item.quantity_needed - item.quantity_available }) }}
                  </span>
                </td>
                <td class="num" :class="item.days_delayed > 7 ? 'late-bad' : 'late-warn'">
                  {{ t('backlog.days', { count: item.days_delayed }) }}
                </td>
                <td>
                  <span :class="['tag', priorityTag[item.priority]]">
                    {{ t(`priority.${item.priority}`) }}
                  </span>
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
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Backlog',
  setup() {
    const { t, translateProductName } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allBacklogItems = ref([])
    const inventoryItems = ref([])

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Filter backlog based on inventory filters
    const backlogItems = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allBacklogItems.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allBacklogItems.value.filter(b => validSkus.has(b.item_sku))
    })

    const loadBacklog = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [backlogData, inventoryData] = await Promise.all([
          api.getBacklog(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allBacklogItems.value = backlogData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = t('backlog.loadError') + ': ' + err.message
      } finally {
        loading.value = false
      }
    }

    const getBacklogByPriority = (priority) => {
      return backlogItems.value.filter(item => item.priority === priority)
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadBacklog()
    })

    onMounted(loadBacklog)

    const priorityTag = { high: 'tag--bad', medium: 'tag--warn', low: 'tag--info' }

    return {
      t,
      priorityTag,
      translateProductName,
      loading,
      error,
      backlogItems,
      getBacklogByPriority
    }
  }
}
</script>

<style scoped>
.strong {
  font-weight: 600;
}

.late-bad {
  color: var(--bad);
}

.late-warn {
  color: var(--warn);
}
</style>
