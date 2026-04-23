# Expenses & Invoicing

## Vehicle Expenses

### Overview
The Vehicle Expense DocType tracks all vehicle-related costs outside of repair orders, such as fuel purchases, insurance premiums, registration fees, and miscellaneous costs.

### Key Fields
- `vehicle` — Vehicle the expense is for
- `expense_date` — Date of expense
- `amount` — Expense amount (Currency)
- `category` — Expense category
- `vendor` — Vendor/supplier name
- `title` — Brief description
- `notes` — Detailed notes
- `payment_status` — Payment status tracking
- `receipt_attachment` — Uploaded receipt file
- `work_order` — Optional link to Repair Order

### KPIs
The expense list API provides aggregated KPIs:
- Total expense amount
- Total expense count
- Average per expense
- Category breakdown

### Filtering
- Date range
- Vehicle
- Category
- Vendor (text search)
- Work order linkage (linked/unlinked)
- Payment status
- Has receipt (boolean)

### Frontend Pages
| Route | Component | Description |
|---|---|---|
| `/expenses` | ExpenseList.vue | Paginated expense list with KPIs |
| `/expenses/new` | ExpenseForm.vue | Create new expense |
| `/expenses/:id` | ExpenseDetail.vue | Expense detail |
| `/expenses/:id/edit` | ExpenseForm.vue | Edit expense |

### Fleet Analysis
- `/vehicles/expense-history` — Fleet-wide expense analysis
- Vehicle Detail → Financials Tab — Per-vehicle cost of ownership

---

## Invoicing

### Overview
The invoice module provides a unified view of both Sales Invoices (customer billing) and Purchase Invoices (vendor costs), with integration to Repair Orders.

### Sales Invoice Flow (from Repair Order)

```
Repair Order
  └→ make_quotation_from_repair_order()
       └→ Quotation (with custom_repair_order link)
            └→ Sales Order (with custom_repair_order link)
                 └→ Sales Invoice (with custom_repair_order link)
                      └→ update_ro_from_sales_invoice() — links back to RO
                      └→ auto_status — can auto-advance RO status
```

### Custom Fields for Tracking

All commercial documents carry links back to the Repair Order:
- Quotation, Sales Order, Sales Invoice: `custom_repair_order` field
- Line items: `repair_order` and `vehicle` fields (hidden)

### Combined Invoice View

The `get_invoices` API combines Sales and Purchase Invoices into a single paginated view:

| Filter | Description |
|---|---|
| `invoice_type` | Sales / Purchase / All |
| `date_from/to` | Date range |
| `status` | Invoice status |
| `customer` | Customer filter (sales only) |
| `supplier` | Supplier filter (purchase only) |
| `work_order_linked` | Has linked Repair Order |
| `amount_min/max` | Amount range |
| `search` | Text search |

### KPIs
- Total sales invoiced
- Total purchases
- Outstanding amount
- Count of invoices

### Frontend Pages
| Route | Component | Description |
|---|---|---|
| `/invoices` | InvoiceList.vue | Combined invoice list |
| `/invoices/:id` | InvoiceDetail.vue | Invoice detail |

---

## Parts & Inventory

### Overview
The parts module manages workshop inventory using ERPNext's Item DocType with stock tracking.

### Key Features
- Item CRUD with stock_uom and valuation
- Real-time stock levels per warehouse
- Reorder level monitoring
- Consumption tracking via Repair Order parts plans

### KPIs
- Total items
- Stock items count
- Low stock items (below reorder level)
- Out of stock items

### Frontend Pages
| Route | Component | Description |
|---|---|---|
| `/parts` | PartList.vue | Parts list with stock status |
| `/parts/new` | PartForm.vue | Create new part |
| `/parts/:id` | PartDetail.vue | Part detail with stock info |
| `/parts/:id/edit` | PartForm.vue | Edit part |
