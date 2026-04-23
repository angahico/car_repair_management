import frappe
from frappe.utils import getdate, nowdate, flt


@frappe.whitelist()
def get_invoices(date_from=None, date_to=None, invoice_type=None, status=None,
				 customer=None, supplier=None, work_order_linked=None,
				 amount_min=None, amount_max=None,
				 search=None, limit_start=0, limit_page_length=20):
	"""Get combined sales and purchase invoices with KPIs."""
	sales_records = []
	purchase_records = []
	si_total = 0
	pi_total = 0

	include_sales = invoice_type in (None, "", "Sales")
	include_purchase = invoice_type in (None, "", "Purchase")

	# Sales Invoices
	if include_sales:
		si_filters = {"docstatus": ["!=", 2]}
		if date_from and date_to:
			si_filters["posting_date"] = ["between", [getdate(date_from), getdate(date_to)]]
		elif date_from:
			si_filters["posting_date"] = [">=", getdate(date_from)]
		elif date_to:
			si_filters["posting_date"] = ["<=", getdate(date_to)]
		if status:
			si_filters["status"] = status
		if customer:
			si_filters["customer"] = customer

		si_or_filters = None
		if search:
			si_or_filters = [
				["name", "like", f"%{search}%"],
				["customer", "like", f"%{search}%"],
			]

		all_si = frappe.get_all(
			"Sales Invoice",
			filters=si_filters,
			or_filters=si_or_filters,
			fields=["name", "posting_date", "customer", "grand_total", "outstanding_amount",
					"status", "due_date", "owner", "creation", "modified"],
		)
		si_total = len(all_si)

		for inv in all_si:
			sales_records.append({
				"name": inv.name,
				"invoice_type": "Sales",
				"posting_date": str(inv.posting_date) if inv.posting_date else None,
				"party": inv.customer,
				"grand_total": flt(inv.grand_total),
				"outstanding_amount": flt(inv.outstanding_amount),
				"status": inv.status,
				"due_date": str(inv.due_date) if inv.due_date else None,
				"owner": inv.owner,
				"creation": str(inv.creation) if inv.creation else None,
				"modified": str(inv.modified) if inv.modified else None,
			})

	# Purchase Invoices
	if include_purchase:
		pi_filters = {"docstatus": ["!=", 2]}
		if date_from and date_to:
			pi_filters["posting_date"] = ["between", [getdate(date_from), getdate(date_to)]]
		elif date_from:
			pi_filters["posting_date"] = [">=", getdate(date_from)]
		elif date_to:
			pi_filters["posting_date"] = ["<=", getdate(date_to)]
		if status:
			pi_filters["status"] = status
		if supplier:
			pi_filters["supplier"] = supplier

		pi_or_filters = None
		if search:
			pi_or_filters = [
				["name", "like", f"%{search}%"],
				["supplier", "like", f"%{search}%"],
			]

		all_pi = frappe.get_all(
			"Purchase Invoice",
			filters=pi_filters,
			or_filters=pi_or_filters,
			fields=["name", "posting_date", "supplier", "grand_total", "outstanding_amount",
					"status", "due_date", "owner", "creation", "modified"],
		)
		pi_total = len(all_pi)

		for inv in all_pi:
			purchase_records.append({
				"name": inv.name,
				"invoice_type": "Purchase",
				"posting_date": str(inv.posting_date) if inv.posting_date else None,
				"party": inv.supplier,
				"grand_total": flt(inv.grand_total),
				"outstanding_amount": flt(inv.outstanding_amount),
				"status": inv.status,
				"due_date": str(inv.due_date) if inv.due_date else None,
				"owner": inv.owner,
				"creation": str(inv.creation) if inv.creation else None,
				"modified": str(inv.modified) if inv.modified else None,
			})

	# Combine and sort
	all_records = sales_records + purchase_records
	all_records.sort(key=lambda r: r["posting_date"] or "", reverse=True)
	combined_total = len(all_records)

	# KPIs
	total_invoiced = sum(flt(r["grand_total"]) for r in all_records)
	total_paid = sum(flt(r["grand_total"]) - flt(r["outstanding_amount"]) for r in all_records)
	total_outstanding = sum(flt(r["outstanding_amount"]) for r in all_records)

	today = getdate(nowdate())
	overdue_count = sum(
		1 for r in all_records
		if r["outstanding_amount"] > 0 and r["due_date"] and getdate(r["due_date"]) < today
	)

	kpis = {
		"total_invoiced": round(total_invoiced, 2),
		"total_paid": round(total_paid, 2),
		"outstanding": round(total_outstanding, 2),
		"overdue_count": overdue_count,
	}

	# Paginate
	start = int(limit_start)
	length = int(limit_page_length)
	paginated = all_records[start:start + length]

	return {"kpis": kpis, "records": paginated, "total": combined_total}


@frappe.whitelist()
def get_invoice_detail(name, invoice_type="Sales"):
	"""Get invoice detail with line items and payments."""
	if not invoice_type:
		invoice_type = "Sales"
	doctype = "Sales Invoice" if invoice_type == "Sales" else "Purchase Invoice"

	if not frappe.db.exists(doctype, name):
		frappe.throw(f"{doctype} '{name}' not found", frappe.DoesNotExistError)

	doc = frappe.get_doc(doctype, name)

	# Get payment entries linked
	payments = []
	try:
		pe_refs = frappe.get_all(
			"Payment Entry Reference",
			filters={"reference_doctype": doctype, "reference_name": name},
			fields=["parent", "allocated_amount"],
		)
		for ref in pe_refs:
			pe = frappe.get_doc("Payment Entry", ref.parent)
			payments.append({
				"name": pe.name,
				"posting_date": str(pe.posting_date) if pe.posting_date else None,
				"paid_amount": flt(pe.paid_amount),
				"mode_of_payment": pe.mode_of_payment,
				"status": pe.docstatus,
				"allocated_amount": flt(ref.allocated_amount),
			})
	except Exception:
		pass

	# Audit trail
	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": doctype, "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	return {
		"doc": doc.as_dict(),
		"payments": payments,
		"audit_trail": versions,
	}
