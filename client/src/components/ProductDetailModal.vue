<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && product" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">Product Details</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="product-header">
              <div class="product-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5"/>
                  <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="product-title-section">
                <h4 class="product-name">{{ product.name }}</h4>
                <div class="product-sku">SKU: {{ product.sku }}</div>
              </div>
              <span class="stock-badge" :class="getStockBadgeClass(product.stockLevel)">
                {{ product.stockLevel }}
              </span>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">Category</div>
                <div class="info-value">{{ product.category }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Warehouse</div>
                <div class="info-value">{{ product.warehouse }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Units Ordered</div>
                <div class="info-value">{{ product.unitsOrdered }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Total Revenue</div>
                <div class="info-value">{{ currencySymbol }}{{ product.revenue.toLocaleString() }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Current Stock</div>
                <div class="info-value">{{ product.quantityOnHand }} units</div>
              </div>

              <div class="info-item">
                <div class="info-label">Reorder Point</div>
                <div class="info-value">{{ product.reorderPoint }} units</div>
              </div>

              <div class="info-item">
                <div class="info-label">First Order Date</div>
                <div class="info-value">{{ formatDate(product.firstOrderDate) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Stock Status</div>
                <div class="info-value">
                  <span :class="['badge', getStockBadgeClass(product.stockLevel)]">
                    {{ product.stockLevel }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">Close</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentCurrency } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  product: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const getStockBadgeClass = (stockLevel) => {
  if (stockLevel === 'In Stock') return 'success'
  if (stockLevel === 'Low Stock') return 'warning'
  if (stockLevel === 'Out of Stock') return 'danger'
  return 'info'
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--color-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--space-4);
}

.modal-container {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.close-button {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  transition: background-color var(--dur-fast) var(--ease), color var(--dur-fast) var(--ease);
}

.close-button:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.modal-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-8);
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-secondary {
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-weight: 600;
  font-size: var(--text-base);
  color: var(--color-text);
  cursor: pointer;
  transition: background-color var(--dur-fast) var(--ease);
}

.btn-secondary:hover {
  background: var(--color-surface-muted);
}

.product-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-5);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-8);
}

.product-icon {
  width: 64px;
  height: 64px;
  background: var(--color-accent);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent-contrast);
  flex-shrink: 0;
}

.product-title-section {
  flex: 1;
  min-width: 0;
}

.product-name {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 var(--space-2);
}

.product-sku {
  font-size: var(--text-base);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.stock-badge {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.stock-badge.success {
  background: var(--color-success-soft);
  color: var(--color-success-ink);
}

.stock-badge.warning {
  background: var(--color-warning-soft);
  color: var(--color-warning-ink);
}

.stock-badge.danger {
  background: var(--color-danger-soft);
  color: var(--color-danger-ink);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
  gap: var(--space-6);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.info-value {
  font-size: var(--text-base);
  color: var(--color-text);
  font-weight: 500;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--dur) var(--ease);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--dur) var(--ease);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
