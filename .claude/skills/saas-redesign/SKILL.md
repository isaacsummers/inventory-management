---
name: saas-redesign
description: Redesign a Vue 3 app's UI into a modern SaaS interface with a left vertical navigation sidebar instead of a top nav bar, a consistent spacing and color token system, polished shared components, and an optional Three.js hero scene. Use when asked to modernize, restyle, or redesign a Vue 3 frontend, add a sidebar layout, or add 3D visuals to a Vue dashboard.
---

# SaaS Redesign for Vue 3

Turns a Vue 3 + vue-router app with a top nav bar into a SaaS-style interface: dark left sidebar, sticky top bar, token-driven spacing and color, consistent cards/tables/badges, and one tasteful Three.js scene.

This is a **visual refactor, not a rewrite**. Routes, API calls, state, i18n keys and business logic stay exactly as they are. If a change would alter behavior, stop and ask.

## Before you start

1. Read the project's `CLAUDE.md` files (root and `client/`). Their rules win over this skill: delegation rules (for example "any `.vue` change goes to the `vue-expert` subagent"), palette, "no emojis in UI", registry or lockfile rules, and the component style (Options-style `export default { setup() }` vs `<script setup>`).
2. Confirm it is a Vue 3 + vue-router app. If it is Vue 2, Nuxt with its own layout system, or has no router, say so and ask how to proceed.
3. Work on a branch (`git checkout -b redesign-saas`) and make sure the tree is clean or the user knows what is uncommitted.
4. Ask the user (only if not already stated): keep the current brand color or pick a new one, and whether they want the Three.js hero at all. Default: keep the brand color, include the hero.

## Workflow

### 1. Audit (read-only)

Gather facts before touching anything:

- Shell file (usually `App.vue`): nav markup, what lives in the header (language switcher, profile menu, filters), global CSS.
- Router file: the list of routes, which become sidebar items.
- Where global classes are defined (`.card`, `.stat-card`, `.badge`, `.page-header`, `.table-container`, buttons). The redesign rewrites these **in place with the same class names**, so views keep working untouched.
- Count hardcoded colors and spacing in views: `grep -rnoE "#[0-9a-fA-F]{3,6}\b" src | wc -l`, and `grep -rnE "(padding|margin|gap):" src`.
- Translation setup: are nav labels translated? Any hardcoded labels (these are bugs; fix them while moving them into the sidebar)?
- Existing modals, sticky or fixed elements that may collide with a fixed sidebar (check `z-index` values and `position: fixed`).

Summarize the audit to the user in a few lines before step 2.

### 2. Design tokens

Copy `templates/design-tokens.css` to `src/styles/design-tokens.css` and import it first in `main.js`.

- Re-point `--color-accent`, `--color-accent-hover`, `--color-accent-soft` at the app's **existing** brand color. Keep status colors if the app already has a convention.
- Keep `--color-text-muted` at 4.5:1 or better on its background. Do not lighten it.
- From now on, **no raw hex colors and no raw px/rem spacing in anything you write or edit.** Use tokens.

### 3. Sidebar shell

1. Copy `templates/AppShell.vue.tpl` to `src/components/AppShell.vue` and `templates/navIcons.js` to `src/utils/navIcons.js`. Fix the import path inside the component. Adapt the script block to the project's component style.
2. Rewrite the shell (`App.vue`) to render `<AppShell>`:
   - `navItems` is a `computed` built from the router's routes with **translated** labels (`{ to, label, icon }`). Map each route to the closest icon in `navIcons`; add new icons in the same 24x24 stroke style if needed.
   - Move the language switcher and profile menu into the `topbar-actions` slot. Move the global filter bar into the `filters` slot. Keep their logic and events unchanged.
   - Pass the brand name and subtitle through the props.
   - Put the app's existing `<router-view />` in the default slot.
3. Delete the old top-nav markup and its CSS from the shell. Do not leave dead styles behind.
4. Check that modals still sit above the sidebar. The sidebar is `z-index: 40`, top bar `30`; modals must be higher. Raise modal z-index if they are lower, using one shared value.

Behavior the shell must keep: active-route highlight, keyboard operable (Tab order, visible focus), a skip link, collapsible rail on desktop (persisted, with `try/catch` around storage), off-canvas drawer under 900px, `Escape` closes the drawer, `aria-expanded` on the toggles.

### 4. Shared primitives

Open `templates/primitives.css` as a **reference**. In the app's existing global stylesheet, rewrite the rules for `.page-header`, `.stats-grid`, `.stat-card`, `.card`, `.card-header`, `.table-container`, `.badge`, buttons, inputs, and the focus ring so they use tokens and match the reference. Keep existing class names and any modifier classes the views use (`.success`, `.warning`, `.increasing`, ...). If a view relies on a class the reference omits, keep it and tokenize it.

Rules for the look:
- One page title per view (`.page-header h2`), 24px, tight tracking.
- Cards: 1px border, `--radius-lg`, `--shadow-sm`, `--space-6` padding. Stat cards slightly smaller radius.
- Table headers small, uppercase, muted, on `--color-surface-muted`. Numbers use `font-variant-numeric: tabular-nums` and are right-aligned.
- Vertical rhythm: `--space-6` between cards and sections, `--space-4` between related controls, `--space-8` page padding (16px on mobile).
- Hover and focus transitions use `--dur` and `--ease` only. Nothing slower than 200ms.
- No emojis anywhere in the UI. Icons are stroke SVGs.

