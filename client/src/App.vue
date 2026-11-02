<template>
  <div class="app">
    <AppShell
      :nav-items="navItems"
      :brand-name="t('nav.companyName')"
      :brand-subtitle="t('nav.subtitle')"
    >
      <template #topbar-actions>
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </template>

      <template #filters>
        <FilterBar />
      </template>

      <router-view />
    </AppShell>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import AppShell from './components/AppShell.vue'

export default {
  name: 'App',
  components: {
    AppShell,
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Sidebar entries, in display order. Labels are translated here so AppShell stays i18n-agnostic.
    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), icon: 'dashboard' },
      { to: '/inventory', label: t('nav.inventory'), icon: 'inventory' },
      { to: '/orders', label: t('nav.orders'), icon: 'orders' },
      { to: '/spending', label: t('nav.finance'), icon: 'finance' },
      { to: '/demand', label: t('nav.demandForecast'), icon: 'forecast' },
      { to: '/restocking', label: t('nav.restocking'), icon: 'restock' },
      { to: '/reports', label: t('nav.reports'), icon: 'reports' }
    ])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      navItems,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* One focus style for everything interactive */
:where(a, button, input, select, textarea, summary):focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* Page header: one per view (dark title and muted subtitle on the page; see the hero overrides below) */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  margin: 0 0 var(--space-1);
  font-size: var(--text-2xl);
  line-height: var(--leading-tight);
  letter-spacing: -0.02em;
  font-weight: 700;
}

.page-header p {
  color: var(--color-text-muted);
}

/* Inside the dark hero banner: light title and subtitle, and the hero supplies the bottom margin */
.scene-hero .page-header {
  margin-bottom: 0;
}

.scene-hero .page-header h2 {
  color: var(--sidebar-text-strong);
}

.scene-hero .page-header p {
  color: var(--sidebar-text);
}

/* Stat cards */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--dur) var(--ease), border-color var(--dur) var(--ease), transform var(--dur) var(--ease);
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.stat-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.stat-value {
  margin-top: var(--space-2);
  font-size: var(--text-3xl);
  line-height: var(--leading-tight);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-info);
}

/* Cards */
.card {
  background: var(--color-surface);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: var(--leading-tight);
}

/* Tables. Bare element selectors on purpose: the old global rules were bare too, and tables that are
   not wrapped in .table-container (for example the Spending transactions table) rely on them.
   Element specificity also lets any view's own scoped table rules win. */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-border);
}

td {
  padding: var(--space-3) var(--space-4);
  vertical-align: middle;
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
  font-variant-numeric: tabular-nums;
}

tbody tr {
  transition: background-color var(--dur-fast) var(--ease);
}

tbody tr:hover {
  background: var(--color-surface-muted);
}

tbody tr:last-child td {
  border-bottom: none;
}

/* Badges: soft background plus the dark "ink" shade so 12px text stays readable */
.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  line-height: var(--leading-tight);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
}

.badge.success,
.badge.increasing {
  background: var(--color-success-soft);
  color: var(--color-success-ink);
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-soft);
  color: var(--color-warning-ink);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-soft);
  color: var(--color-danger-ink);
}

.badge.info,
.badge.stable,
.badge.low {
  background: var(--color-info-soft);
  color: var(--color-info-ink);
}

/* Loading and error states */
.loading {
  padding: var(--space-12);
  text-align: center;
  color: var(--color-text-muted);
}

.error {
  margin: var(--space-4) 0;
  padding: var(--space-4);
  background: var(--color-danger-soft);
  border: 1px solid var(--color-danger-border);
  border-radius: var(--radius-md);
  color: var(--color-danger-ink);
}
</style>
