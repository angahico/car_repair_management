import frappe
from frappe.utils import getdate, nowdate, add_days, flt


@frappe.whitelist()
def get_customers(search=None, customer_group=None, customer_type=None,
                  territory=None, status=None, limit_start=0, limit_page_length=20):
	"""Get customers with KPIs and records."""
	filters = {}

	if customer_group:
		filters["customer_group"] = customer_group
	if customer_type:
		filters["customer_type"] = customer_type
	if territory:
		filters["territory"] = territory
	if status == "Active":
		filters["disabled"] = 0
	elif status == "Inactive":
		filters["disabled"] = 1

	or_filters = None
	if search:
		or_filters = [
			["name", "like", f"%{search}%"],
			["customer_name", "like", f"%{search}%"],
			["mobile_no", "like", f"%{search}%"],
			["email_id", "like", f"%{search}%"],
		]

	fields = [
		"name", "customer_name", "customer_type", "customer_group",
		"territory", "mobile_no", "email_id", "disabled",
		"creation", "modified", "owner",
	]

	# KPIs - get all matching customers for aggregation
	all_customers = frappe.get_all(
		"Customer",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "disabled", "creation"],
	)

	total = len(all_customers)
	active_customers = sum(1 for c in all_customers if not c.disabled)
	thirty_days_ago = getdate(add_days(nowdate(), -30))
	new_customers_30d = sum(1 for c in all_customers if getdate(c.creation) >= thirty_days_ago)

	# Outstanding balance from Sales Invoice
	try:
		outstanding = frappe.get_all(
			"Sales Invoice",
			filters={"docstatus": 1, "outstanding_amount": [">", 0]},
			fields=["customer", "outstanding_amount"],
		)
		outstanding_map = {}
		for o in outstanding:
			outstanding_map[o.customer] = outstanding_map.get(o.customer, 0) + flt(o.outstanding_amount)
		customers_with_outstanding = len(outstanding_map)
	except Exception:
		outstanding_map = {}
		customers_with_outstanding = 0

	kpis = {
		"total_customers": total,
		"active_customers": active_customers,
		"new_customers_30d": new_customers_30d,
		"customers_with_outstanding": customers_with_outstanding,
	}

	# Paginated records
	records = frappe.get_all(
		"Customer",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by="modified desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	for r in records:
		r["outstanding_amount"] = flt(outstanding_map.get(r["name"], 0))

	return {"kpis": kpis, "records": records, "total": total}


@frappe.whitelist()
def get_customer_detail(name):
	"""Get full customer detail with vehicles, orders, invoices, addresses, and audit trail."""
	doc = frappe.get_doc("Customer", name)

	# Vehicles linked to customer
	try:
		# Find vehicles via Repair Orders for this customer
		vehicle_names = frappe.get_all(
			"Repair Order",
			filters={"customer": name},
			pluck="vehicle",
			distinct=True,
		)
		vehicles = []
		if vehicle_names:
			vehicles = frappe.get_all(
				"Vehicle",
				filters={"name": ["in", vehicle_names]},
				fields=["name", "license_plate", "make", "model", "year", "color"],
			)
	except Exception:
		vehicles = []

	# Repair orders
	try:
		orders = frappe.get_all(
			"Repair Order",
			filters={"customer": name},
			fields=["name", "status", "vehicle", "creation", "modified", "grand_total"],
			order_by="creation desc",
			limit=50,
		)
	except Exception:
		orders = []

	# Sales invoices
	try:
		invoices = frappe.get_all(
			"Sales Invoice",
			filters={"customer": name, "docstatus": 1},
			fields=["name", "posting_date", "status", "grand_total", "outstanding_amount", "currency"],
			order_by="posting_date desc",
			limit=50,
		)
	except Exception:
		invoices = []

	# Addresses via Dynamic Link
	try:
		address_names = frappe.get_all(
			"Dynamic Link",
			filters={"link_doctype": "Customer", "link_name": name, "parenttype": "Address"},
			pluck="parent",
		)
		addresses = frappe.get_all(
			"Address",
			filters={"name": ["in", address_names]},
			fields=["name", "address_line1", "city", "state", "country", "pincode", "phone"],
		) if address_names else []
	except Exception:
		addresses = []

	# Audit trail
	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Customer", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	return {
		"doc": doc.as_dict(),
		"vehicles": vehicles,
		"repair_orders": orders,
		"invoices": invoices,
		"addresses": addresses,
		"audit_trail": versions,
	}
