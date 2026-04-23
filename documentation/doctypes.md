# DocType Reference

This document covers all 28+ custom DocTypes in the Car Repair Management app, plus custom fields added to standard ERPNext DocTypes.

---

## Core Repair DocTypes

### Repair Order

The central work order document for vehicle repair and maintenance.

| Property | Value |
|---|---|
| **Naming** | `RO-.YYYY.-.#####` (e.g., RO-2026-00001) |
| **Is Submittable** | Yes |
| **Module** | Car Repair Management |

**Key Fields**:

| Field | Type | Description |
|---|---|---|
| `vehicle` | Link → Vehicle | Vehicle being repaired |
| `order_for` | Select | "Customer" or "Company" |
| `customer` | Link → Customer | Required when order_for = Customer |
| `company` | Link → Company | Required when order_for = Company |
| `problem_summary` | Data | Brief problem description |
| `problem_details` | Text | Detailed problem description |
| `status` | Select | Draft / Scheduled / In Progress / Awaiting Parts / Ready for Handover / Delivered / Closed / On Hold / Cancelled |
| `priority` | Select | Low / Normal / High / Urgent |
| `intake_channel` | Data | How the order was received |
| `entry_datetime` | Datetime | When vehicle entered workshop |
| `expected_delivery_datetime` | Datetime | Expected completion |
| `sla_response_by` | Datetime | SLA response deadline |
| `sla_delivery_by` | Datetime | SLA delivery deadline |
| `service_template` | Link → Service Template | Pre-defined service package |
| `project` | Link → Project | Auto-created on submit |
| `sales_invoice` | Link → Sales Invoice | Linked invoice |
| `parts_cost` | Currency | Accumulated parts cost |
| `labor_cost` | Currency | Accumulated labor cost |
| `other_charges` | Currency | Additional charges |
| `total_job_cost` | Currency | Computed total |

**Child Tables**:
- `operations` → **Repair Operation Line** — Individual tasks/operations
- `parts_plan` → **Repair Parts Plan** — Required parts
- `handover_checklist` → **Repair Checklist Response** — Handover items
- `customer_updates` → **Customer Update** — Communication log

