// Simple 24x24 stroke icons for sidebar items. Each value is the `d` attribute of a single <path>.
// AppShell renders them with stroke="currentColor", so they follow the item's text color.
// Pick the closest match for each route; add more in the same style (24x24 grid, no fills).
export const navIcons = {
  dashboard: 'M3 3h7v7H3z M14 3h7v7h-7z M14 14h7v7h-7z M3 14h7v7H3z',
  inventory: 'M21 8l-9-5-9 5v8l9 5 9-5z M3 8l9 5 9-5 M12 13v8',
  orders: 'M9 4h6v3H9z M7 5H5v16h14V5h-2 M9 12h6 M9 16h6',
  finance: 'M12 3v18 M16 7.5c0-1.4-1.8-2.5-4-2.5s-4 1.1-4 2.5 1.8 2.5 4 2.5 4 1.1 4 2.5-1.8 2.5-4 2.5-4-1.1-4-2.5',
  forecast: 'M3 17l6-6 4 4 8-8 M15 7h6v6',
  restock: 'M21 12a9 9 0 1 1-3-6.7 M21 4v5h-5',
  reports: 'M6 3h9l4 4v14H6z M14 3v5h5 M9 13h6 M9 17h6',
  settings: 'M4 7h10 M18 7h2 M4 17h2 M10 17h10 M16 4v6 M8 14v6',
  users: 'M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2 M9.5 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7 M21 21v-2a4 4 0 0 0-3-3.9 M16 4.1a3.5 3.5 0 0 1 0 6.8'
}
