# Issues, Faults & Recalls

## Issues

Issues use Frappe's core **Issue** DocType with custom fields for vehicle-specific workflows.

### Custom Fields on Issue
- `custom_vehicle` — Link → Vehicle
- `custom_severity` — Low / Medium / High / Critical
- `custom_category` — Mechanical / Electrical / Body/Paint / Interior / Safety / Compliance / Other
- `custom_source` — Inspection / Driver Report / Mechanic / Customer / Sensor / Other
- `custom_assigned_to` — Assigned employee
- `custom_requested_by_employee` — Creator's Employee record
- `custom_workflow_state` — Draft / Pending Custodian Approval / Submitted / Rejected / Work Order Created
- `custom_linked_work_order` — Link → Repair Order
- `custom_linked_inspection` — Link → Vehicle Inspection
- `custom_linked_fault` — Link → Vehicle Fault
- `custom_rejected_by/on/reason` — Rejection details
- `custom_resolution_notes` — Resolution notes

### Issue Workflow

```
Driver creates issue
  └→ workflow_state = "Pending Custodian Approval"
       ├→ Custodian approves → "Submitted"
       │     └→ Create Work Order → "Work Order Created"
       │     └→ Close → Closed
       │     └→ Mark Duplicate → Closed
       └→ Custodian rejects → "Rejected"

Custodian/Admin creates issue
  └→ workflow_state = "Submitted"
       └→ (same actions as above)
```

### Creating Issues

The `create_issue` API determines the creator's role relative to the vehicle:
1. Looks up Employee via `user_id`
2. Checks if employee is custodian (`custom_custodian`) or active driver (`custom_drivers`)
3. Sets workflow accordingly

**No Employee required**: Users without an Employee record (e.g., administrators) can still create issues — they get role "other" and workflow "Submitted".

### Vehicle Search

The issue form uses a custom `search_vehicles` API instead of the standard LinkField because:
- Standard `frappe.client.get_list` respects User Permissions (company-scoped)
- The custom API uses `ignore_permissions` so users can report issues on any vehicle

### Converting to Work Order

The "Create Work Order" action opens a popup modal where the user selects:
1. **Order For**: Company or Customer (radio buttons)
2. **Company** or **Customer**: Searchable dropdown (using `search_link_options` API with `ignore_permissions`)

The API then creates a Repair Order with proper `order_for`, `customer`/`company`, and links it back to the issue.

### Available Actions

The `get_issue_detail` API computes `available_actions` based on workflow state:

| Workflow State | Available Actions |
|---|---|
| Pending Custodian Approval | approve, reject |
| Submitted | create_work_order, close, mark_duplicate |
| Work Order Created | open_draft_ro |
| Rejected | (none or resubmit) |

---

## Faults

Vehicle Faults track known fault codes and recurring problems.

### Key Features
- Fault code identification
- Severity classification
- Occurrence counting
- Occurrence history tracking
- Status management

### API
- `get_faults(vehicle, severity, status, search, ...)` — list with filters
- `get_fault_detail(name)` — detail with occurrence history
- `create_fault(vehicle, fault_code, title, ...)` — new fault
- `update_fault(name, ...)` — update existing

### Frontend Routes
- `/issues/faults` — Fault list
- `/issues/faults/:id` — Fault detail

---

## Recalls

Vehicle Recalls track manufacturer recall notices affecting one or more vehicles.

### Key Features
- Recall notice management
- Affected vehicles tracking
- Status tracking

### API
- `get_recalls(search, status, ...)` — list with filters
- `get_recall_detail(name)` — detail with affected vehicles and audit trail

### Frontend Routes
- `/issues/recalls` — Recall list
- `/issues/recalls/:id` — Recall detail
