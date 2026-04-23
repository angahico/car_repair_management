import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_parts(search=None, item_group=None, stock_status=None, is_stock_item=None,
              uom=None, limit_start=0, limit_page_length=20):
	"""Get parts/items with KPIs and stock info."""
	filters = {}

	if is_stock_item is not None and is_stock_item != "":
		filters["is_stock_item"] = int(is_stock_item)
	if item_group:
		filters["item_group"] = item_group
	if uom:
		filters["stock_uom"] = uom

	or_filters = None
	if search:
		or_filters = [
			["item_code", "like", f"%{search}%"],
			["item_name", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
		]

	fields = [
		"name", "item_name", "item_group", "stock_uom", "is_stock_item",
		"is_fixed_asset", "image", "description", "standard_rate",
		"valuation_rate", "owner", "creation", "modified",
	]

	# Get all matching items for KPI aggregation
	all_items = frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
	)

	# Get reorder levels from child table
	reorder_map = {}
	try:
		reorders = frappe.get_all("Item Reorder",
			fields=["parent", "warehouse_reorder_level"],
			filters={"parenttype": "Item"})
		for r in reorders:
			reorder_map[r.parent] = max(reorder_map.get(r.parent, 0), flt(r.warehouse_reorder_level))
	except Exception:
		pass

	# Get stock levels from Bin
	stock_map = {}
	stock_item_codes = [r.name for r in all_items if r.is_stock_item]
	if stock_item_codes:
		try:
			from frappe.query_builder.functions import Sum

			Bin = frappe.qb.DocType("Bin")
			stock_data = (
				frappe.qb.from_(Bin)
				.select(Bin.item_code, Sum(Bin.actual_qty).as_("total_qty"))
				.where(Bin.item_code.isin(stock_item_codes))
				.groupby(Bin.item_code)
				.run(as_dict=True)
			)
			stock_map = {s.item_code: flt(s.total_qty) for s in stock_data}
		except Exception:
			stock_map = {}

	# Enrich records with stock info
	for r in all_items:
		if r.is_stock_item:
			r["current_qty"] = stock_map.get(r.name, 0)
			r["reorder_level"] = reorder_map.get(r.name, 0)
			reorder = flt(r["reorder_level"])
			qty = r["current_qty"]
			if qty <= 0:
				r["stock_status"] = "Out of Stock"
			elif reorder and qty <= reorder:
				r["stock_status"] = "Low"
			else:
				r["stock_status"] = "In Stock"
		else:
			r["current_qty"] = 0
			r["stock_status"] = "N/A"

	# Filter by stock_status if requested
	if stock_status:
		status_map = {"in_stock": "In Stock", "low": "Low", "out": "Out of Stock"}
		target_status = status_map.get(stock_status)
		if target_status:
			all_items = [r for r in all_items if r.get("stock_status") == target_status]

	# KPIs
	total = len(all_items)
	in_stock_count = sum(1 for r in all_items if r.get("stock_status") == "In Stock")
	low_stock_count = sum(1 for r in all_items if r.get("stock_status") == "Low")
	out_of_stock_count = sum(1 for r in all_items if r.get("stock_status") == "Out of Stock")

	kpis = {
		"total_items": total,
		"in_stock_count": in_stock_count,
		"low_stock_count": low_stock_count,
		"out_of_stock_count": out_of_stock_count,
	}

	# Paginate in Python (since stock_status filtering happens post-query)
	start = int(limit_start)
	length = int(limit_page_length)
	records = all_items[start:start + length]

	return {"kpis": kpis, "records": records, "total": total}


@frappe.whitelist()
def get_part_detail(name):
	"""Get single item with stock details and usage history."""
	doc = frappe.get_doc("Item", name)

	# Stock by warehouse
	stock_by_warehouse = []
	try:
		stock_by_warehouse = frappe.get_all(
			"Bin",
			filters={"item_code": name},
			fields=["warehouse", "actual_qty", "reserved_qty", "ordered_qty"],
			order_by="actual_qty desc",
		)
	except Exception:
		stock_by_warehouse = []

	# Usage history from Repair Parts Plan
	usage_history = []
	try:
		usage_history = frappe.get_all(
			"Repair Parts Plan",
			filters={"item": name},
			fields=["parent as repair_order", "item", "qty", "rate", "amount"],
			order_by="creation desc",
			limit=20,
		)
	except Exception:
		usage_history = []

	# Audit trail
	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Item", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	return {
		"doc": doc.as_dict(),
		"stock_by_warehouse": stock_by_warehouse,
		"usage_history": usage_history,
		"audit_trail": versions,
	}


@frappe.whitelist()
def create_part(**kwargs):
	"""Create a new Item."""
	kwargs.pop("cmd", None)
	doc = frappe.get_doc({"doctype": "Item", **kwargs}).insert()
	return doc.as_dict()
