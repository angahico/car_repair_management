# Reports & Analytics

## Overview

The reporting system provides 30+ standard reports across 9 categories, plus saved report configurations and scheduled report execution.

## Standard Reports

### Fleet Overview
| Report | Type | Description |
|---|---|---|
| Fleet Health Score | KPI | Composite fleet health score |
| Age Distribution | Chart | Vehicle fleet age distribution |
| Utilization Overview | Chart | Fleet utilization rates |
| Downtime Summary | Table | Vehicle downtime analysis |

### Utilization & Meter
| Report | Type | Description |
|---|---|---|
| Mileage by Vehicle | Table | Mileage readings per vehicle |
| Low-Use Vehicles | Table | Vehicles with minimal activity |
| Fuel vs Mileage Efficiency | Chart | Fuel consumption vs distance |

### Work Orders & Repairs
| Report | Type | Description |
|---|---|---|
| Work Order Volume Trend | Chart | WO creation trends over time |
| Average Resolution Time | KPI | Average time to complete WOs |
| Backlog by Status | Chart | Current WO backlog breakdown |
| Cost vs Estimate Variance | Table | Actual vs estimated costs |
| Repeat Repairs / Rework | KPI | Rate of repeat repairs |

### Parts & Inventory
| Report | Type | Description |
|---|---|---|
| Low Stock / Out of Stock | Table | Items below reorder level |
| Fast-Moving Items | Table | Most consumed parts |
| Work Order Consumption | Table | Parts consumed by WOs |

### Inspections
| Report | Type | Description |
|---|---|---|
| Pass/Fail Trends | Chart | Inspection pass/fail rates over time |
| Overdue Schedules | Table | Overdue inspection schedules |
| Failure Hotspots | Chart | Top failed inspection components |
| Inspector Productivity | Table | Inspections per inspector |

### Issues & Faults
| Report | Type | Description |
|---|---|---|
| New vs Resolved Trend | Chart | Issue creation vs resolution |
| Mean Time to Resolve | KPI | Average issue resolution time |
| Top Fault Codes | Table | Most common fault codes |
| High Severity Open Issues | Table | Open critical/high issues |

### Financials
| Report | Type | Description |
|---|---|---|
| Expenses by Category | Chart | Expense breakdown by category |
| Cost per Vehicle | Table | Total costs per vehicle |
| Cost per KM | Table | Operating cost per kilometer |
| Invoice Aging | Table | Outstanding invoice aging |

### Customers
| Report | Type | Description |
|---|---|---|
| Top Customers by Revenue | Table | Highest revenue customers |
| Outstanding Balance | Table | Customer outstanding balances |

### Employees
| Report | Type | Description |
|---|---|---|
| Work Orders Completed | Table | WOs completed per employee |
| Avg Completion Time | KPI | Average WO completion time |
| Workload Distribution | Chart | Current workload spread |

## Report Types

- **KPI**: Single metric value with trend indicator
- **Chart**: Visual chart (bar, line, pie, etc.)
- **Table**: Tabular data with sortable columns

## Saved Reports

Users can save report configurations (filters, parameters) for quick access:

```python
save_report(report_id, title, filters)    # Save configuration
get_saved_reports()                        # List user's saved reports
delete_saved_report(name)                  # Remove saved report
```

## Scheduled Reports

Reports can be scheduled for automatic execution and email delivery:

### Configuration
- **Report ID**: Which standard report to run
- **Frequency**: How often (daily, weekly, monthly)
- **Recipients**: Email addresses for delivery
- **Enabled**: Active/inactive toggle

### Execution
- Scheduler runs hourly via `tasks.execute_scheduled_reports`
- Checks `Workshop Report Schedule` records where `enabled = 1` and `next_run <= now`
- Executes report and updates `last_status` and `next_run`

## Frontend Pages

| Route | Component | Description |
|---|---|---|
| `/reports` | Overview.vue | Report dashboard with KPIs |
| `/reports/library` | Library.vue | Browse 30+ standard reports by category |
| `/reports/view/:id` | ReportView.vue | Execute and view a report |
| `/reports/saved` | SavedReports.vue | Manage saved report configs |
| `/reports/scheduled` | ScheduledReports.vue | Manage scheduled reports |

## Desk Integration

The Workshop workspace in Frappe Desk includes:
- **Dashboard Charts**: ROs by Status (30d), Billable vs FoC Parts (30d), Most Repaired Vehicles
- **Number Cards**: ROs Today, In Progress, Awaiting Parts, Ready for Handover, Due Today, Overdue
- **Report Shortcuts**: Job Profitability, Parts Consumption, Technician Utilization, WIP Aging, Repeat Repairs
