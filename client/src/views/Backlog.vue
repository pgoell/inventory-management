<template>
  <div class="backlog">
    <div class="page-head">
      <h2>Backlog Management</h2>
      <p>Track and resolve inventory shortages</p>
    </div>

    <div v-if="loading" class="loading">Loading backlog...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats">
        <div class="stat is-bad">
          <span class="stat-label">High Priority</span>
          <span class="stat-value">{{ getBacklogByPriority('high').length }}</span>
        </div>
        <div class="stat is-warn">
          <span class="stat-label">Medium Priority</span>
          <span class="stat-value">{{ getBacklogByPriority('medium').length }}</span>
        </div>
        <div class="stat is-info">
          <span class="stat-label">Low Priority</span>
          <span class="stat-value">{{ getBacklogByPriority('low').length }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Total Backlog Items</span>
          <span class="stat-value">{{ backlogItems.length }}</span>
        </div>
      </div>

      <section class="section">
        <div class="section-label">
          <span>Backlog Items</span>
        </div>
        <div v-if="backlogItems.length === 0" class="empty">
          No backlog items - all orders can be fulfilled!
        </div>
        <div v-else class="ledger-wrap">
          <table class="ledger">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>SKU</th>
                <th>Item Name</th>
                <th class="num">Quantity Needed</th>
                <th class="num">Quantity Available</th>
                <th>Shortage</th>
                <th class="num">Days Delayed</th>
                <th>Priority</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in backlogItems" :key="item.id">
                <td class="mono strong">{{ item.order_id }}</td>
                <td class="mono strong">{{ item.item_sku }}</td>
                <td>{{ item.item_name }}</td>
                <td class="num">{{ item.quantity_needed }}</td>
                <td class="num">{{ item.quantity_available }}</td>
                <td>
                  <span class="tag tag--bad">
                    {{ item.quantity_needed - item.quantity_available }} units short
                  </span>
                </td>
                <td class="num" :class="item.days_delayed > 7 ? 'late-bad' : 'late-warn'">
                  {{ item.days_delayed }} days
                </td>
                <td>
                  <span :class="['tag', priorityTag[item.priority]]">
                    {{ item.priority }}
                  </span>
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
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'

export default {
  name: 'Backlog',
  setup() {
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
        error.value = 'Failed to load backlog: ' + err.message
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
      loading,
      error,
      backlogItems,
      getBacklogByPriority,
      priorityTag
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
