<template>
  <div class="orders">
    <div class="page-header">
      <h2>{{ t('orders.title') }}</h2>
      <p>{{ t('orders.description') }}</p>
    </div>

    <!-- Restocking orders: independent of global filters and of the customer orders request -->
    <div class="card">
      <div class="card-header">
        <div>
          <h3 class="card-title">
            {{ t('orders.submittedOrders') }}<template v-if="!restockLoading && !restockError"> ({{ restockOrders.length }})</template>
          </h3>
          <p class="card-subtitle">{{ t('orders.submittedOrdersDescription') }}</p>
        </div>
      </div>

      <div v-if="restockLoading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="restockError" class="error">{{ restockError }}</div>
      <div v-else-if="restockOrders.length === 0" class="empty-state">{{ t('orders.noSubmittedOrders') }}</div>
      <div v-else class="table-container">
        <table class="orders-table restock-table">
          <thead>
            <tr>
              <th class="col-order-number">{{ t('orders.table.orderNumber') }}</th>
              <th class="col-items">{{ t('orders.table.items') }}</th>
              <th class="col-date">{{ t('orders.table.submittedDate') }}</th>
              <th class="col-lead-time">{{ t('orders.table.leadTime') }}</th>
              <th class="col-date">{{ t('orders.table.expectedDelivery') }}</th>
              <th class="col-value">{{ t('orders.table.totalValue') }}</th>
              <th class="col-status">{{ t('orders.table.status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in restockOrders" :key="order.id">
              <td class="col-order-number"><strong>{{ order.order_number }}</strong></td>
              <td class="col-items">
                <details class="items-details">
                  <summary class="items-summary">
                    {{ t('orders.itemsCount', { count: order.items.length }) }}
                  </summary>
                  <div class="items-dropdown">
                    <div v-for="item in order.items" :key="item.sku" class="item-entry">
                      <span class="item-name">{{ translateProductName(item.name) }}</span>
                      <span class="item-meta">{{ item.sku }} &middot; {{ t('orders.quantity') }}: {{ item.quantity }} @ {{ formatCurrencyWithDecimals(item.unit_price, currentCurrency, 2) }}</span>
                    </div>
                  </div>
                </details>
              </td>
              <td class="col-date">{{ formatDate(order.submitted_date) }}</td>
              <td class="col-lead-time">{{ t('orders.leadTimeDays', { days: order.lead_time_days }) }}</td>
              <td class="col-date">{{ formatDate(order.expected_delivery) }}</td>
              <td class="col-value"><strong>{{ formatCurrency(order.total_value, currentCurrency) }}</strong></td>
              <td class="col-status">
                <span :class="['badge', getOrderStatusClass(order.status)]">
                  {{ t(`status.${order.status.toLowerCase()}`) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('status.delivered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Delivered').length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('status.shipped') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Shipped').length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('status.processing') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Processing').length }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t('status.backordered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Backordered').length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('orders.allOrders') }} ({{ orders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th class="col-order-number">{{ t('orders.table.orderNumber') }}</th>
                <th class="col-customer">{{ t('orders.table.customer') }}</th>
                <th class="col-items">{{ t('orders.table.items') }}</th>
                <th class="col-status">{{ t('orders.table.status') }}</th>
                <th class="col-date">{{ t('orders.table.orderDate') }}</th>
                <th class="col-date">{{ t('orders.table.expectedDelivery') }}</th>
                <th class="col-value">{{ t('orders.table.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="col-order-number"><strong>{{ order.order_number }}</strong></td>
                <td class="col-customer">{{ translateCustomerName(order.customer) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="(item, idx) in order.items" :key="idx" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ currencySymbol }}{{ item.unit_price }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-status">
                  <span :class="['badge', getOrderStatusClass(order.status)]">
                    {{ t(`status.${order.status.toLowerCase()}`) }}
                  </span>
                </td>
                <td class="col-date">{{ formatDate(order.order_date) }}</td>
                <td class="col-date">{{ formatDate(order.expected_delivery) }}</td>
                <td class="col-value"><strong>{{ currencySymbol }}{{ order.total_value.toLocaleString() }}</strong></td>
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
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

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

    // Submitted restocking orders have their own state so a failure in either request
    // doesn't hide the other table
    const restockLoading = ref(true)
    const restockError = ref(null)
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

    // Not filter-dependent: loaded once on mount, never from the filter watcher
    const loadRestockOrders = async () => {
      try {
        restockLoading.value = true
        restockError.value = null
        restockOrders.value = await api.getRestockOrders()
      } catch (err) {
        restockError.value = 'Failed to load submitted orders: ' + err.message
      } finally {
        restockLoading.value = false
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
        'Delivered': 'success',
        'Shipped': 'info',
        'Processing': 'warning',
        'Backordered': 'danger',
        'Submitted': 'info'
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

    onMounted(() => {
      loadOrders()
      loadRestockOrders()
    })

    return {
      t,
      loading,
      error,
      orders,
      restockLoading,
      restockError,
      restockOrders,
      currentCurrency,
      formatCurrency,
      formatCurrencyWithDecimals,
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
/*
  Both order tables share these rules so they look identical. Columns size naturally
  (no fixed layout or px widths); headers may wrap so long Japanese labels fit.
*/
.restock-table {
  min-width: 860px;
}

.orders-table th {
  white-space: normal;
}

/* Keep identifiers, dates and money on one line */
.orders-table td.col-order-number,
.orders-table td.col-date,
.orders-table td.col-value {
  white-space: nowrap;
}

/* Numeric columns */
.orders-table .col-lead-time,
.orders-table .col-value {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* Submitted orders card */
.card-subtitle {
  margin-top: var(--space-1);
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

.empty-state {
  padding: var(--space-8) var(--space-4);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

/* Items details styling */
.items-details {
  position: relative;
}

.items-summary {
  cursor: pointer;
  color: var(--color-accent);
  font-weight: 500;
  list-style: none;
  user-select: none;
  display: inline-block;
}

.items-summary::-webkit-details-marker {
  display: none;
}

.items-summary::before {
  content: '▶';
  display: inline-block;
  margin-right: var(--space-1);
  font-size: var(--text-xs);
  transition: transform var(--dur) var(--ease);
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

.items-summary:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

/* Dropdown container */
.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: var(--space-2);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: var(--space-3);
  z-index: 10;
  min-width: 300px;
  max-width: 400px;
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2);
  border-bottom: 1px solid var(--color-surface-muted);
}

.item-entry:last-child {
  border-bottom: none;
}

.item-name {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--color-text);
}

.item-meta {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* .table-container is overflow-x: auto, which clips an absolutely positioned dropdown
   (and the list can be short, so it would add a scrollbar). Expand inline instead. */
.restock-table .items-dropdown {
  position: static;
  min-width: 0;
  max-width: none;
  box-shadow: none;
  padding: var(--space-2);
}
</style>
