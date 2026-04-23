# Frontend Developer Guide

## Technology Stack

| Technology | Purpose |
|---|---|
| Vue 3 | UI framework (Composition API with `<script setup>`) |
| TypeScript | Type safety |
| Vite | Build tool |
| Tailwind CSS | Utility-first styling with semantic CSS custom properties |
| Vue Router | Client-side routing (history mode, base: `/workshop`) |
| Vue I18n | Internationalization (7 languages) |
| Lucide Vue | Icon library (exclusively, never FeatherIcon) |
| Pinia | State management |

## Project Structure

```
frontend/src/
├── api/
│   └── client.ts                 # API client wrapper
├── components/
│   ├── ui/                       # 12 reusable UI primitives
│   │   ├── Badge.vue             # Status badges (variant: success/danger/warning/info/primary/default)
│   │   ├── Button.vue            # Buttons (variant: primary/secondary/outline/danger/ghost, size, loading)
│   │   ├── Card.vue              # Card containers (hoverable, padding="none" for tables)
│   │   ├── Chart.vue             # Chart wrapper
│   │   ├── ConfirmModal.vue      # Confirmation dialog with optional reason textarea
│   │   ├── EmptyState.vue        # Empty state with title + description
│   │   ├── Input.vue             # Form inputs
│   │   ├── LinkField.vue         # Frappe DocType search dropdown (uses apiSearchLink)
│   │   ├── Skeleton.vue          # Loading skeleton placeholder
│   │   ├── Tabs.vue              # Tab navigation
│   │   ├── ViewToggle.vue        # List/Grid view toggle
│   │   └── index.ts              # Barrel exports
│   ├── common/
│   │   └── ActivityTimeline.vue  # Audit trail + comments timeline
│   └── layouts/
│       ├── AppLayout.vue         # Main layout (sidebar + content area)
│       ├── Sidebar.vue           # Desktop navigation sidebar
│       ├── MobileSidebar.vue     # Mobile drawer navigation
│       ├── Topbar.vue            # Top bar with search, notifications, user menu
│       └── index.ts
├── pages/                        # 13 feature modules
│   ├── auth/                     # Login.vue, ForgotPassword.vue
│   ├── repair-orders/            # RepairOrderList, RepairOrderForm, RepairOrderDetail, OperationDetail
│   ├── vehicles/                 # VehicleList, VehicleForm, VehicleDetail, + sub-pages + 10 tabs
│   │   └── tabs/                 # SpecsTab, ServiceHistoryTab, WorkOrdersTab, InspectionHistoryTab,
│   │                             # IssuesTab, FinancialsTab, FuelQuotaTab, ServiceRemindersTab,
│   │                             # SensorDataTab, AttachmentsTab
│   ├── customers/                # CustomerList, CustomerDetail
│   ├── employees/                # EmployeeList, EmployeeDetail
│   ├── inspections/              # InspectionHistory, InspectionDetail, Schedules, ScheduleDetail,
│   │                             # Forms, FormDetail, ItemFailure, ItemFailureDetail
│   ├── issues/                   # IssueList, IssueForm, IssueDetail, Faults, FaultDetail, Recalls, RecallDetail
│   ├── expenses/                 # ExpenseList, ExpenseForm, ExpenseDetail
│   ├── fuel/                     # FuelList, FuelForm, FuelDetail, FuelQuotaList
│   ├── parts/                    # PartList, PartForm, PartDetail
│   ├── invoices/                 # InvoiceList, InvoiceDetail
│   ├── reports/                  # Overview, Library, ReportView, SavedReports, ScheduledReports
│   ├── settings/                 # SettingsHome, SettingsCategory
│   ├── Dashboard.vue             # Main dashboard with KPIs + status charts
│   ├── Tasks.vue                 # Task management board
│   └── NotFound.vue              # 404 page
├── stores/
│   ├── session.ts                # Auth state (isLoggedIn, user, login/logout)
│   ├── theme.ts                  # Dark/light mode (persisted to localStorage)
│   ├── schema.ts                 # DocType metadata cache
│   └── index.ts
├── locales/                      # 7 language files
│   ├── en.ts                     # English (primary)
│   ├── am.ts                     # Amharic
│   ├── fr.ts                     # French
│   ├── ar.ts                     # Arabic
│   ├── ti.ts                     # Tigrinya
│   ├── om.ts                     # Oromo
│   ├── rw.ts                     # Kinyarwanda
│   └── index.ts
├── types/                        # TypeScript type definitions
├── router.ts                     # 50+ route definitions
├── App.vue                       # Root component
├── main.ts                       # App bootstrap
└── index.css                     # Tailwind config + CSS custom properties
```

## Routing

All routes are defined in `router.ts` with Vue Router in history mode, base path `/workshop`.

### Route Map

