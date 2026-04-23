# Architecture Overview

## High-Level Architecture

Car Repair Management follows the standard Frappe app pattern with an additional Vue 3 SPA frontend:

```
┌─────────────────────────────────────────────────────────────┐
│                      Nginx (Reverse Proxy)                  │
├─────────────┬──────────────────────┬────────────────────────┤
│  /workshop  │     /api/method/*    │    /app/* (Desk)       │
│  Vue 3 SPA  │   Frappe API Layer   │   Frappe Desk UI      │
│  (Static)   │   (Gunicorn + WSGI)  │   (Server-rendered)   │
├─────────────┴──────────────────────┴────────────────────────┤
│                   Frappe Framework                          │
│         ┌─────────────────────────────────────┐             │
│         │   car_repair_management (App)       │             │
│         │   ├── 28 Custom DocTypes            │             │
│         │   ├── 22 API Modules                │             │
│         │   ├── Doc Event Hooks               │             │
│         │   └── Scheduler Tasks               │             │
│         └─────────────────────────────────────┘             │
├─────────────────────────────────────────────────────────────┤
│  MariaDB  │  Redis Cache  │  Redis Queue  │  Socket.IO     │
└───────────┴───────────────┴───────────────┴─────────────────┘
```

- **Backend**: Frappe app at `apps/car_repair_management/`
- **Frontend**: Vue 3 SPA at `apps/car_repair_management/frontend/`, built output served from `car_repair_management/public/frontend/`
- **Website Route**: `/workshop/<path>` mapped via `website_route_rules` in `hooks.py`
- **API Access**: All frontend calls go through `/api/method/car_repair_management.api.*`

## Directory Structure

```
apps/car_repair_management/
├── car_repair_management/              # Python package
│   ├── api/                            # Whitelisted API modules (22 files)
│   │   ├── activity.py                 # Activity timeline for any doctype
│   │   ├── aging_analysis.py           # Vehicle fleet aging analysis
│   │   ├── customer.py                 # Customer CRUD + KPIs
│   │   ├── employee.py                 # Employee detail + vehicle/RO assignments
│   │   ├── expense.py                  # Vehicle expense CRUD + KPIs
│   │   ├── expense_history.py          # Expense history analysis
│   │   ├── fuel.py                     # Fuel quota management + refueling records
│   │   ├── inspection.py              # Inspection history, schedules, forms, failures
│   │   ├── invoice.py                  # Combined sales + purchase invoice views
│   │   ├── issue.py                    # Issues, faults, recalls + workflow engine
│   │   ├── meter_history.py            # Odometer/meter reading tracking
│   │   ├── notification.py             # Notification preferences
│   │   ├── parts.py                    # Parts/inventory management + stock levels
│   │   ├── replacement_analysis.py     # Vehicle replacement scoring algorithm
│   │   ├── reports.py                  # 30+ standard reports execution engine
│   │   ├── settings.py                 # 14 settings categories configuration
│   │   ├── setup.py                    # Schema setup helpers
│   │   ├── setup_fuel_fields.py        # Fuel custom field creation
│   │   ├── setup_issue_fields.py       # Issue custom field creation
│   │   ├── vehicle.py                  # Vehicle dashboard + CRUD (1400+ lines)
│   │   ├── vehicle_assignments.py      # Driver/custodian assignment management
│   │   └── __init__.py
│   ├── car_repair_management/          # Module directory
│   │   ├── doctype/                    # 28 custom DocTypes
│   │   │   ├── repair_order/           # Core: Repair Order + controller
│   │   │   ├── repair_operation_line/  # Child: operation lines
│   │   │   ├── repair_parts_plan/      # Child: parts plan
│   │   │   ├── repair_checklist_response/ # Child: checklist responses
│   │   │   ├── customer_update/        # Child: customer communications
│   │   │   ├── vehicle_driver/         # Child: driver assignments
│   │   │   ├── vehicle_expense/        # Vehicle expenses
│   │   │   ├── vehicle_fuel_quota/     # Monthly fuel quotas
│   │   │   ├── vehicle_refueling_record/ # Refueling events
│   │   │   ├── vehicle_inspection/     # Inspection records
│   │   │   ├── vehicle_fault/          # Fault codes
│   │   │   ├── vehicle_recall/         # Manufacturer recalls
│   │   │   ├── inspection_form_template/ # Inspection form templates
│   │   │   ├── inspection_form_item/   # Inspection form items
│   │   │   ├── inspection_item_failure/ # Inspection failures
│   │   │   ├── inspection_schedule/    # Recurring schedules
│   │   │   ├── service_template/       # Service packages
│   │   │   ├── service_template_*/     # Service template children (3)
│   │   │   ├── handover_checklist_item/ # Checklist master data
│   │   │   ├── repair_checklist/       # Reusable checklists
│   │   │   ├── repair_checklist_item/  # Checklist items
│   │   │   ├── job_costing/            # Cost snapshots
│   │   │   ├── sla_template/           # SLA configurations
│   │   │   ├── fleet_replacement_settings/ # Replacement thresholds
│   │   │   ├── workshop_report_schedule/ # Scheduled reports
│   │   │   └── workshop_saved_report/  # Saved report configs
│   │   ├── report/                     # Script reports
│   │   ├── workspace/                  # Workshop workspace
│   │   └── dashboard_chart/            # Dashboard charts
│   ├── overrides/
│   │   ├── vehicle.py                  # Vehicle validate + on_update hooks
│   │   └── vehicle_dashboard.py        # Vehicle dashboard links
│   ├── fixtures/                       # Exported fixture data
│   ├── hooks.py                        # App configuration (doc_events, scheduler, routes)
│   ├── install.py                      # Post-install setup (custom fields, workspace, demo data)
│   ├── tasks.py                        # Scheduler tasks (reports, job costing)
│   └── demo_data.py                    # Demo data seeding
├── frontend/
│   ├── src/
│   │   ├── api/                        # API client (frappeRequest wrapper)
│   │   ├── components/
│   │   │   ├── ui/                     # 12 reusable UI components
│   │   │   ├── common/                 # ActivityTimeline
│   │   │   └── layouts/                # AppLayout, Sidebar, Topbar, MobileSidebar
│   │   ├── pages/                      # 13 feature modules, 50+ page components
│   │   ├── stores/                     # Pinia stores (session, theme, schema)
│   │   ├── locales/                    # i18n translations (7 languages)
│   │   ├── types/                      # TypeScript type definitions
│   │   ├── router.ts                   # Vue Router with 50+ routes
│   │   ├── App.vue                     # Root component
│   │   └── main.ts                     # App bootstrap
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── pyproject.toml
└── README.md
```

