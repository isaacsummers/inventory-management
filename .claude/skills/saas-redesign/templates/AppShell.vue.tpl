<!--
  AppShell: vertical-sidebar layout. Copy to src/components/AppShell.vue.

  ADAPT BEFORE USE
  1. Fix the navIcons import path below.
  2. The parent (App.vue) passes `navItems` with labels already translated, so this component
     stays i18n-agnostic:
       const navItems = computed(() => [{ to: '/', label: t('nav.overview'), icon: 'dashboard' }, ...])
  3. Match the app's component style. This repo uses `export default { setup() }`, not <script setup>.
  4. Slots keep the app's own logic (language switcher, profile menu, global filters, modals) in App.vue.
-->
<template>
  <div class="shell" :class="{ collapsed, 'drawer-open': drawerOpen }">
    <a class="skip-link" href="#main-content">Skip to content</a>

    <aside id="app-sidebar" class="sidebar" aria-label="Primary">
      <div class="sidebar-brand">
        <slot name="brand">
          <span class="brand-mark" aria-hidden="true">{{ brandName.charAt(0) }}</span>
          <span class="brand-text">
            <span class="brand-name">{{ brandName }}</span>
            <span v-if="brandSubtitle" class="brand-subtitle">{{ brandSubtitle }}</span>
          </span>
        </slot>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          active-class="active"
          :title="collapsed ? item.label : null"
        >
          <svg
            class="nav-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path :d="navIcons[item.icon] || navIcons.dashboard" />
          </svg>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <button
          type="button"
          class="collapse-btn"
          :aria-expanded="String(!collapsed)"
          aria-controls="app-sidebar"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="toggleCollapsed"
        >
          <svg class="nav-icon chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M15 6l-6 6 6 6" />
          </svg>
          <span class="nav-label">{{ collapsed ? 'Expand' : 'Collapse' }}</span>
        </button>
      </div>
    </aside>

    <div class="scrim" aria-hidden="true" @click="drawerOpen = false"></div>

    <div class="shell-main">
      <header class="topbar">
        <button
          type="button"
          class="menu-btn"
          aria-controls="app-sidebar"
          :aria-expanded="String(drawerOpen)"
          aria-label="Open navigation"
          @click="drawerOpen = true"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
            <path d="M4 7h16 M4 12h16 M4 17h16" />
          </svg>
        </button>
        <div class="topbar-start"><slot name="topbar-start" /></div>
        <div class="topbar-actions"><slot name="topbar-actions" /></div>
      </header>

      <slot name="filters" />

      <main id="main-content" class="content" tabindex="-1">
        <div class="content-inner"><slot /></div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { navIcons } from '../utils/navIcons' // <- adjust path

const STORAGE_KEY = 'shell-collapsed'

export default {
  name: 'AppShell',
  props: {
    navItems: { type: Array, required: true }, // [{ to, label, icon }]
    brandName: { type: String, default: 'App' },
    brandSubtitle: { type: String, default: '' }
  },
  setup() {
    const route = useRoute()
    const collapsed = ref(false)
    const drawerOpen = ref(false)

    try {
      collapsed.value = localStorage.getItem(STORAGE_KEY) === '1'
    } catch (e) {
      // storage unavailable (private mode, blocked): fall back to expanded
    }

    const toggleCollapsed = () => {
      collapsed.value = !collapsed.value
      try {
        localStorage.setItem(STORAGE_KEY, collapsed.value ? '1' : '0')
      } catch (e) {
        // ignore
      }
    }

    // Close the mobile drawer after navigating
    watch(() => route.path, () => { drawerOpen.value = false })

    const onKeydown = (e) => {
      if (e.key === 'Escape') drawerOpen.value = false
    }
    onMounted(() => window.addEventListener('keydown', onKeydown))
    onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

    return { navIcons, collapsed, drawerOpen, toggleCollapsed }
  }
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  background: var(--color-bg);
}

