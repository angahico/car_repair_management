# Assumptions — Inspections, Issues & Core Operations Modules

## Data Model Assumptions

### Vehicle Inspection
- Links to `Vehicle` (core Frappe DocType from Setup module) via `vehicle` field
- Links to `Employee` (core ERPNext DocType) for `inspector`
- Links to `Repair Order` (custom DocType) for `linked_work_order`
- Links to `Inspection Form Template` (new DocType) for `form_template`
- `score` is a Percent (0-100) field, manually set or calculated from checklist
- `failures_count` is a read-only Int updated when `Inspection Item Failure` records are created
- `result` is manually set (Pass/Conditional/Fail) — not auto-computed from score thresholds

### Inspection Item Failure
- Each failure is a standalone record linked to a `Vehicle Inspection` and `Vehicle`
- `is_recurring` flag is manually set — no auto-detection of recurring failures
- `resolution_type` tracks how the failure was handled (Work Order, Quick Fix, Deferred, N/A)

### Inspection Schedule
- `frequency` determines recurrence but auto-generation of inspections is not yet implemented
- `next_due` must be manually updated or handled by a future scheduled task
- `auto_create_inspection` flag exists but the automation is not yet wired

### Inspection Form Template
- Items are stored as a child table (`Inspection Form Item`)
- `usage_count` must be manually incremented when a template is used in an inspection
- Versioning is tracked via the `version` Int field (incremented manually on edit)
- The builder UI is not implemented — editing is done via Frappe Desk form

### Issues (Frappe core Issue DocType)
- Uses Frappe's built-in `Issue` DocType from the Support module
- Extended with custom fields: `custom_vehicle`, `custom_category`, `custom_severity`, `custom_source`, `custom_assigned_to`, `custom_linked_work_order`, `custom_linked_inspection`, `custom_linked_fault`, `custom_resolution_notes`
- `raised_by` (email field from Issue) is used as "Reported By"
- Triage time is approximated from `first_responded_on` field
- Resolution time uses `resolution_date` field

### Vehicle Fault
- Standalone DocType for technical defects
- `fault_code` supports free-text OBD/manufacturer codes (no code validation)
- `confirmed` status (Unconfirmed/Confirmed/False Positive) is a manual assessment
- Occurrence history matches by same vehicle + component_system

### Vehicle Recall
- `affected_models` is a comma-separated text field of model names
- `affected_years` is a free-text field (e.g., "2018-2022")
- `vehicles_affected`, `vehicles_completed`, and `compliance_pct` are manually maintained
- Affected vehicles lookup in the detail page matches by `make` (=manufacturer) and `model` (in affected_models)
- Bulk actions (schedule inspections, create WOs, mark addressed) are planned but not implemented

## Backend Assumptions
- All new DocTypes use `naming_series` for auto-naming
- `track_changes: 1` is enabled on all new DocTypes for audit trail
- The `Version` DocType (core Frappe) is used for audit trail display
- `or_filters` in API endpoints support multi-field search (name, vehicle, title, etc.)

## Frontend Assumptions
- Calendar, Kanban, and Gantt views for Schedules show "Coming soon" placeholder — Table is default
- Form Template builder/editor is not implemented — uses "Edit in Desk" link to Frappe form
- Bulk resolution actions on recalls are disabled with "Coming soon" labels
- Detail pages use `apiCall` to whitelisted methods, not direct resource API
- No data validation is done on the frontend beyond what Frappe enforces

## Core Operations Module Assumptions

### Vehicle Expense (New DocType — VE-)
- Standalone DocType for tracking vehicle and repair-related expenses
- Links to `Vehicle` (required) and `Repair Order` (optional)
- Categories: Fuel, Parts, Labor, External Service, Insurance, Taxes, Other
- `vendor` is free-text Data field (not linked to Supplier DocType)
- `payment_status` tracks Unpaid/Paid/Partially Paid — no workflow integration
- `receipt_attachment` is Attach Image field for receipt photos/PDFs
- `receipt_required` is a toggle but does not enforce validation (advisory only)
- `odometer_reading` is optional, shown only for Fuel category
- This is separate from the existing `expense_history.py` API which aggregates data from Vehicle Log + Repair Order

### Parts / Inventory
- Uses ERPNext's `Item` DocType directly — no new DocType created
- Stock levels aggregated from `Bin` DocType (sum across all warehouses)
- Stock status computed in Python: "In Stock" / "Low" (qty ≤ reorder_level) / "Out of Stock" (qty ≤ 0)
- `reorder_level` used from Item's field (may be 0 if not set)
- Item creation through the SPA creates items via frappe API — no custom DocType
- Usage history queries `Repair Parts Plan` child table of Repair Order

### Customers
- Uses ERPNext's `Customer` DocType directly
- Outstanding balance computed by querying `Sales Invoice` (docstatus=1, outstanding_amount > 0)
- Addresses fetched via `Dynamic Link` pattern (Address → Customer)
- "New customers (30 days)" KPI counts by creation date
- Customer creation redirects to Frappe Desk form (/app/customer/new)

### Employees
- Uses ERPNext's `Employee` DocType directly
- Work order assignment tracked via `assigned_to` field on Repair Order (if it exists)
- Performance metrics (completed WOs, avg completion days) computed from Repair Order status transitions
- Employee creation redirects to Frappe Desk form (/app/employee/new)

### Invoices
- Combines Sales Invoice and Purchase Invoice into a unified view
- Both DocTypes queried separately and merged/sorted in Python
- KPIs: total_invoiced, total_paid, outstanding, overdue_count
- Overdue detection: outstanding > 0 AND due_date < today
- Invoice creation redirects to Frappe Desk form
- Detail page uses `?type=Sales|Purchase` query param to determine DocType
- Payment info fetched via `Payment Entry Reference` child table

## Backend API Additions (Core Operations)
- `api/expense.py`: get_expenses, get_expense_detail, create_expense, update_expense
- `api/parts.py`: get_parts, get_part_detail, create_part
- `api/customer.py`: get_customers, get_customer_detail
- `api/employee.py`: get_employees, get_employee_detail
- `api/invoice.py`: get_invoices, get_invoice_detail

## Frontend Route Additions
- `/expenses` → ExpenseList, `/expenses/new` → ExpenseForm, `/expenses/:id` → ExpenseDetail, `/expenses/:id/edit` → ExpenseForm
- `/parts` → PartList, `/parts/new` → PartForm, `/parts/:id` → PartDetail, `/parts/:id/edit` → PartForm
- `/invoices` → InvoiceList, `/invoices/:id` → InvoiceDetail
- Customers and Employees routes unchanged (list + detail already existed)

## What Was NOT Changed
- No existing DocTypes were modified (all changes are additive)
- No existing fields were renamed or removed
- No existing API endpoints were modified
- No existing routes or sidebar items were removed
- Vehicle Details page and all 10 tabs remain untouched
- Repair Order creation/listing/detail remains untouched
- Fleet Intelligence pages (Meter History, Expense History, Replacement Analysis, Aging Analysis) remain untouched
- Inspection and Issues modules remain untouched
- Old stub pages (Expenses.vue, Parts.vue, Invoices.vue) still exist but are no longer routed to