## Backend Architecture

### hooks.py Configuration

**Document Events** — the backbone of the backend logic:

| DocType | Event | Handler | Purpose |
|---|---|---|---|
| Repair Order | validate | `repair_order.on_validate` | Order-for validation, parts mutual exclusion, SLA checks |
| Repair Order | before_save | `repair_order.before_save` | Auto entry_datetime, cost recomputation |
| Repair Order | on_submit | `repair_order.on_submit` | Set status→Scheduled, apply service template |
| Repair Order | after_save | `repair_order.after_save` | (reserved) |
| Repair Order | before_update_after_submit | `repair_order.before_update_after_submit` | Cost recompute, QC guards, close guards |
| Vehicle | validate | `overrides.vehicle.validate` | Single active driver enforcement |
| Vehicle | on_update | `overrides.vehicle.on_update` | Auto-create Asset, sync insurance, auto-create fuel quota |
| Timesheet | on_submit/on_cancel | `repair_order.update_ro_from_timesheet` | Labor cost rollup |
| Purchase Invoice | on_submit/on_cancel | `repair_order.update_ro_from_purchase_invoice` | Parts cost rollup |
| Quotation | on_submit/on_cancel | `repair_order.update_ro_from_quotation` | Link tracking |
| Sales Order | on_submit/on_cancel | `repair_order.update_ro_from_sales_order` | Link tracking |
| Sales Invoice | on_submit/on_cancel | `repair_order.update_ro_from_sales_invoice` + `auto_status.update_ro_status_from_sales_invoice` | Revenue tracking + auto-status |
| Task | on_update | `auto_status.update_ro_status_from_task` | Auto-advance RO status |

**Scheduler Events**:
- **Hourly**: `tasks.execute_scheduled_reports` — runs due Workshop Report Schedules
- **Daily**: `tasks.update_job_costing_snapshots` — refreshes Job Costing for all ROs

**Website Route**: `/workshop/<path:app_path>` → serves the Vue SPA

### Doc Events Flow

```
Vehicle Save
  └→ validate: enforce single active driver
  └→ on_update:
       ├→ Auto-create ERPNext Asset (if acquisition data present)
       ├→ Sync insurance fields to linked Asset
       └→ Auto-create Vehicle Fuel Quota (if fuel_capacity > 0)

Repair Order Lifecycle
  └→ validate: order_for checks, parts validation, SLA check
  └→ before_save: auto entry_datetime, cost recompute
  └→ on_submit: status → Scheduled, apply Service Template
  └→ before_update_after_submit: cost recompute, QC guards, close guards

Cross-Document Hooks
  └→ Task on_update → auto-advance parent RO status
  └→ Sales Invoice on_submit → update RO revenue + auto-status
  └→ Timesheet on_submit → update RO labor cost
  └→ Purchase Invoice on_submit → update RO parts cost
```

## Frontend Architecture

| Aspect | Technology |
|---|---|
| Framework | Vue 3 Composition API + TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS + CSS Custom Properties |
| Routing | Vue Router (history mode, base: `/workshop`) |
| State | Pinia (session, theme, schema stores) |
| i18n | Vue I18n (7 languages) |
| Icons | Lucide Vue (exclusively) |
| HTTP | Custom `frappeRequest` wrapper with CSRF |

### Key Frontend Patterns

1. **API Layer**: All backend calls go through `apiCall()` which wraps `frappeRequest()` targeting `/api/method/*`
2. **Auth**: Session store checks login state; unauthenticated users redirect to `/login?redirect-to=/workshop`
3. **Theming**: Dark/light mode via CSS custom properties (`--bg-*`, `--text-*`, `--border-*`, `--accent`)
4. **Pages**: Each module follows List → Detail → Form pattern with KPI cards, filters, and paginated tables

## ERPNext Integration Points

| Integration | Mechanism | Purpose |
|---|---|---|
| **Asset Management** | Auto-create Asset on Vehicle save | Vehicle depreciation tracking |
| **Accounting** | Quotation → Sales Order → Sales Invoice | Revenue pipeline from ROs |
| **Stock** | Material Request, Stock Entry | Parts consumption for repairs |
| **HR** | Employee as driver/custodian/technician | Workforce management |
| **Projects** | Project + Task from RO submission | Work tracking, Gantt charts |
| **Timesheets** | Linked to RO for labor costing | Labor cost accumulation |
| **Purchase Invoice** | Linked to RO for parts costing | Parts cost accumulation |
