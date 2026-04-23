# Car Repair Management Frontend

A MoveX-inspired Vue 3 + TypeScript frontend for the Car Repair Management Frappe app.

## Features

- **MoveX-inspired UI**: Modern card-based layout with sidebar navigation
- **Light/Dark/System themes**: Persisted theme preference with system detection
- **Fully responsive**: Mobile drawer, tablet collapsible, desktop fixed sidebar
- **Schema discovery**: Auto-introspects Frappe backend DocTypes and fields
- **Domain model mappings**: Stable UI keys mapped to actual fieldnames

## Tech Stack

- **Vue 3** with Composition API + TypeScript
- **frappe-ui** for Frappe API integration
- **Pinia** for state management
- **Vue Router** for navigation
- **Tailwind CSS** for styling
- **Lucide Vue** for icons

## Development

### Prerequisites

- Node.js 18+
- pnpm or npm
- Frappe bench with `car_repair_management` app installed

### Setup

```bash
cd apps/car_repair_management/frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

This starts the Vite dev server on port 8080 with proxying to Frappe at port 8000.

Access the app at: `http://<site>:8080/workshop`

### Build for Production

```bash
npm run build
```

This builds assets to `car_repair_management/public/frontend/` and copies the entry HTML.

After building, run:

```bash
bench build --app car_repair_management
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # Frappe REST client wrapper
│   │   ├── client.ts     # apiList, apiGet, apiCreate, apiUpdate, apiDelete
│   │   └── index.ts
│   ├── components/
│   │   ├── layouts/      # AppLayout, Sidebar, Topbar, MobileSidebar
│   │   └── ui/           # Button, Card, Badge, Input, Tabs, etc.
│   ├── pages/
│   │   ├── auth/         # Login, ForgotPassword
│   │   ├── repair-orders/# RepairOrderList, RepairOrderDetail
│   │   ├── vehicles/     # VehicleList, VehicleDetail
│   │   ├── customers/    # CustomerList, CustomerDetail
│   │   ├── Dashboard.vue
│   │   ├── Tasks.vue
│   │   ├── Invoices.vue
│   │   ├── Reports.vue
│   │   ├── Settings.vue
│   │   └── NotFound.vue
│   ├── schema/           # Schema discovery module
│   │   ├── types.ts      # TypeScript interfaces
│   │   ├── discovery.ts  # DocType introspection
│   │   ├── mappings.ts   # Domain model mappers
│   │   └── index.ts
│   ├── stores/           # Pinia stores
│   │   ├── session.ts    # Auth state
│   │   ├── theme.ts      # Theme preference
│   │   ├── schema.ts     # Schema registry
│   │   └── index.ts
│   ├── types/            # Shared TypeScript types
│   ├── App.vue           # Root component
│   ├── main.ts           # Entry point
│   ├── router.ts         # Vue Router config
│   └── index.css         # Global styles + Tailwind
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Schema Discovery

The app auto-discovers the Frappe backend schema on startup:

1. **Attempts DocType metadata fetch** via `/api/resource/DocType/{name}`
2. **Falls back to inference** from list endpoint responses if blocked
3. **Caches results** in localStorage (refreshes hourly)

### Regenerating Schema

In the Settings page, use the hidden "Regenerate mappings" action (admin only) or clear localStorage and refresh.

### Adding a New Page

1. Add route in `src/router.ts`
2. Create page component in `src/pages/`
3. Add navigation item in `src/components/layouts/Sidebar.vue` with optional `doctype` for schema-gating
4. If the page depends on a DocType, set `doctype: 'DocType Name'` in the nav item - it will hide automatically if the DocType doesn't exist

## Theming

The app uses CSS custom properties for theming, with Tailwind semantic classes:

- **Light mode**: Default
- **Dark mode**: Add `.dark` class to `<html>`
- **System mode**: Auto-detects and follows OS preference

Theme toggle is in the Topbar and Settings page.

### Color tokens

- `bg-surface-light-*` / `bg-surface-dark-*` - Background surfaces
- `text-ink-light-*` / `text-ink-dark-*` - Text colors
- `border-border-light` / `border-border-dark` - Borders
- `bg-primary-*` - Primary purple accent

## API Binding

All API calls go through `src/api/client.ts`:

```typescript
import { apiList, apiGet, apiCreate, apiUpdate, apiDelete, apiCall } from '@/api'

// List documents
const orders = await apiList({
  doctype: 'Repair Order',
  fields: ['name', 'status', 'customer'],
  filters: { status: 'In Progress' },
  orderBy: 'modified desc',
  limitPageLength: 20,
})

// Get single document
const order = await apiGet('Repair Order', 'RO-2024-00001')

// Create document
await apiCreate('Repair Order', { customer: 'C-001', vehicle: 'V-001' })

// Update document
await apiUpdate('Repair Order', 'RO-2024-00001', { status: 'Closed' })

// Delete document
await apiDelete('Repair Order', 'RO-2024-00001')

// Call whitelisted method
await apiCall('car_repair_management...make_quotation_from_repair_order', { name: 'RO-2024-00001' })
```

## Feature Gating

Pages and navigation items are hidden if:

1. The required DocType doesn't exist in the schema
2. The user doesn't have read permission

This is handled by the `useSchemaStore().hasDoctype()` check in `Sidebar.vue`.

## Browser Support

- Chrome/Edge 88+
- Firefox 78+
- Safari 14+
- Mobile Safari/Chrome

## License

MIT
