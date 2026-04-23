# Repair Order Lifecycle

## Status Flow

```
Draft → Scheduled → In Progress → Awaiting Parts → In Progress → Ready for Handover → Delivered → Closed
                 ↘                                                                   ↗
                  → On Hold ────────────────────────────────────────────────────────→
                  → Cancelled
```

## Statuses

| Status | Description | Transitions To |
|---|---|---|
| **Draft** | Initial state, order being prepared | Scheduled (on submit) |
| **Scheduled** | Submitted, work planned | In Progress, On Hold, Cancelled |
| **In Progress** | Active repair work | Awaiting Parts, Ready for Handover, On Hold |
| **Awaiting Parts** | Blocked waiting for parts | In Progress (parts arrived) |
| **Ready for Handover** | Work complete, vehicle ready for pickup | Delivered |
| **Delivered** | Vehicle handed over to customer/company | Closed |
| **Closed** | Fully complete, invoiced and paid | (terminal) |
| **On Hold** | Temporarily paused | In Progress, Cancelled |
| **Cancelled** | Order cancelled | (terminal) |

## Detailed Lifecycle

### 1. Creation (Draft)

**Via Frontend**: Navigate to `/workshop/repair-orders/new`. Fill in:
- Vehicle (required)
- Order For: Company or Customer
- Customer or Company (depending on order_for)
- Problem summary and details
- Priority, intake channel
- Service Template (optional — auto-populates operations, parts, checklist)

**Via Issue Conversion**: From Issue Detail page → "Create Work Order" button opens a modal to select order_for and customer/company.

**Via Frappe Desk**: Standard form at `/app/repair-order/new`.

### 2. Submission (→ Scheduled)

On submit (`on_submit` hook):
1. Status automatically set to **Scheduled**
2. If a Service Template is specified:
   - Default operations copied to `operations` child table
   - Default parts copied to `parts_plan` child table
   - Default checklist items copied to `handover_checklist` child table
3. Project and Tasks can be created via the desk interface

### 3. Work Execution (In Progress)

Each operation in the `operations` child table progresses independently:

| Operation Status | Linked Task Status | Description |
|---|---|---|
| Open | Open | Not started |
| Working | Working | In progress |
| Pending Review | Pending Review | Awaiting QC review |
| Completed | Completed | Done |
| Rejected | Open | Failed review, needs redo |
| Cancelled | Cancelled | Skipped |

**Task auto-status**: When a linked Task's status changes (via `Task.on_update` hook), the RO status can auto-advance:
- All operations completed → RO can move to Ready for Handover
- Any operation started → RO moves to In Progress

### 4. Parts Management (Awaiting Parts)

When parts are needed:
1. Parts listed in `parts_plan` child table (billable or FoC)
2. **Material Request** created via `make_material_request_from_repair_order()`
3. RO status set to "Awaiting Parts"
4. When parts arrive and are issued, status returns to "In Progress"

### 5. Handover Process (Ready for Handover)

**Guards** (`before_update_after_submit`):
- All QC operations (`is_qc = 1`) must have their linked Tasks in Completed/Closed status
- If any QC task is incomplete, the status change is blocked with an error listing incomplete items

**Handover Checklist**:
1. Each checklist item can have a linked Vehicle Inspection
2. `get_handover_checklist_status()` returns pass/fail status of all items
3. `create_handover_inspection()` creates an inspection for a specific checklist item
4. All items must pass before vehicle is ready

### 6. Delivery & Closure

**Delivered**: Vehicle picked up. Commercial documents can be generated:
- `make_quotation_from_repair_order()` — creates Quotation with operations + billable parts
- Quotation → Sales Order → Sales Invoice pipeline

**Closed** (`before_update_after_submit` guard):
- Linked Sales Invoice must be in "Paid" or "Submitted" status
- If invoice is unpaid, close is blocked

## Cost Tracking

Costs are automatically accumulated via doc event hooks:

| Source | Hook | RO Field Updated |
|---|---|---|
| Purchase Invoices | `update_ro_from_purchase_invoice` | `parts_cost` |
| Timesheets | `update_ro_from_timesheet` | `labor_cost` |
| Manual entry | `other_charges` field | `other_charges` |
| **Total** | `before_save` recomputation | `total_job_cost = parts_cost + labor_cost + other_charges` |

The **Job Costing** DocType provides daily snapshots of all RO costs (updated by `tasks.update_job_costing_snapshots`).

## Commercial Flow

```
Repair Order
  └→ make_quotation_from_repair_order() → Quotation (operations + billable parts)
      └→ Sales Order
          └→ Sales Invoice
              └→ update_ro_from_sales_invoice() → links back to RO
              └→ auto_status.update_ro_status_from_sales_invoice() → auto-advance status
```

Custom fields `custom_repair_order` on Quotation, Sales Order, and Sales Invoice link them back to the source RO. Item-level fields `repair_order` and `vehicle` on line items enable detailed tracking.
