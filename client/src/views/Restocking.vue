<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
      <p class="filters-note">{{ t('restocking.filtersNotApplied') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-header">
          <label for="restock-budget" class="budget-label">{{ t('restocking.budget') }}</label>
          <div class="budget-value">{{ formatMoney(budgetValue) }}</div>
        </div>
        <input
          id="restock-budget"
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          :max="maxBudget"
          :step="BUDGET_STEP"
          :disabled="maxBudget === 0"
          :aria-valuetext="formatMoney(budgetValue)"
        />
        <div class="budget-scale">
          <span>{{ formatMoney(0) }}</span>
          <span>{{ t('restocking.budgetMax') }}: {{ formatMoney(maxBudget) }}</span>
        </div>
        <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.allocated') }}</div>
          <div class="stat-value">{{ formatMoneyExact(allocated) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatMoneyExact(remaining) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.orderLeadTime') }}</div>
          <div class="stat-value">
            <template v-if="orderLeadTime !== null">{{ t('restocking.leadTimeDays', { days: orderLeadTime }) }}</template>
            <template v-else>&mdash;</template>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header rec-header">
          <div class="rec-heading">
            <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
            <p class="card-hint">{{ t('restocking.recommendationsHint') }}</p>
          </div>
          <button
            type="button"
            class="place-order-btn"
            :disabled="recommendations.length === 0 || placing"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="orderResult" class="success-banner" role="status">
          <span>{{ t('restocking.orderPlaced', { number: orderResult.order_number, days: orderResult.lead_time_days }) }}</span>
          <router-link to="/orders" class="banner-link">{{ t('restocking.viewInOrders') }}</router-link>
        </div>
        <div v-if="orderError" class="error" role="alert">
          {{ t('restocking.orderFailed') }}: {{ orderError }}
        </div>

        <div v-if="candidates.length === 0" class="empty-state">{{ t('restocking.noShortfall') }}</div>
        <div v-else-if="recommendations.length === 0" class="empty-state">{{ t('restocking.noBudget') }}</div>
        <div v-else class="table-container">
          <table class="rec-table">
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.onHand') }}</th>
                <th class="num">{{ t('restocking.table.forecast') }}</th>
                <th class="num">{{ t('restocking.table.shortfall') }}</th>
                <th class="num">{{ t('restocking.table.orderQty') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recommendations" :key="row.sku">
                <td><strong>{{ row.sku }}</strong></td>
                <td>{{ translateProductName(row.name) }}</td>
                <td>
                  <span :class="['badge', row.trend]">
                    {{ t(`trends.${row.trend}`) }}
                  </span>
                </td>
                <td class="num">{{ row.onHand }}</td>
                <td class="num">{{ row.forecast }}</td>
                <td class="num">{{ row.shortfall }}</td>
                <td class="num">
                  <strong>{{ row.orderQty }}</strong>
                  <span v-if="row.partial" class="badge warning partial-badge">{{ t('restocking.partial') }}</span>
                </td>
                <td class="num">{{ formatMoneyExact(row.unitCost) }}</td>
                <td class="num"><strong>{{ formatMoneyExact(row.lineCost) }}</strong></td>
                <td class="num">{{ t('restocking.leadTimeDays', { days: row.leadTimeDays }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_STEP = 500
const DEFAULT_BUDGET = 10000

const toCents = (amount) => Math.round(amount * 100)

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])

    const budget = ref(DEFAULT_BUDGET)

    const placing = ref(false)
    const orderResult = ref(null)
    const orderError = ref(null)

    // Whole-dollar display (slider values) and cents display (costs and totals)
    const formatMoney = (amountUsd) => formatCurrency(amountUsd, currentCurrency.value)
    const formatMoneyExact = (amountUsd) => formatCurrencyWithDecimals(amountUsd, currentCurrency.value, 2)

    // Items forecast to sell more than is on hand, in funding priority order:
    // increasing demand first, then largest shortfall, then SKU ascending.
    const candidates = computed(() => {
      return forecasts.value
        .map(f => {
          const onHand = Number(f.quantity_on_hand) || 0
          const forecast = Number(f.forecasted_demand) || 0
          return {
            sku: f.item_sku,
            name: f.item_name,
            trend: f.trend,
            onHand,
            forecast,
            shortfall: Math.max(0, forecast - onHand),
            unitCost: Number(f.unit_cost) || 0,
            unitCents: toCents(Number(f.unit_cost) || 0),
            leadTimeDays: Number(f.lead_time_days) || 0
          }
        })
        .filter(c => c.shortfall > 0)
        .sort((a, b) => {
          const aInc = a.trend === 'increasing' ? 1 : 0
          const bInc = b.trend === 'increasing' ? 1 : 0
          if (aInc !== bInc) return bInc - aInc
          if (a.shortfall !== b.shortfall) return b.shortfall - a.shortfall
          if (a.sku === b.sku) return 0
          return a.sku < b.sku ? -1 : 1
        })
    })

    // Slider max: cost of the full shortfall of every candidate, rounded up to the next step
    const maxBudget = computed(() => {
      const fullCents = candidates.value.reduce((sum, c) => sum + c.shortfall * c.unitCents, 0)
      return Math.ceil(fullCents / (BUDGET_STEP * 100)) * BUDGET_STEP
    })

    // Budget actually used for calculations, always within [0, maxBudget]
    const budgetValue = computed(() => {
      const value = Number(budget.value)
      if (!Number.isFinite(value)) return 0
      return Math.min(Math.max(0, value), maxBudget.value)
    })

    // Greedy fill in integer cents so the total can never exceed the budget through float drift
    const allocation = computed(() => {
      const budgetCents = toCents(budgetValue.value)
      let remainingCents = budgetCents
      const rows = []

      for (const c of candidates.value) {
        const affordable = c.unitCents > 0 ? Math.floor(remainingCents / c.unitCents) : c.shortfall
        const qty = Math.min(c.shortfall, affordable)
        if (qty <= 0) break

        const lineCents = qty * c.unitCents
        remainingCents -= lineCents
        rows.push({
          sku: c.sku,
          name: c.name,
          trend: c.trend,
          onHand: c.onHand,
          forecast: c.forecast,
          shortfall: c.shortfall,
          orderQty: qty,
          unitCost: c.unitCost,
          lineCost: lineCents / 100,
          leadTimeDays: c.leadTimeDays,
          partial: qty < c.shortfall
        })

        // A partly funded item is the last one
        if (qty < c.shortfall) break
      }

      return {
        rows,
        allocatedCents: budgetCents - remainingCents,
        remainingCents
      }
    })

    const recommendations = computed(() => allocation.value.rows)
    const allocated = computed(() => allocation.value.allocatedCents / 100)
    const remaining = computed(() => allocation.value.remainingCents / 100)

    const orderLeadTime = computed(() => {
      if (recommendations.value.length === 0) return null
      return Math.max(...recommendations.value.map(r => r.leadTimeDays))
    })

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        // Default budget, clamped to what the slider can reach
        budget.value = Math.min(DEFAULT_BUDGET, maxBudget.value)
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const getErrorDetail = (err) => {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string' && detail) return detail
      if (Array.isArray(detail) && detail.length > 0) {
        return detail.map(d => d.msg || JSON.stringify(d)).join('; ')
      }
      return err.message
    }

    const placeOrder = async () => {
      if (placing.value || recommendations.value.length === 0) return

      // Snapshot the payload so slider changes during the request don't alter it
      const payload = {
        items: recommendations.value.map(r => ({ sku: r.sku, quantity: r.orderQty })),
        budget: budgetValue.value
      }

      orderResult.value = null
      orderError.value = null
      placing.value = true
      try {
        orderResult.value = await api.createRestockOrder(payload)
      } catch (err) {
        orderError.value = getErrorDetail(err)
        console.error('Place order error:', err)
      } finally {
        placing.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      BUDGET_STEP,
      loading,
      error,
      budget,
      budgetValue,
      maxBudget,
      candidates,
      recommendations,
      allocated,
      remaining,
      orderLeadTime,
      placing,
      orderResult,
      orderError,
      placeOrder,
      formatMoney,
      formatMoneyExact,
      translateProductName
    }
  }
}
</script>

<style scoped>
.filters-note {
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
  font-style: italic;
}

/* Budget control */
.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.budget-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  display: block;
  width: 100%;
  height: 1.5rem;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-slider:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 0.25rem;
  font-size: 0.813rem;
  color: #64748b;
}

.budget-hint {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: #64748b;
}

/* Order banners */
.success-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 0 0 1rem;
  font-size: 0.938rem;
}

.banner-link {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
}

.banner-link:hover {
  color: #064e3b;
}

/* Recommendations card */
.rec-header {
  flex-wrap: wrap;
  gap: 1rem;
}

.rec-heading {
  flex: 1 1 320px;
  min-width: 0;
}

.card-hint {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: #64748b;
}

.place-order-btn {
  padding: 0.625rem 1.25rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  color: #64748b;
  cursor: not-allowed;
}

.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Keep the table scrollable instead of squashed on narrow screens */
.rec-table {
  min-width: 920px;
}

.rec-table th.num,
.rec-table td.num {
  text-align: right;
  white-space: nowrap;
}

.partial-badge {
  margin-left: 0.5rem;
  padding: 0.125rem 0.5rem;
  font-size: 0.688rem;
}
</style>
