# Settings & Configuration

## Overview

The Settings module provides 14 configuration categories accessible from the frontend at `/workshop/settings`.

## Settings Categories

| ID | Title | Description |
|---|---|---|
| `organization` | Organization & Locations | Company profile, currency, fiscal year |
| `vehicles` | Vehicles Configuration | Vehicle types, service reminders, thresholds |
| `work_orders` | Work Orders & Workflow | Statuses, SLA targets, numbering rules |
| `inspections` | Inspections | Inspection types, schedules, form templates |
| `issues` | Issues & Faults | Severity scales, categories, fault codes |
| `expenses` | Expenses & Finance | Expense categories, receipt policies |
| `inventory` | Inventory | Warehouses, reorder defaults, stock policies |
| `customers` | Customers & CRM | Customer groups, territories, templates |
| `users` | Users, Roles & Permissions | Roles, permission sets, access control |
| `notifications` | Notifications | Channels, rules, recipient mapping |
| `integrations` | Integrations | Email, APIs, webhooks, external modules |
| `data_audit` | Data & Audit | Import tools, audit logs, activity history |
| `branding` | Branding & Documents | Logo, print formats, PDF and email templates |
| `maintenance` | System Maintenance | Scheduled jobs, cache, health checks |

## System Info

The settings home page displays:
- Frappe version
- ERPNext version
- Site name
- Active scheduled jobs count
- Email account integration status

## Scheduler Configuration

Two scheduled tasks are configured in `hooks.py`:

| Schedule | Task | Purpose |
|---|---|---|
| Hourly | `execute_scheduled_reports` | Run due Workshop Report Schedules |
| Daily | `update_job_costing_snapshots` | Refresh Job Costing records for all ROs |

## Installation Setup (install.py)

The `after_install` hook performs extensive setup:

### 1. Custom DocTypes Created
- Vehicle Location (GPS telemetry)
- Vehicle Fuel Level (fuel telemetry)
- Vehicle Sensor Data (generic sensors)

### 2. Custom Fields Added
On 10+ standard DocTypes (see [DocType Reference](doctypes.md#custom-fields-on-standard-doctypes)).

### 3. Master Data
- Asset Category: "Vehicles" (with accounting links)
- Item: "VEHICLE-ASSET" (fixed asset item for vehicle assets)

### 4. Workspace
- Workshop workspace with KPI cards, charts, and categorized shortcuts
- Kanban Board: "Repair Order by Status"

### 5. Demo Data
Sample vehicles, employees, customers, and repair orders for testing.

## Frontend Pages

| Route | Component |
|---|---|
| `/settings` | SettingsHome.vue — Grid of 14 category cards |
| `/settings/:category` | SettingsCategory.vue — Category-specific settings |
