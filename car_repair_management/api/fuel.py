import frappe
from frappe.utils import getdate, nowdate, flt


@frappe.whitelist()
def get_vehicle_quota_status(vehicle, month=None):
	if not month:
		month = getdate(nowdate()).strftime("%Y-%m")

	quota_name = f"FQ-{vehicle}-{month}"
	if frappe.db.exists("Vehicle Fuel Quota", quota_name):
		quota = frappe.get_doc("Vehicle Fuel Quota", quota_name)
	else:
		fuel_capacity = 0
		km_per_liter = 0
		monthly_override = 0
		try:
			vehicle_doc = frappe.get_doc("Vehicle", vehicle)
			fuel_capacity = flt(getattr(vehicle_doc, "custom_fuel_capacity_liters", 0))
			km_per_liter = flt(getattr(vehicle_doc, "custom_km_per_liter", 0))
			monthly_override = flt(getattr(vehicle_doc, "custom_monthly_fuel_quota", 0))
		except Exception:
			pass

		if monthly_override > 0:
			quota_liters = monthly_override
		elif fuel_capacity > 0:
			quota_liters = flt(fuel_capacity) * 2
		else:
			quota_liters = 0

		quota = frappe.get_doc({
			"doctype": "Vehicle Fuel Quota",
			"vehicle": vehicle,
			"quota_month": month,
			"fuel_capacity_liters": fuel_capacity,
			"km_per_liter": km_per_liter,
			"quota_liters": quota_liters,
			"consumed_liters": 0,
			"remaining_liters": quota_liters,
			"status": "Active",
		})
		quota.insert(ignore_permissions=True)
		frappe.db.commit()

	return {
		"name": quota.name,
		"vehicle": quota.vehicle,
		"quota_month": quota.quota_month,
		"fuel_capacity_liters": quota.fuel_capacity_liters,
		"km_per_liter": quota.km_per_liter,
		"quota_liters": quota.quota_liters,
		"consumed_liters": quota.consumed_liters,
		"remaining_liters": quota.remaining_liters,
		"status": quota.status,
	}


@frappe.whitelist()
def get_refueling_records(vehicle=None, month=None, status=None, search=None, limit_start=0, limit_page_length=20):
	filters = {}
	if vehicle:
		filters["vehicle"] = vehicle
	if status:
		filters["approval_status"] = status

	or_filters = {}
	if search:
		or_filters = {
			"vehicle": ["like", f"%{search}%"],
			"fuel_station": ["like", f"%{search}%"],
			"name": ["like", f"%{search}%"],
		}

	if month:
		filters["refuel_date"] = ["between", [f"{month}-01", f"{month}-31"]]

	records = frappe.get_all(
		"Vehicle Refueling Record",
		filters=filters,
		or_filters=or_filters if or_filters else None,
		fields=[
			"name", "vehicle", "refuel_date", "driver", "liters",
			"cost_per_liter", "total_cost", "fuel_station",
			"approval_status", "is_over_quota", "over_quota_liters",
			"quota_link", "odometer_reading",
		],
		order_by="refuel_date desc, creation desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	total = frappe.db.count("Vehicle Refueling Record", filters=filters)

	return {
		"records": records,
		"total": total,
	}


@frappe.whitelist()
def get_refueling_detail(name):
	doc = frappe.get_doc("Vehicle Refueling Record", name)
	result = doc.as_dict()

	if doc.quota_link and frappe.db.exists("Vehicle Fuel Quota", doc.quota_link):
		quota = frappe.get_doc("Vehicle Fuel Quota", doc.quota_link)
		result["quota"] = {
			"quota_liters": quota.quota_liters,
			"consumed_liters": quota.consumed_liters,
			"remaining_liters": quota.remaining_liters,
			"status": quota.status,
			"quota_month": quota.quota_month,
		}

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Vehicle Refueling Record", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)
	result["audit_trail"] = versions

	return result


@frappe.whitelist()
def create_refueling_record(
	vehicle,
	liters,
	refuel_date=None,
	odometer_reading=None,
	cost_per_liter=None,
	fuel_station=None,
	notes=None,
):
	liters = flt(liters)
	if not refuel_date:
		refuel_date = nowdate()

	month = getdate(refuel_date).strftime("%Y-%m")

	quota_status = get_vehicle_quota_status(vehicle, month)
	quota_name = quota_status["name"]
	consumed_before = flt(quota_status["consumed_liters"])
	consumed_after = consumed_before + liters
	quota_liters = flt(quota_status["quota_liters"])

	is_over_quota = 0
	over_quota_liters = 0
	approval_status = "Approved"

	if consumed_after > quota_liters:
		is_over_quota = 1
		over_quota_liters = consumed_after - quota_liters
		approval_status = "Pending Dept Head Approval"

	record = frappe.get_doc({
		"doctype": "Vehicle Refueling Record",
		"vehicle": vehicle,
		"liters": liters,
		"refuel_date": refuel_date,
		"odometer_reading": flt(odometer_reading) if odometer_reading else 0,
		"cost_per_liter": flt(cost_per_liter) if cost_per_liter else 0,
		"fuel_station": fuel_station,
		"notes": notes,
		"quota_link": quota_name,
		"consumed_before": consumed_before,
		"consumed_after": consumed_after,
		"is_over_quota": is_over_quota,
		"over_quota_liters": over_quota_liters,
		"approval_status": approval_status,
	})
	record.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"name": record.name,
		"approval_needed": is_over_quota == 1,
		"approval_status": approval_status,
		"over_quota_liters": over_quota_liters,
	}


