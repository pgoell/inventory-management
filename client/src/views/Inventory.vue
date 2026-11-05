<template>
  <div class="inventory">
    <div class="page-head">
      <h2>{{ t('inventory.title') }}</h2>
      <p>{{ t('inventory.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <section v-else class="section">
      <div class="section-label">
        <span>{{ t('inventory.stockLevels') }}</span>
        <span class="aside mono">{{ filteredItems.length }} {{ t('inventory.skus') }}</span>
      </div>
      <div class="toolbar">
        <div class="search-box">
          <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="t('inventory.searchPlaceholder')"
            :aria-label="t('inventory.searchPlaceholder')"
            class="input search-input"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="clear-search"
            :title="t('inventory.clearSearch')"
            :aria-label="t('inventory.clearSearch')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
      <div class="ledger-wrap">
        <table class="ledger">
          <thead>
            <tr>
              <th>{{ t('inventory.table.sku') }}</th>
              <th>{{ t('inventory.table.itemName') }}</th>
              <th>{{ t('inventory.table.category') }}</th>
              <th class="num">{{ t('inventory.table.quantityOnHand') }}</th>
              <th class="num">{{ t('inventory.table.reorderPoint') }}</th>
              <th class="num">{{ t('inventory.table.unitCost') }}</th>
              <th class="num">{{ t('inventory.table.totalValue') }}</th>
              <th>{{ t('inventory.table.location') }}</th>
              <th>{{ t('inventory.table.status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in filteredItems"
              :key="item.id"
              class="is-clickable"
              tabindex="0"
              @click="showItemDetail(item)"
              @keydown.enter="showItemDetail(item)"
            >
              <td class="mono sku">{{ item.sku }}</td>
              <td>{{ translateProductName(item.name) }}</td>
              <td>{{ translateCategory(item.category) }}</td>
              <td class="num"><strong>{{ item.quantity_on_hand }}</strong></td>
              <td class="num">{{ item.reorder_point }}</td>
              <td class="num">{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
              <td class="num"><strong>{{ currencySymbol }}{{ (item.quantity_on_hand * item.unit_cost).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong></td>
              <td>{{ translateWarehouse(item.location) }}</td>
              <td>
                <span :class="['tag', getStockStatusClass(item)]">
                  {{ getStockStatus(item) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <InventoryDetailModal
      :is-open="showItemModal"
      :inventory-item="selectedItem"
      @close="showItemModal = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import InventoryDetailModal from '../components/InventoryDetailModal.vue'

export default {
  name: 'Inventory',
  components: {
    InventoryDetailModal
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const items = ref([])
    const searchQuery = ref('')

    // Modal state
    const showItemModal = ref(false)
    const selectedItem = ref(null)

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Stock status order for sorting (using status keys)
    const STATUS_ORDER = { 'lowStock': 0, 'adequate': 1, 'inStock': 2 }

    // Get stock status key (for sorting and translation)
    const getStockStatusKey = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'lowStock'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'adequate'
      } else {
        return 'inStock'
      }
    }

    // Computed property to filter items by search query and sort by stock status
    const filteredItems = computed(() => {
      let filtered = items.value

      // Apply search filter if query exists
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase().trim()
        filtered = filtered.filter(item =>
          item.name.toLowerCase().includes(query)
        )
      }

      // Sort by stock status: Low Stock first, then Adequate, then In Stock
      // Always create a copy to avoid mutating the original array
      return filtered.slice().sort((a, b) => {
        const statusA = getStockStatusKey(a)
        const statusB = getStockStatusKey(b)
        return STATUS_ORDER[statusA] - STATUS_ORDER[statusB]
      })
    })

    const loadInventory = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        // Inventory doesn't support month/status filters, only warehouse and category
        items.value = await api.getInventory({
          warehouse: filters.warehouse,
          category: filters.category
        })
      } catch (err) {
        error.value = 'Failed to load inventory: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadInventory()
    })

    const getStockStatus = (item) => {
      const key = getStockStatusKey(item)
      return t(`status.${key}`)
    }

    const getStockStatusClass = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'tag--bad'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'tag--warn'
      } else {
        return 'tag--ok'
      }
    }

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

    const showItemDetail = (item) => {
      selectedItem.value = item
      showItemModal.value = true
    }

    onMounted(loadInventory)

    return {
      t,
      loading,
      error,
      items,
      searchQuery,
      filteredItems,
      getStockStatus,
      getStockStatusClass,
      translateCategory,
      showItemModal,
      selectedItem,
      showItemDetail,
      currencySymbol,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.sku {
  font-weight: 600;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 22rem;
}

.search-icon {
  position: absolute;
  left: var(--s-3);
  width: 16px;
  height: 16px;
  color: var(--ink-3);
  pointer-events: none;
}

.search-input {
  padding-left: 2.25rem;
  padding-right: 2.25rem;
}

.clear-search {
  position: absolute;
  right: var(--s-1);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: 0;
  border-radius: var(--radius);
  color: var(--ink-3);
  cursor: pointer;
  transition: transform var(--dur-ui) var(--ease-out), color var(--dur-ui) ease;
}

.clear-search:active {
  transform: scale(0.95);
}

@media (hover: hover) and (pointer: fine) {
  .clear-search:hover {
    color: var(--ink);
  }
}

.clear-search svg {
  width: 14px;
  height: 14px;
}
</style>