.skip-link {
  position: fixed;
  top: var(--space-2);
  left: var(--space-2);
  z-index: 100;
  padding: var(--space-2) var(--space-4);
  background: var(--color-accent);
  color: var(--color-accent-contrast);
  border-radius: var(--radius-sm);
  transform: translateY(-200%);
}
.skip-link:focus { transform: translateY(0); }

/* Sidebar */
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 40;
  width: var(--sidebar-w);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-3);
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  transition: width var(--dur) var(--ease), transform var(--dur) var(--ease);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--sidebar-border);
  min-height: var(--topbar-h);
  box-sizing: border-box;
}
.brand-mark {
  flex: none;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
  color: var(--color-accent-contrast);
  font-weight: 700;
}
.brand-text { display: flex; flex-direction: column; min-width: 0; }
.brand-name {
  color: var(--sidebar-text-strong);
  font-weight: 700;
  line-height: var(--leading-tight);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.brand-subtitle {
  font-size: var(--text-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  overflow-y: auto;
}

.nav-item,
.collapse-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--sidebar-text);
  font: inherit;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease), color var(--dur-fast) var(--ease);
}
.nav-item { min-height: 40px; box-sizing: border-box; }
.nav-item:hover,
.collapse-btn:hover {
  background: var(--sidebar-hover);
  color: var(--sidebar-text-strong);
}
.nav-item.active {
  background: var(--sidebar-active);
  color: var(--sidebar-text-strong);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: var(--space-2);
  bottom: var(--space-2);
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--color-accent);
}
.nav-item:focus-visible,
.collapse-btn:focus-visible { outline-offset: -2px; }

.nav-icon { flex: none; width: 20px; height: 20px; }
.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-footer {
  padding-top: var(--space-3);
  border-top: 1px solid var(--sidebar-border);
}
.collapse-btn { width: 100%; }
.chevron { transition: transform var(--dur) var(--ease); }

/* Main column */
.shell-main {
  min-width: 0;
  min-height: 100vh;
  margin-left: var(--sidebar-w);
  display: flex;
  flex-direction: column;
  transition: margin-left var(--dur) var(--ease);
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: var(--space-4);
  height: var(--topbar-h);
  padding: 0 var(--space-8);
  box-sizing: border-box;
  background: color-mix(in srgb, var(--color-surface) 88%, transparent);
  backdrop-filter: saturate(1.4) blur(8px);
  border-bottom: 1px solid var(--color-border);
}
.topbar-start { flex: 1; min-width: 0; }
.topbar-actions { display: flex; align-items: center; gap: var(--space-3); }

.menu-btn {
  display: none;
  padding: var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
}

.content { flex: 1; padding: var(--space-8); outline: none; }
.content-inner { max-width: var(--content-max); margin: 0 auto; }

.scrim { display: none; }

/* Desktop: collapsible rail */
@media (min-width: 901px) {
  .shell.collapsed .sidebar { width: var(--sidebar-w-collapsed); }
  .shell.collapsed .shell-main { margin-left: var(--sidebar-w-collapsed); }
  .shell.collapsed .brand-text,
  .shell.collapsed .nav-label { display: none; }
  .shell.collapsed .sidebar-brand,
  .shell.collapsed .nav-item,
  .shell.collapsed .collapse-btn { justify-content: center; padding-left: 0; padding-right: 0; }
  .shell.collapsed .chevron { transform: rotate(180deg); }
}

/* Mobile and tablet: off-canvas drawer */
@media (max-width: 900px) {
  .sidebar { transform: translateX(-100%); box-shadow: var(--shadow-lg); }
  .shell.drawer-open .sidebar { transform: translateX(0); }
  .shell-main { margin-left: 0; }
  .menu-btn { display: inline-flex; }
  .collapse-btn { display: none; }
  .topbar { padding: 0 var(--space-4); }
  .content { padding: var(--space-4); }
  .shell.drawer-open .scrim {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 35;
    background: rgba(15, 23, 42, 0.5);
  }
}
</style>