**Controller Hooks** (in `repair_order.py`):
- `on_validate`: Validates order_for requirements, parts mutual exclusion (can't be both billable and FoC), SLA date logic
- `before_save`: Auto-sets entry_datetime, recomputes cost aggregates
- `on_submit`: Sets status to "Scheduled", applies Service Template if specified
- `before_update_after_submit`: Recomputes costs, enforces QC completion for "Ready for Handover", enforces paid invoice for "Closed"

---

### Repair Operation Line (Child Table)

Individual operation within a Repair Order.

| Field | Type | Description |
|---|---|---|
| `task` | Link → Task | Auto-created on RO submit |
| `operation_name` | Link → Operation | Type of operation |
| `planned_minutes` | Int | Estimated duration |
| `assigned_to` | Link → User | Technician assigned |
| `workstation` | Link → Workstation | Workshop bay |
| `is_qc` | Check | Quality control operation |
| `status` | Select | Open / Working / Pending Review / Completed / Rejected / Cancelled |

### Repair Parts Plan (Child Table)

Parts required for a Repair Order.

| Field | Type | Description |
|---|---|---|
| `item_code` | Link → Item | Part item code |
| `item_name` | Data | Part name |
| `uom` | Link → UOM | Unit of measure |
| `qty_planned` | Float | Quantity needed |
| `is_billable` | Check | Charge to customer |
| `is_foc` | Check | Free of charge |
| `notes` | Small Text | Notes |

**Validation**: A part cannot be both `is_billable` and `is_foc`.

### Repair Checklist Response (Child Table)

Handover checklist entries linked to inspections.

| Field | Type | Description |
|---|---|---|
| `check_item` | Link → Handover Checklist Item | Checklist item reference |
| `type` | Data | Item type |
| `value` | Data | Recorded value |
| `notes` | Small Text | Notes |
| `passed` | Check | Pass/fail |

### Customer Update (Child Table)

Customer communication log within a Repair Order.

### Handover Checklist Item

Master data for checklist items used in vehicle handover processes.

### Service Template

Pre-defined service packages that auto-populate operations, parts, and checklist items when applied to a Repair Order.

**Child Tables**:
- `default_operations` → **Service Template Operation**
- `default_parts` → **Service Template Part**
- `default_checklist` → **Service Template Checklist Item**

### Repair Checklist

Reusable checklist templates with child items (**Repair Checklist Item**).

### Job Costing

Daily cost snapshots for Repair Orders, updated by the scheduler task.

| Field | Type | Description |
|---|---|---|
| `repair_order` | Link → Repair Order | Source RO |
| `project` | Link → Project | Linked project |
| `vehicle` | Link → Vehicle | Vehicle |
| `parts_cost` | Currency | Parts cost snapshot |
| `labor_cost` | Currency | Labor cost snapshot |
| `other_charges` | Currency | Other charges snapshot |
| `margin_snapshot` | Currency | Margin calculation |

### SLA Template

SLA configuration for response and delivery time targets.

---

## Vehicle & Fleet DocTypes

### Vehicle Driver (Child Table of Vehicle)

Tracks driver assignments with full lifecycle.

| Field | Type | Description |
|---|---|---|
| `employee` | Link → Employee | Driver |
| `employee_name` | Data | Auto-populated |
| `assigned_date` | Date | Assignment start |
| `assigned_by` | Link → Employee | Who assigned |
| `status` | Select | Active / Removal Requested / Removed |
| `ended_date` | Date | Assignment end |
| `ended_by` | Link → Employee | Who removed |
| `removal_reason` | Small Text | Reason for removal |

**Validation**: Only one driver can have status "Active" per vehicle.

### Vehicle Expense

Track vehicle-related expenses (fuel, maintenance, insurance, etc.).

| Field | Type | Description |
|---|---|---|
| `vehicle` | Link → Vehicle | Vehicle |
| `expense_date` | Date | Date of expense |
| `amount` | Currency | Expense amount |
| `category` | Select | Expense category |
| `vendor` | Data | Vendor/supplier |
| `title` | Data | Expense title |
| `notes` | Text | Details |
| `payment_status` | Select | Payment status |
| `receipt_attachment` | Attach | Receipt file |
| `work_order` | Link → Repair Order | Linked RO (optional) |

### Vehicle Fuel Quota

Monthly fuel allowance per vehicle with consumption tracking.

| Property | Value |
|---|---|
| **Naming** | `FQ-{vehicle}-{quota_month}` (e.g., FQ-3-24345-2026-04) |

| Field | Type | Description |
|---|---|---|
| `vehicle` | Link → Vehicle | Vehicle |
| `quota_month` | Data | Format YYYY-MM |
| `fuel_capacity_liters` | Float | Tank capacity (from vehicle) |
| `km_per_liter` | Float | Efficiency (from vehicle) |
| `quota_liters` | Float | Monthly allowance |
| `consumed_liters` | Float | Used so far |
| `remaining_liters` | Float | Remaining allowance |
| `status` | Select | Active / Exhausted / Closed |

**Auto-creation**: Created when a Vehicle is saved with `custom_fuel_capacity_liters > 0`, or on-demand when `get_vehicle_quota_status()` is called.

**Quota Calculation Priority**:
1. `custom_monthly_fuel_quota` (if > 0) — explicit override
2. `custom_fuel_capacity_liters × 2` — default formula
3. `0` — no capacity set

### Vehicle Refueling Record

Individual refueling events with two-tier over-quota approval.

| Field | Type | Description |
|---|---|---|
| `vehicle` | Link → Vehicle | Vehicle |
| `refuel_date` | Date | Date of refueling |
| `liters` | Float | Liters filled |
| `cost_per_liter` | Currency | Unit cost |
| `total_cost` | Currency | Total cost |
| `fuel_station` | Data | Station name |
| `odometer_reading` | Float | Odometer at refueling |
| `quota_link` | Link → Vehicle Fuel Quota | Linked quota |
| `consumed_before` | Float | Quota consumed before this fill |
| `consumed_after` | Float | Quota consumed after this fill |
| `is_over_quota` | Check | Exceeds quota |
| `over_quota_liters` | Float | Amount over quota |
| `approval_status` | Select | Approved / Pending Dept Head Approval / Pending Depot Manager Approval / Rejected |
| `dept_head_approved_by` | Link → Employee | First approver |
| `depot_manager_approved_by` | Link → Employee | Second approver |
| `rejection_reason` | Small Text | If rejected |

### Vehicle Fault

Known fault codes and recurring problems.

| Field | Type | Description |
|---|---|---|
| `vehicle` | Link → Vehicle | Affected vehicle |
| `fault_code` | Data | Fault identifier |
| `title` | Data | Fault name |
| `description` | Text | Details |
| `severity` | Select | Severity level |
| `status` | Select | Current status |
| `occurrence_count` | Int | Times occurred |

### Vehicle Recall

Manufacturer recall notices affecting one or more vehicles.

| Field | Type | Description |
|---|---|---|
| `title` | Data | Recall title |
| `description` | Text | Details |
| `affected_vehicles` | Table | Vehicles affected |
| `recall_date` | Date | Recall issue date |
| `status` | Select | Status |

---

## Inspection DocTypes

### Vehicle Inspection

Inspection record for a vehicle.

| Field | Type | Description |
|---|---|---|
| `title` | Data | Inspection title |
| `vehicle` | Link → Vehicle | Inspected vehicle |
| `inspection_date` | Datetime | When inspected |
| `inspection_type` | Select | Scheduled / Ad-Hoc |
| `status` | Select | Draft / Completed |
| `result` | Select | Pass / Fail |
| `score` | Float | Numeric score |
| `inspector` | Link → Employee | Inspector |
| `form_template` | Link → Inspection Form Template | Form used |
| `linked_work_order` | Link → Repair Order | Associated RO |
| `handover_checklist_item` | Data | Linked checklist item |
| `failures_count` | Int | Number of failures |
| `follow_up_required` | Check | Needs follow-up |
| `follow_up_due_date` | Date | Follow-up deadline |

### Inspection Form Template

Reusable inspection form definition with child items (**Inspection Form Item**).

### Inspection Form Item (Child)

Individual check items within an inspection form template.

### Inspection Item Failure

Specific failures recorded during inspections.

| Field | Type | Description |
|---|---|---|
| `inspection` | Link → Vehicle Inspection | Parent inspection |
| `vehicle` | Link → Vehicle | Vehicle |
| `item_name` | Data | Failed component |
| `severity` | Select | Failure severity |
| `notes` | Text | Details |
| `follow_up_action` | Text | Recommended action |

### Inspection Schedule

Recurring inspection schedule definitions.

| Field | Type | Description |
|---|---|---|
| `vehicle` | Link → Vehicle | Vehicle (or group) |
| `inspection_type` | Select | Type of inspection |
| `frequency` | Select | How often |
| `next_due_date` | Date | Next due date |
| `form_template` | Link → Inspection Form Template | Form to use |
| `status` | Select | Active / Paused |

---

## Report & Settings DocTypes

### Workshop Report Schedule

Scheduled report execution configuration, processed hourly by the scheduler.

| Field | Type | Description |
|---|---|---|
| `report_id` | Data | Standard report identifier |
| `frequency` | Select | How often to run |
| `recipients` | Text | Email recipients |
| `enabled` | Check | Active/inactive |
| `next_run` | Datetime | Next execution time |
| `last_status` | Data | Last run result |

### Workshop Saved Report

User-saved report configurations for quick access.

### Fleet Replacement Settings

Configuration for vehicle replacement scoring algorithm thresholds.

---

## Custom Fields on Standard DocTypes

### Vehicle (ERPNext core)

Extensive custom fields added:

| Field | Type | Purpose |
|---|---|---|
| `custom_status` | Select | Active / In Maintenance / Undergoing Tests / Delivered to Customer / Scrapped |
| `custom_vehicle_type` | Select | Car / SUV / Truck / Van / Motorcycle / Bus / Other |
| `custom_image` | Attach Image | Vehicle photo |
| `custom_custodian` | Link → Employee | Assigned custodian |
| `custom_custodian_name` | Data | Custodian name |
| `custom_drivers` | Table → Vehicle Driver | Driver assignment history |
| `custom_fuel_capacity_liters` | Float | Tank capacity |
| `custom_km_per_liter` | Float | Fuel efficiency |
| `custom_monthly_fuel_quota` | Float | Override for auto-calculated quota |
| `variant` | Data | Vehicle variant |
| `year` | Int | Model year |
| `transmission` | Select | Manual / Automatic / CVT |
| `acquisition_cost` | Currency | Purchase price |
| `engine_type/capacity/cylinders/drivetrain/number` | Various | Engine specifications |
| `ownership_type` | Data | Ownership classification |
| `registration_authority/expiry` | Data/Date | Registration info |
| `insurance_policy/expiry/insured_value/start_date/company` | Various | Insurance details |
| `odometer_at_last_service` | Int | Last service odometer |
| `last_service_date` | Date | Read-only, auto-updated |
| `next_service_due_date` | Date | Read-only, auto-updated |
| `jobs_count` | Int | Read-only, RO count |
| `repair_cost_to_date` | Currency | Read-only, total cost |
| `revenue_billed_to_date` | Currency | Read-only, total revenue |
| `erpnext_asset` | Link → Asset | Linked fixed asset |
| `depreciation_method` | Select | Straight Line / DDB / WDV |
| `depreciation_months` | Int | Useful life (default 60) |
| `custom_last_known_latitude/longitude` | Float | GPS tracking |
| `custom_last_location_update` | Datetime | Last GPS update |

### Other Standard DocTypes

| DocType | Custom Field | Type | Purpose |
|---|---|---|---|
| Asset | `vehicle` | Link → Vehicle | Reverse link from asset to vehicle |
| Quotation | `custom_repair_order` | Link → Repair Order | Link to source RO |
| Sales Order | `custom_repair_order` | Link → Repair Order | Link to source RO |
| Sales Invoice | `custom_repair_order` | Link → Repair Order | Link to source RO |
| Quotation Item | `repair_order`, `vehicle` | Link (hidden) | Item-level tracking |
| Sales Order Item | `repair_order`, `vehicle` | Link (hidden) | Item-level tracking |
| Sales Invoice Item | `repair_order`, `vehicle` | Link (hidden) | Item-level tracking |
| Project | `repair_order` | Link → Repair Order (hidden) | Project-RO link |
| Task | `repair_order` | Link → Repair Order (hidden) | Task-RO link |
| Timesheet | `repair_order` | Link → Repair Order (hidden) | Labor tracking |
| Stock Entry | `repair_order` | Link → Repair Order (hidden) | Parts consumption |
| Purchase Invoice | `repair_order` | Link → Repair Order (hidden) | Cost tracking |
| Repair Order | `entry_datetime`, `expected_delivery_datetime`, `entry_datetime_editable` | Datetime/Check | Timing fields |

---

## Runtime-Created DocTypes (via install.py)

These are created programmatically on install, not from JSON files:

### Vehicle Location
Telemetry data: vehicle, timestamp, latitude, longitude, direction (bearing), speed.

### Vehicle Fuel Level
Telemetry data: vehicle, timestamp, fuel_level (%), location (Link → Vehicle Location).

### Vehicle Sensor Data
Generic sensor telemetry: vehicle, timestamp, sensor_type, value, unit.
