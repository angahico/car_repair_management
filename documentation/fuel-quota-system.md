# Fuel Quota System

## Overview

The fuel quota system manages monthly fuel allowances per vehicle, tracks refueling events, and provides a two-tier approval workflow for over-quota consumption.

## Components

### 1. Vehicle Fuel Fields

Three custom fields on the Vehicle DocType control fuel quota behavior:

| Field | Type | Purpose |
|---|---|---|
| `custom_fuel_capacity_liters` | Float | Tank capacity in liters |
| `custom_km_per_liter` | Float | Fuel efficiency rating |
| `custom_monthly_fuel_quota` | Float | Manual monthly quota override |

### 2. Vehicle Fuel Quota (DocType)

Monthly quota records auto-created per vehicle.

- **Naming**: `FQ-{vehicle}-{YYYY-MM}` (e.g., `FQ-3-24345-2026-04`)
- **Auto-creation triggers**:
  - Vehicle saved with `custom_fuel_capacity_liters > 0` (via `on_update` hook)
  - `get_vehicle_quota_status()` API called (on-demand)

### 3. Vehicle Refueling Record (DocType)

Individual refueling events with approval workflow.

## Quota Calculation

Priority order:

```
1. custom_monthly_fuel_quota (if > 0)  →  User explicitly set a quota
2. custom_fuel_capacity_liters × 2      →  Default: 2 full tanks per month
3. 0                                     →  No fuel capacity configured
```

**Important**: The VehicleForm.vue sends `null` (not `0`) when the monthly fuel quota field is left blank, so the system correctly distinguishes "no override" from "override to zero".

## Auto-Creation Flow

```
Vehicle Save (on_update hook)
  └→ _ensure_fuel_quota(doc)
       ├─ Check: custom_fuel_capacity_liters > 0 ?
       ├─ Check: Quota for current month already exists?
       └─ Create Vehicle Fuel Quota record with calculated quota_liters
```

## Refueling Workflow

### Creating a Refueling Record

```python
create_refueling_record(vehicle, liters, refuel_date, odometer_reading, cost_per_liter, fuel_station, notes)
```

1. Gets/creates quota for the refueling month
2. Calculates `consumed_after = consumed_before + liters`
3. If `consumed_after > quota_liters`:
   - Sets `is_over_quota = 1`
   - Sets `over_quota_liters = consumed_after - quota_liters`
   - Sets `approval_status = "Pending Dept Head Approval"`
4. Otherwise: `approval_status = "Approved"`

### Approval Flow

```
                          ┌─────────────────┐
Within Quota ───────────→ │    Approved      │
                          └─────────────────┘

                          ┌─────────────────┐     ┌─────────────────────────┐
Over Quota ─────────────→ │ Pending Dept    │────→│ Approved                │
                          │ Head Approval   │     │ (if over_quota small)   │
                          └────────┬────────┘     └─────────────────────────┘
                                   │
                                   │ (if significant over_quota)
                                   ▼
                          ┌─────────────────────────┐     ┌──────────┐
                          │ Pending Depot Manager   │────→│ Approved │
                          │ Approval                │     └──────────┘
                          └─────────────────────────┘
                                   │
                                   ▼
                          ┌──────────┐
                          │ Rejected │
                          └──────────┘
```

**On Approval** (when `approval_status = "Approved"`):
- Quota record is updated: `consumed_liters += liters`, `remaining_liters` recalculated
- If `remaining_liters <= 0`, quota status set to "Exhausted"

### Manual Quota Adjustment

```python
update_fuel_quota(name, quota_liters=None, status=None)
```

Allows administrators to adjust monthly quota limits or change quota status.

## Frontend Pages

| Route | Component | Description |
|---|---|---|
| `/fuel` | FuelList.vue | Refueling records list with filters |
| `/fuel/new` | FuelForm.vue | Create new refueling record |
| `/fuel/:id` | FuelDetail.vue | Refueling detail with approval actions |
| `/fuel/quotas` | FuelQuotaList.vue | Monthly quota management |

The vehicle detail page also includes a **Fuel Quota Tab** showing the vehicle's quota history and refueling records.
