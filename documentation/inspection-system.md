# Inspection System

## Overview

The inspection system provides structured vehicle inspection workflows with form templates, scheduling, failure tracking, and integration with Repair Order handover checklists.

## Components

### Vehicle Inspection
The main inspection record capturing results for a specific vehicle.

**Key Fields**:
- `vehicle` — The vehicle inspected
- `inspection_type` — Scheduled or Ad-Hoc
- `inspection_date` — When performed
- `inspector` — Employee who conducted it
- `form_template` — Inspection Form Template used
- `result` — Pass / Fail
- `score` — Numeric score (0-100)
- `failures_count` — Number of failed items
- `follow_up_required` — Whether follow-up needed
- `follow_up_due_date` — Deadline for follow-up
- `linked_work_order` — Associated Repair Order (for handover inspections)
- `handover_checklist_item` — Specific checklist item (for handover inspections)

### Inspection Form Template
Reusable forms defining what to check during an inspection. Contains child items (Inspection Form Item) with item name, type, requirements, and default values.

### Inspection Schedule
Recurring inspection schedules specifying vehicle, frequency, next due date, and form template.

### Inspection Item Failure
Individual failure records linked to inspections. Tracks severity, notes, and recommended follow-up actions.

## Inspection Workflow

### Scheduled Inspections
1. **Create Schedule**: Define vehicle, frequency, form template
2. **Due Date Tracking**: System tracks next due date
3. **Perform Inspection**: Inspector creates Vehicle Inspection from schedule
4. **Record Results**: Pass/fail with score, capture failures
5. **Follow-Up**: Flag items needing follow-up with due dates

### Ad-Hoc Inspections
Created on-demand, often linked to repair orders or specific events.

### Handover Inspections
Created from Repair Order handover checklists:
1. RO has `handover_checklist` items
2. `create_handover_inspection()` creates a Vehicle Inspection linked to a specific checklist item
3. `get_handover_checklist_status()` aggregates pass/fail across all items
4. All items must pass before vehicle is "Ready for Handover"

## KPIs and Analytics

The inspection history API provides KPIs:
- **Total inspections** in filter range
- **Pass rate** / **Fail rate**
- **Average score**
- **Overdue follow-ups** — inspections with follow_up_required where due date has passed

## Frontend Pages

| Route | Component | Description |
|---|---|---|
| `/inspections` | InspectionHistory.vue | All inspections with KPIs and filters |
| `/inspections/:id` | InspectionDetail.vue | Single inspection detail |
| `/inspections/schedules` | Schedules.vue | Schedule management |
| `/inspections/schedules/:id` | ScheduleDetail.vue | Schedule detail |
| `/inspections/forms` | Forms.vue | Form template library |
| `/inspections/forms/:id` | FormDetail.vue | Form template detail |
| `/inspections/item-failures` | ItemFailure.vue | Failure tracking list |
| `/inspections/item-failures/:id` | ItemFailureDetail.vue | Failure detail |

The Vehicle Detail page also includes an **Inspection History Tab** showing all inspections for that specific vehicle.

## Filters

The inspection history supports extensive filtering:
- Date range
- Vehicle(s)
- Inspector
- Inspection type (Scheduled/Ad-Hoc)
- Result (Pass/Fail)
- Form template
- Has failures (boolean)
- Search text