| Path | Component | Description |
|---|---|---|
| `/` | Dashboard.vue | Main dashboard |
| `/repair-orders` | RepairOrderList.vue | RO list with KPIs |
| `/repair-orders/new` | RepairOrderForm.vue | Create new RO |
| `/repair-orders/:id` | RepairOrderDetail.vue | RO detail |
| `/repair-orders/:id/edit` | RepairOrderForm.vue | Edit RO |
| `/repair-orders/:roId/operations/:opId` | OperationDetail.vue | Operation detail |
| `/vehicles` | VehicleList.vue | Vehicle fleet list |
| `/vehicles/new` | VehicleForm.vue | Create vehicle |
| `/vehicles/assignments` | VehicleAssignments.vue | Driver assignment management |
| `/vehicles/meter-history` | MeterHistory.vue | Odometer readings |
| `/vehicles/expense-history` | ExpenseHistory.vue | Fleet expense analysis |
| `/vehicles/replacement-analysis` | ReplacementAnalysis.vue | Replacement scoring |
| `/vehicles/aging-analysis` | AgingAnalysis.vue | Fleet aging analysis |
| `/vehicles/:id` | VehicleDetail.vue | Vehicle detail (10 tabs) |
| `/vehicles/:id/edit` | VehicleForm.vue | Edit vehicle |
| `/customers` | CustomerList.vue | Customer list |
| `/customers/:id` | CustomerDetail.vue | Customer detail |
| `/employees` | EmployeeList.vue | Employee list |
| `/employees/:id` | EmployeeDetail.vue | Employee detail with assignments |
| `/tasks` | Tasks.vue | Task board |
| `/inspections` | InspectionHistory.vue | Inspection history |
| `/inspections/:id` | InspectionDetail.vue | Inspection detail |
| `/inspections/item-failures` | ItemFailure.vue | Failure tracking |
| `/inspections/schedules` | Schedules.vue | Schedule management |
| `/inspections/forms` | Forms.vue | Form templates |
| `/issues` | IssueList.vue | Issue list |
| `/issues/new` | IssueForm.vue | Create issue |
| `/issues/:id` | IssueDetail.vue | Issue detail with workflow |
| `/issues/faults` | Faults.vue | Fault codes |
| `/issues/recalls` | Recalls.vue | Recall notices |
| `/expenses` | ExpenseList.vue | Expense list |
| `/expenses/new` | ExpenseForm.vue | Create expense |
| `/expenses/:id` | ExpenseDetail.vue | Expense detail |
| `/fuel` | FuelList.vue | Refueling records |
| `/fuel/new` | FuelForm.vue | New refueling |
| `/fuel/quotas` | FuelQuotaList.vue | Quota management |
| `/fuel/:id` | FuelDetail.vue | Refueling detail |
| `/parts` | PartList.vue | Parts/inventory |
| `/invoices` | InvoiceList.vue | Invoice list |
| `/reports` | Overview.vue | Report dashboard |
| `/reports/library` | Library.vue | 30+ report library |
| `/reports/saved` | SavedReports.vue | User saved reports |
| `/reports/scheduled` | ScheduledReports.vue | Scheduled reports |
| `/reports/view/:id` | ReportView.vue | Execute/view report |
| `/settings` | SettingsHome.vue | Settings hub |
| `/settings/:category` | SettingsCategory.vue | Category settings |
| `/auth/login` | Login.vue | Login (public) |
| `/auth/forgot` | ForgotPassword.vue | Password reset (public) |

### Auth Guard

The router's `beforeEach` guard checks `sessionStore.isLoggedIn`. Unauthenticated users are redirected to `/login?redirect-to=/workshop`. Public routes (`meta: { public: true }`) bypass this check.

## API Client (`api/client.ts`)

### Core Functions

```typescript
// Base HTTP wrapper with CSRF token handling
frappeRequest(options: { url, method, params?, body? }): Promise<any>

// Call a whitelisted Python method
apiCall<T>(method: string, args?: Record<string, unknown>): Promise<T>
// Example: apiCall('car_repair_management.api.vehicle.get_vehicles', { limit_page_length: 20 })

// List documents via frappe.client.get_list
apiList<T>(doctype: string, options?: { fields, filters, order_by, limit_start, limit_page_length }): Promise<T[]>

// Count documents via frappe.client.get_count
apiGetCount(doctype: string, filters?: Record<string, unknown>): Promise<number>

// Create document via frappe.client.insert
apiCreate<T>(doctype: string, values: Record<string, unknown>): Promise<T>

// Update document via frappe.client.save
apiUpdate<T>(doctype: string, name: string, values: Record<string, unknown>): Promise<T>

// Search link field options via frappe.client.get_list
apiSearchLink(doctype: string, txt?: string, filters?, titleField?): Promise<{ value, label, description? }[]>
```

### Important Note on Permissions

`apiSearchLink` and `apiList` use `frappe.client.get_list` which respects Frappe User Permissions. If a user has company-scoped User Permissions, they may not see all records. For issue/work order creation forms, the app provides custom search APIs (`search_vehicles`, `search_link_options`) that use `ignore_permissions`.

