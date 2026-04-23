import json
import frappe
from frappe.utils import getdate, nowdate, flt


@frappe.whitelist()
def get_expenses(date_from=None, date_to=None, vehicle=None, category=None,
				 vendor=None, work_order=None, payment_status=None, has_receipt=None,
				 search=None, limit_start=0, limit_page_length=20):
	"""Get expenses with KPIs and records."""
	filters = {}

	if date_from and date_to:
		filters["expense_date"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		filters["expense_date"] = [">=", getdate(date_from)]
	elif date_to:
		filters["expense_date"] = ["<=", getdate(date_to)]

	if vehicle:
		filters["vehicle"] = vehicle
	if category:
		filters["category"] = category
	if vendor:
		filters["vendor"] = ["like", f"%{vendor}%"]
	if work_order == "linked":
		filters["work_order"] = ["!=", ""]
	elif work_order == "unlinked":
		filters["work_order"] = ["in", ["", None]]
	if payment_status:
		filters["payment_status"] = payment_status
	if has_receipt and int(has_receipt):
		filters["receipt_attachment"] = ["!=", ""]

	or_filters = None
	if search:
		or_filters = [
			["name", "like", f"%{search}%"],
			["vehicle", "like", f"%{search}%"],
			["vendor", "like", f"%{search}%"],
			["title", "like", f"%{search}%"],
			["notes", "like", f"%{search}%"],
		]

	# KPIs - get all matching expenses for aggregation
	all_expenses = frappe.get_all(
		"Vehicle Expense",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "amount", "category", "vehicle", "work_order", "receipt_attachment"],
	)

	total = len(all_expenses)
	total_expenses = sum(flt(e.amount) for e in all_expenses)
	fuel_spend = sum(flt(e.amount) for e in all_expenses if e.category == "Fuel")
	maintenance_categories = ("Parts", "Labor", "External Service")
	maintenance_spend = sum(flt(e.amount) for e in all_expenses if e.category in maintenance_categories)

	distinct_vehicles = set(e.vehicle for e in all_expenses if e.vehicle)
	avg_per_vehicle = round(total_expenses / len(distinct_vehicles), 2) if distinct_vehicles else 0

	unlinked_count = sum(1 for e in all_expenses if not e.work_order)
	missing_receipts = sum(1 for e in all_expenses if not e.receipt_attachment)

	kpis = {
		"total_expenses": total_expenses,
		"fuel_spend": fuel_spend,
		"maintenance_spend": maintenance_spend,
		"avg_per_vehicle": avg_per_vehicle,
		"unlinked_count": unlinked_count,
		"missing_receipts": missing_receipts,
	}

	# Paginated records
	records = frappe.get_all(
		"Vehicle Expense",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "title", "expense_date", "vehicle", "category", "amount",
			"vendor", "work_order", "payment_status", "payment_method",
			"receipt_attachment", "notes", "owner", "creation", "modified",
		],
		order_by="expense_date desc, creation desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	return {"kpis": kpis, "records": records, "total": total}


@frappe.whitelist()
def get_expense_detail(name):
	"""Get single expense with audit trail."""
	doc = frappe.get_doc("Vehicle Expense", name)

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Vehicle Expense", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	return {
		"doc": doc.as_dict(),
		"audit_trail": versions,
	}


@frappe.whitelist()
def create_expense(**kwargs):
	"""Create a new Vehicle Expense."""
	kwargs.pop("cmd", None)
	doc = frappe.get_doc({"doctype": "Vehicle Expense", **kwargs}).insert()
	return doc.as_dict()


@frappe.whitelist()
def update_expense(name, **kwargs):
	"""Update an existing Vehicle Expense."""
	kwargs.pop("cmd", None)
	doc = frappe.get_doc("Vehicle Expense", name)
	doc.update(kwargs)
	doc.save()
	return doc.as_dict()
