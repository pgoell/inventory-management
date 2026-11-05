<template>
  <Teleport to="body">
    <div v-if="isOpen && backlogItem" class="modal-scrim" @click="close">
      <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="po-modal-title" @click.stop>
        <div class="modal-head">
          <h3 id="po-modal-title" class="modal-heading">
            {{ t(mode === 'view' ? 'purchaseOrder.viewTitle' : 'purchaseOrder.createTitle') }}
          </h3>
          <button type="button" class="modal-x" :aria-label="t('common.close')" @click="close">&times;</button>
        </div>

        <form class="po-form" novalidate @submit.prevent="submit">
          <div class="modal-content">
            <dl class="po-item">
              <div>
                <dt class="label">{{ t('purchaseOrder.orderId') }}</dt>
                <dd class="mono">{{ backlogItem.order_id }}</dd>
              </div>
              <div>
                <dt class="label">{{ t('purchaseOrder.sku') }}</dt>
                <dd class="mono">{{ backlogItem.item_sku }}</dd>
              </div>
              <div>
                <dt class="label">{{ t('purchaseOrder.item') }}</dt>
                <dd>{{ translateProductName(backlogItem.item_name) }}</dd>
              </div>
              <div>
                <dt class="label">{{ t('purchaseOrder.shortage') }}</dt>
                <dd>
                  <span class="tag tag--bad">{{ t('purchaseOrder.unitsShort', { count: shortage }) }}</span>
                </dd>
              </div>
            </dl>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
              <div v-else-if="loadError" class="error" role="alert">{{ loadError }}</div>
              <dl v-else-if="po" class="po-fields">
                <div>
                  <dt class="label">{{ t('purchaseOrder.supplier') }}</dt>
                  <dd>{{ po.supplier_name }}</dd>
                </div>
                <div>
                  <dt class="label">{{ t('purchaseOrder.status') }}</dt>
                  <dd><span :class="['tag', statusTag]">{{ po.status }}</span></dd>
                </div>
                <div>
                  <dt class="label">{{ t('purchaseOrder.quantity') }}</dt>
                  <dd class="mono">{{ po.quantity }}</dd>
                </div>
                <div>
                  <dt class="label">{{ t('purchaseOrder.unitCost') }}</dt>
                  <dd class="mono">{{ money(po.unit_cost) }}</dd>
                </div>
                <div>
                  <dt class="label">{{ t('purchaseOrder.total') }}</dt>
                  <dd class="mono po-total">{{ money(po.quantity * po.unit_cost) }}</dd>
                </div>
                <div>
                  <dt class="label">{{ t('purchaseOrder.expectedDelivery') }}</dt>
                  <dd>{{ formatDate(po.expected_delivery_date) }}</dd>
                </div>
                <div>
                  <dt class="label">{{ t('purchaseOrder.createdDate') }}</dt>
                  <dd>{{ formatDate(po.created_date) }}</dd>
                </div>
                <div class="po-wide">
                  <dt class="label">{{ t('purchaseOrder.notes') }}</dt>
                  <dd class="po-notes">{{ po.notes || '-' }}</dd>
                </div>
              </dl>
            </template>

            <!-- Create mode -->
            <div v-else class="po-grid">
              <div class="field po-wide">
                <label for="po-supplier">{{ t('purchaseOrder.supplier') }}</label>
                <input id="po-supplier" v-model.trim="form.supplier_name" class="input" type="text" required autocomplete="off" />
              </div>
              <div class="field">
                <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                <input id="po-quantity" v-model.number="form.quantity" class="input num" type="number" min="1" step="1" required />
              </div>
              <div class="field">
                <label for="po-cost">{{ t('purchaseOrder.unitCost') }}</label>
                <input id="po-cost" v-model.number="form.unit_cost" class="input num" type="number" min="0" step="0.01" required />
              </div>
              <div class="field po-wide">
                <label for="po-date">{{ t('purchaseOrder.expectedDelivery') }}</label>
                <input id="po-date" v-model="form.expected_delivery_date" class="input" type="date" required />
              </div>
              <div class="field po-wide">
                <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                <textarea id="po-notes" v-model="form.notes" class="textarea" rows="3"></textarea>
              </div>
              <div class="po-wide po-sum">
                <span class="label">{{ t('purchaseOrder.total') }}</span>
                <span class="mono po-total">{{ money(total) }}</span>
              </div>
              <div v-if="submitError" class="error po-wide" role="alert">{{ submitError }}</div>
            </div>
          </div>

          <div class="modal-foot">
            <button type="button" class="btn" @click="close">{{ t('common.close') }}</button>
            <button
              v-if="mode !== 'view'"
              type="submit"
              class="btn btn--primary"
              :disabled="!isValid || saving"
            >
              {{ t(saving ? 'purchaseOrder.saving' : 'purchaseOrder.submit') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script>
import { reactive, ref, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

const pad = (n) => String(n).padStart(2, '0')

const defaultDeliveryDate = () => {
  const d = new Date()
  d.setDate(d.getDate() + 14)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: { type: Boolean, default: false },
    backlogItem: { type: Object, default: null },
    mode: { type: String, default: 'create', validator: (v) => ['create', 'view'].includes(v) }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentLocale, translateProductName } = useI18n()

    const form = reactive({
      supplier_name: '',
      quantity: 1,
      unit_cost: null,
      expected_delivery_date: '',
      notes: ''
    })
    const saving = ref(false)
    const submitError = ref(null)
    const po = ref(null)
    const loading = ref(false)
    const loadError = ref(null)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(1, Math.abs(props.backlogItem.quantity_needed - props.backlogItem.quantity_available))
    })

    const total = computed(() => (Number(form.quantity) || 0) * (Number(form.unit_cost) || 0))

    const isValid = computed(() =>
      form.supplier_name.trim() !== '' &&
      Number.isInteger(form.quantity) && form.quantity >= 1 &&
      typeof form.unit_cost === 'number' && form.unit_cost > 0 &&
      form.expected_delivery_date !== ''
    )

    const money = (value) =>
      Number(value).toLocaleString('en-US', { style: 'currency', currency: 'USD' })

    const formatDate = (value) => {
      if (!value) return '-'
      const date = new Date(value)
      if (isNaN(date.getTime())) return value
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        month: 'short', day: 'numeric', year: 'numeric'
      })
    }

    const statusTag = computed(() => {
      const s = String(po.value?.status || '').toLowerCase()
      if (s === 'delivered' || s === 'received') return 'tag--ok'
      if (s === 'cancelled') return 'tag--bad'
      if (s === 'pending') return 'tag--warn'
      return 'tag--info'
    })

    const errorDetail = (err, fallback) => {
      const detail = err?.response?.data?.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length) return detail.map((d) => d.msg).join(', ')
      return fallback
    }

    const resetForm = () => {
      form.supplier_name = ''
      form.quantity = shortage.value
      form.unit_cost = null
      form.expected_delivery_date = defaultDeliveryDate()
      form.notes = ''
      submitError.value = null
      saving.value = false
    }

    const loadPO = async () => {
      po.value = null
      loadError.value = null
      loading.value = true
      const id = props.backlogItem.id
      try {
        const result = await api.getPurchaseOrderByBacklogItem(id)
        if (props.backlogItem?.id === id) po.value = result
      } catch (err) {
        console.error('Failed to load purchase order:', err)
        loadError.value = errorDetail(err, t('purchaseOrder.loadError'))
      } finally {
        loading.value = false
      }
    }

    watch(
      () => [props.isOpen, props.backlogItem, props.mode],
      () => {
        if (!props.isOpen || !props.backlogItem) return
        if (props.mode === 'view') loadPO()
        else resetForm()
      },
      { immediate: true }
    )

    const submit = async () => {
      if (!isValid.value || saving.value) return
      saving.value = true
      submitError.value = null
      try {
        const payload = {
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.supplier_name.trim(),
          quantity: form.quantity,
          unit_cost: form.unit_cost,
          expected_delivery_date: form.expected_delivery_date
        }
        const notes = form.notes.trim()
        if (notes) payload.notes = notes
        const created = await api.createPurchaseOrder(payload)
        emit('po-created', created)
      } catch (err) {
        console.error('Failed to create purchase order:', err)
        submitError.value = errorDetail(err, t('purchaseOrder.createError'))
      } finally {
        saving.value = false
      }
    }

    const close = () => emit('close')

    return {
      t, form, saving, submitError, po, loading, loadError,
      shortage, total, isValid, money, formatDate, statusTag,
      submit, close, translateProductName
    }
  }
}
</script>

<style scoped>
.po-item {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
  gap: var(--s-3) var(--s-5);
  padding-bottom: var(--s-4);
  margin-bottom: var(--s-4);
  border-bottom: var(--hair);
}

.po-item dd,
.po-fields dd {
  margin-top: var(--s-1);
}

.po-grid,
.po-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--s-4) var(--s-5);
}

.po-wide {
  grid-column: 1 / -1;
}

.po-notes {
  white-space: pre-wrap;
}

.po-sum {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding-top: var(--s-3);
  border-top: var(--hair);
}

.po-total {
  font-size: var(--fs-lg);
  font-weight: 600;
}

.po-form {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.error {
  color: var(--bad);
  font-size: var(--fs-sm);
}
</style>