## Component Conventions

### Styling

Use CSS custom properties for theming (dark/light mode compatible):

```vue
<div
  class="p-4 rounded-lg border"
  style="background: var(--bg-tertiary); color: var(--text-primary); border-color: var(--border-color);"
>
```

Key CSS variables:
- **Backgrounds**: `--bg-tertiary`, `--bg-elevated`
- **Text**: `--text-primary`, `--text-secondary`, `--text-muted`
- **Borders**: `--border-color`, `--border-subtle`
- **Accent**: `--accent`

### Icons

Always use Lucide Vue icons:

```vue
<script setup>
import { LucideSettings, LucideCar } from 'lucide-vue-next'
</script>
<template>
  <LucideSettings class="size-4" />
</template>
```

### Badge Variants

```vue
<Badge variant="success">Active</Badge>   <!-- green -->
<Badge variant="danger">Critical</Badge>  <!-- red -->
<Badge variant="warning">Pending</Badge>  <!-- yellow -->
<Badge variant="info">Scheduled</Badge>   <!-- blue -->
<Badge variant="primary">In Progress</Badge> <!-- purple -->
<Badge variant="default">Draft</Badge>    <!-- gray -->
```

### Card Component

```vue
<Card>Normal card with padding</Card>
<Card padding="none">Card for tables (no padding)</Card>
<Card hoverable>Clickable card with hover effect</Card>
```

## State Management

### Session Store (`stores/session.ts`)
- `isLoggedIn: boolean` — auth state
- `user: object` — current user info
- `login(email, password)` / `logout()`

### Theme Store (`stores/theme.ts`)
- `isDark: boolean` — dark/light mode
- `toggle()` — switch themes
- Persisted to `localStorage`

### Schema Store (`stores/schema.ts`)
- Caches DocType metadata for dynamic form rendering
- `getMeta(doctype)` — fetches and caches schema

## Internationalization

7 languages with keys organized by module:

```typescript
// locales/en.ts
export default {
  common: { save: 'Save', cancel: 'Cancel', vehicle: 'Vehicle', ... },
  dashboard: { title: 'Dashboard', ... },
  repair_orders: { title: 'Repair Orders', new_order: 'New Repair Order', ... },
  vehicles: { title: 'Vehicles', ... },
  issues: { title: 'Issues', create_issue: 'Create Issue', ... },
  inspections: { ... },
  ...
}
```

Usage in components:

```vue
<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>
<template>
  <h1>{{ $t('repair_orders.title') }}</h1>
</template>
```

## Page Patterns

### 1. List Page Pattern

```
┌─────────────────────────────────┐
│  KPI Cards (4 across)           │
├─────────────────────────────────┤
│  Filter Bar (search + dropdowns)│
├─────────────────────────────────┤
│  Table with sortable columns    │
│  - Clickable rows → detail      │
│  - Status badges                │
│  - Pagination controls          │
└─────────────────────────────────┘
```

### 2. Detail Page Pattern

```
┌─────────────────────────────────┐
│  ← Back | Title + Badges | Actions │
├─────────────────────────────────┤
│  Summary Card (grid of fields)  │
├─────────────────────────────────┤
│  Related Data Sections          │
│  (tables, cards, relationships) │
├─────────────────────────────────┤
│  Comment/Post Section           │
├─────────────────────────────────┤
│  Activity Timeline              │
└─────────────────────────────────┘
```

### 3. Form Page Pattern

```
┌─────────────────────────────────┐
│  ← Back | Title                 │
├─────────────────────────────────┤
│  Card with form fields          │
│  - Inputs, selects, textareas   │
│  - LinkField for DocType links  │
├─────────────────────────────────┤
│  Cancel | Save/Create Button    │
└─────────────────────────────────┘
```

### 4. Vehicle Detail (Tabbed)

```
┌─────────────────────────────────┐
│  Header + Status + Actions      │
├─────────────────────────────────┤
│  Custodian + Drivers Card       │
├─────────────────────────────────┤
│  Tab Bar: Specs | Service | WOs │
│  | Inspections | Issues | ...   │
├─────────────────────────────────┤
│  Active Tab Content             │
└─────────────────────────────────┘
```

10 tabs: Specs, Service History, Work Orders, Inspection History, Issues, Financials, Fuel Quota, Service Reminders, Sensor Data, Attachments.

## Build & Development

```bash
# Development (hot reload on port 8080)
cd apps/car_repair_management/frontend
yarn dev
# Access: http://site:8080/workshop

# Production build
yarn build
# Output: car_repair_management/public/frontend/
# Access: http://site/workshop

# After Python changes (gunicorn with --preload):
pkill -9 -f "gunicorn.*frappe"
# Wait for supervisor to restart (~10-15 seconds)
```