### 5. Normalize the views

For each view, remove styles that fight the new system:

- Replace raw colors and spacing with tokens (mechanical; do it with search and replace per file, then read the diff).
- Delete per-view rules that re-declare `.card`, `.badge`, buttons or headings differently from the global ones.
- Remove each view's own outer padding or `max-width` (the shell's content area owns those).
- Keep view-specific layout (grids, chart wrappers) and domain colors (for example chart series colors). Only change a chart color if it is a plain neutral that should follow the tokens.
- Do not restructure templates unless a view is visibly broken by the new shell.

If the project requires delegation for `.vue` edits (this repo does), give the `vue-expert` subagent a self-contained brief per batch of views: which tokens exist, which rules to delete, what must not change (logic, i18n keys, class names used by tests).

### 6. Three.js hero (optional, one scene only)

Purpose: a single memorable moment on the overview page. It is decoration, never data.

1. `npm install three` in the client (respect the project's registry rules; in this repo `client/.npmrc` pins the public registry and the lockfile is gitignored, so do not commit either). Check the resolved version is current and that `package.json` gains only the `three` dependency.
2. Copy `templates/SceneHero.vue.tpl` to `src/components/SceneHero.vue`.
3. Use it on the overview/dashboard view only, as the page header: put the title and subtitle in its default slot, and remove the view's old `.page-header`.
4. Do not add more scenes. If the user wants more 3D, extend this one (for example colors from live status counts passed as a prop), do not add canvases to other pages.

Non-negotiables, all already implemented in the template. Keep them if you modify it:
- `three` is imported dynamically (`await import('three')`), so it ships as a separate chunk.
- Pauses offscreen (IntersectionObserver) and when the tab is hidden; renders a single still frame under `prefers-reduced-motion`.
- Falls back to a CSS gradient if WebGL is unavailable or init throws.
- Disposes geometries, materials, renderer, observers and listeners on unmount; calls `forceContextLoss`.
- Pixel ratio capped at 2; `powerPreference: 'low-power'`; no per-frame allocations.
- Text sits on a gradient shade so contrast never depends on the animation.
- The canvas is `aria-hidden`; nothing essential is rendered only in WebGL.

### 7. Responsive and dark mode

- Under 900px the sidebar becomes a drawer opened by the menu button. Verify tables scroll inside `.table-container` instead of widening the page.
- Dark mode is optional: only add it if the project already supports it or the user asks. If so, redefine the surface/text tokens under `@media (prefers-color-scheme: dark)` and keep the sidebar as is.

## Verify (do all of these, report results honestly)

1. **Build:** `npm run build` passes. Note the size of the `three` chunk, and confirm it is NOT in the main entry chunk.
2. **Run the app and look at it** with Playwright (or the project's preferred browser tool), at 1440, 1024 and 390px wide. For every route: screenshot, then check no horizontal page scroll, no overlapping header or sidebar, no clipped modals.
3. **Navigation:** click every sidebar item; active state follows the route; collapse/expand persists across reload; drawer opens, closes on scrim click, `Escape` and route change.
4. **Keyboard:** Tab through sidebar and top bar; focus ring is visible on every stop; skip link works.
5. **Console:** no new errors or warnings from the redesign. Pre-existing errors: list them separately and do not "fix" them silently.
6. **3D:** scene animates; scrolling it out of view stops the animation loop; emulate `prefers-reduced-motion: reduce` and confirm a still frame; disable WebGL (or force the failure path) and confirm the gradient fallback; navigate away and back several times and confirm no growth in canvases or WebGL-context warnings.
7. **i18n:** if the app has locales, switch each and check sidebar labels fit and nothing hardcoded remains. Long labels truncate with an ellipsis and have a `title` when the rail is collapsed.
8. **Regression:** existing tests still pass; filters, forms and modals behave as before.
9. **Leftovers:** `grep` for the removed top-nav classes and for raw hex colors or px spacing in files you touched.

## Report to the user

Say what changed (files, new components, tokens), what you verified and how, and what you did NOT verify. Call out anything you chose not to change (domain chart colors, pre-existing bugs found) and any behavior you noticed was already broken. Do not commit unless asked.

## Pitfalls

- A fixed sidebar plus `position: fixed` modals or toasts from the old layout: re-check z-index and left offsets.
- Views that set their own `min-height: 100vh` or padding create double scrollbars or double gutters inside the shell.
- Sticky table headers or filter bars that used `top: <old nav height>`: update them to `var(--topbar-h)`.
- Using `100vh` on mobile: prefer `100dvh` if a view needs full height.
- Do not animate the sidebar with `left`; the template uses `transform` and `width` only.
- Do not import all of `three/examples`. If an addon is truly needed, import that one module.
- Do not render the scene on every page, in a loop of cards, or behind data tables. One scene, one page.
- Do not swap the app's brand color for generic blue unless the app was already that blue.