@frappe.whitelist()
def approve_refueling(name, role):
	doc = frappe.get_doc("Vehicle Refueling Record", name)
	now = frappe.utils.now_datetime()
	user = frappe.session.user

	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")

	if role == "dept_head":
		doc.dept_head_approved_by = employee
		doc.dept_head_approved_on = now
		if doc.over_quota_liters and flt(doc.over_quota_liters) > 0:
			doc.approval_status = "Pending Depot Manager Approval"
		else:
			doc.approval_status = "Approved"
	elif role == "depot_manager":
		doc.depot_manager_approved_by = employee
		doc.depot_manager_approved_on = now
		doc.approval_status = "Approved"

	doc.save(ignore_permissions=True)

	if doc.approval_status == "Approved" and doc.quota_link:
		quota = frappe.get_doc("Vehicle Fuel Quota", doc.quota_link)
		quota.consumed_liters = flt(quota.consumed_liters) + flt(doc.liters)
		quota.remaining_liters = flt(quota.quota_liters) - flt(quota.consumed_liters)
		if quota.remaining_liters <= 0:
			quota.status = "Exhausted"
		quota.save(ignore_permissions=True)

	frappe.db.commit()

	return {"status": doc.approval_status, "name": doc.name}


@frappe.whitelist()
def reject_refueling(name, reason):
	doc = frappe.get_doc("Vehicle Refueling Record", name)
	doc.approval_status = "Rejected"
	doc.rejection_reason = reason
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"status": "Rejected", "name": doc.name}


@frappe.whitelist()
def get_fuel_quotas(vehicle=None, month=None, status=None, search=None, limit_start=0, limit_page_length=20):
	"""List fuel quotas with filters."""
	filters = {}
	if vehicle:
		filters["vehicle"] = vehicle
	if month:
		filters["quota_month"] = month
	if status:
		filters["status"] = status

	or_filters = None
	if search:
		or_filters = [
			["vehicle", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
		]

	records = frappe.get_all(
		"Vehicle Fuel Quota",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "vehicle", "quota_month", "fuel_capacity_liters",
			"km_per_liter", "quota_liters", "consumed_liters",
			"remaining_liters", "status",
		],
		order_by="quota_month desc, vehicle asc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	total = frappe.db.count("Vehicle Fuel Quota", filters=filters)

	return {"records": records, "total": total}


@frappe.whitelist()
def update_fuel_quota(name, quota_liters=None, status=None):
	"""Update a fuel quota's monthly limit or status."""
	doc = frappe.get_doc("Vehicle Fuel Quota", name)
	if quota_liters is not None:
		doc.quota_liters = flt(quota_liters)
		doc.remaining_liters = flt(doc.quota_liters) - flt(doc.consumed_liters)
		if doc.remaining_liters <= 0:
			doc.status = "Exhausted"
		elif doc.status == "Exhausted":
			doc.status = "Active"
	if status:
		doc.status = status
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return doc.as_dict()
