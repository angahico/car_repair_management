# User Manual

## Getting Started

### Accessing the Application

Navigate to `https://your-site.com/workshop` in your web browser. Log in with your credentials. You'll be directed to the **Dashboard**.

### Navigation

The left sidebar contains links to all modules:

| Section | Pages |
|---|---|
| **Main** | Dashboard |
| **Operations** | Repair Orders, Vehicles, Customers, Employees, Tasks |
| **Quality** | Inspections, Issues |
| **Finance** | Expenses, Fuel, Parts, Invoices |
| **Analytics** | Reports |
| **System** | Settings |

---

## Dashboard

The dashboard shows key metrics at a glance:
- **Total Repair Orders** — active order count
- **In Progress** — currently being worked on
- **Awaiting Parts** — blocked on parts
- **Ready for Handover** — completed, awaiting pickup
- **Status Breakdown** — visual chart of RO distribution
- **Recent Orders** — latest repair orders
- **Fleet Summary** — total vehicles and active count

---

## Repair Orders

### Viewing Repair Orders
Navigate to **Repair Orders** from the sidebar. The list shows:
- KPI cards at the top (total, in progress, etc.)
- Filters for status, date, vehicle, search
- Clickable rows to view details

### Creating a Repair Order
1. Click **New Repair Order**
2. Select **Order For**: Company or Customer
3. Select the **Company** or **Customer**
4. Select the **Vehicle** to repair
5. Enter **Problem Summary** and details
6. Set **Priority** (Low/Normal/High/Urgent)
7. Optionally select a **Service Template** to auto-populate operations and parts
8. Click **Save** to create as Draft
9. **Submit** the order to schedule work

### Managing Operations
Each RO contains operations (tasks). Click on an operation to:
- View operation details and linked task
- Change status (Open → Working → Completed)
- Assign a technician
- Add comments

### Generating Documents
From an RO detail page:
- **Create Quotation** — generates a customer quotation from operations + billable parts
- **Create Material Request** — generates a parts request for warehouse

---

## Vehicles

### Vehicle List
Browse all vehicles with filters for status, type, make, and fuel type. KPI cards show total fleet, active vehicles, and in-maintenance count.

### Vehicle Detail
Click a vehicle to see 10 tabs of information:

| Tab | What You'll See |
|---|---|
| **Specs** | Engine, transmission, capacity details |
| **Service History** | Past repairs and maintenance |
| **Work Orders** | Current and past repair orders |
| **Inspections** | Inspection history and results |
| **Issues** | Open and resolved issues |
| **Financials** | Cost of ownership, insurance, depreciation |
| **Fuel Quota** | Monthly fuel allowances and refueling records |
| **Service Reminders** | Upcoming maintenance due dates |
| **Sensor Data** | GPS and telemetry data |
| **Attachments** | Documents and files |

### Creating a Vehicle
1. Click **New Vehicle**
2. Enter license plate, make, model, year
3. Set vehicle type and status
4. Add engine specifications
5. Set acquisition cost and date (auto-creates ERPNext Asset)
6. Configure fuel capacity for fuel quota tracking
7. Save

### Driver Management
On the Vehicle Detail page, the drivers section shows:
- **Current drivers** with "Active" status
- **Past drivers** with removal dates
- **Custodian** — the responsible employee

---

## Employees

### Employee List
View all employees with department, designation, and assigned work order counts.

### Employee Detail
Shows:
- **Profile** — name, department, designation, contact info
- **Performance** — completed WOs, active WOs, average completion time
- **Current Vehicle Assignments** — vehicles where employee is active driver or custodian (table view with role badges)
- **Past Vehicle Assignments** — removed assignments with dates
- **Current Repair Orders** — active ROs assigned to the employee
- **Past Repair Orders** — completed/closed ROs
- **Audit Trail** — recent changes

---

## Issues

### Viewing Issues
Navigate to **Issues** to see all reported problems. Filter by vehicle, severity, category, source, and status.

### Creating an Issue
1. Click **New Issue**
2. Enter a **Subject** describing the problem
3. Select the **Vehicle** (searchable dropdown shows all vehicles)
4. Set **Severity** (Low/Medium/High/Critical)
5. Choose a **Category** (Mechanical, Electrical, etc.)
6. Select **Source** (Driver Report, Inspection, etc.)
7. Add **Description** with details
8. Click **Create**

**Workflow**: If you're a driver for the selected vehicle, the issue will require custodian approval before a work order can be created.

### Issue Actions
From the Issue Detail page:
- **Approve** (custodian only) — approves a driver-reported issue
- **Reject** — rejects with reason
- **Create Work Order** — converts issue to a Repair Order (opens a popup to select Company/Customer)
- **Close** — closes the issue with a reason
- **Mark Duplicate** — marks as duplicate of another issue

### Faults & Recalls
- **Faults** (`/issues/faults`) — known recurring problems with fault codes
- **Recalls** (`/issues/recalls`) — manufacturer recall notices

---

## Fuel Management

### Refueling Records
Navigate to **Fuel** to see all refueling events. Filter by vehicle, month, and approval status.

### Creating a Refueling Record
1. Click **New Refueling**
2. Select the **Vehicle**
3. Enter **Liters** filled
4. Set **Date** and **Odometer Reading**
5. Enter **Cost per Liter** and **Fuel Station**
6. Click **Create**

The system automatically checks the vehicle's monthly quota:
- **Within quota**: Approved immediately
- **Over quota**: Requires department head approval, then possibly depot manager approval

### Fuel Quotas
Navigate to **Fuel → Quotas** to view monthly allowances per vehicle. Quotas are auto-created when vehicles have fuel capacity configured.

---

## Inspections

### Inspection History
View all inspections with filters for date, vehicle, inspector, type, result, and failures.

### Inspection Schedules
Manage recurring inspection schedules at `/inspections/schedules`.

### Form Templates
Browse and manage inspection form templates at `/inspections/forms`.

### Item Failures
Track inspection failures at `/inspections/item-failures` with severity and follow-up tracking.

---

## Expenses

### Recording Expenses
1. Navigate to **Expenses** → **New Expense**
2. Select vehicle, date, amount, category
3. Add vendor and notes
4. Optionally attach a receipt
5. Save

### Viewing Expense History
The expense list provides KPIs: total amount, count, average, and category breakdown. Filter by date range, vehicle, category, vendor, and payment status.

---

## Parts & Inventory

Browse workshop parts at `/workshop/parts`. View stock levels, reorder status, and valuation. Create or edit parts/items as needed.

---

## Invoices

View combined Sales and Purchase Invoices at `/workshop/invoices`. Filter by type, date range, status, customer/supplier, and amount range.

---

## Reports

### Report Dashboard
Navigate to **Reports** for overview KPIs and quick access to key metrics.

### Report Library
Browse 30+ standard reports organized by category:
- Fleet Overview, Utilization, Work Orders, Parts, Inspections, Issues, Financials, Customers, Employees

Click any report to run it with customizable filters.

### Saved Reports
Save frequently used report configurations for quick access.

### Scheduled Reports
Set up automatic report execution with email delivery.

---

## Settings

Configure the application at `/workshop/settings`. 14 categories cover organization, vehicles, work orders, inspections, issues, expenses, inventory, customers, users, notifications, integrations, data, branding, and system maintenance.

---

## Tips

1. **Use the search bar** in list pages to quickly find records
2. **Click any row** in a table to view details
3. **Status badges** are color-coded for quick identification
4. **"Open in Desk"** button on detail pages takes you to the full Frappe form for advanced editing
5. The app supports **7 languages** — check settings for language preferences
6. **Dark mode** is available via the theme toggle in the top bar
