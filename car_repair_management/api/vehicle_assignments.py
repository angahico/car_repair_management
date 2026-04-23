import frappe
from frappe.utils import getdate, nowdate, add_days, flt


@frappe.whitelist()
def get_vehicle_assignments(range_start, range_end):
	"""Return vehicle assignment data for the calendar view.

	Each vehicle includes custodian and repair assignment blocks
	that overlap the requested date range.
	"""
	r_start = getdate(range_start)
	r_end = getdate(range_end)

	vehicles = frappe.get_all(
		"Vehicle",
		fields=[
			"name", "license_plate", "make", "model", "year",
			"employee", "custom_custodian", "acquisition_date", "creation",
			"custom_image", "custom_status", "custom_vehicle_type",
		],
		order_by="license_plate asc",
	)

	user_fullnames = _get_user_fullnames()
	employee_cache = {}

	repair_orders = frappe.get_all(
		"Repair Order",
		filters=[
			["vehicle", "is", "set"],
			["creation", "<=", r_end],
			["docstatus", "<", 2],
		],
		or_filters=[
			["sla_delivery_by", ">=", r_start],
			["sla_delivery_by", "is", "not set"],
		],
		fields=["name", "vehicle", "status", "creation", "sla_delivery_by", "problem_summary"],
	)

	ro_map = {}
	ro_names = []
	for ro in repair_orders:
		ro_map.setdefault(ro.vehicle, []).append(ro)
		ro_names.append(ro.name)

	op_lines_by_parent = {}
	if ro_names:
		op_lines = frappe.get_all(
			"Repair Operation Line",
			filters={"parent": ["in", ro_names]},
			fields=["parent", "assigned_to", "operation_name", "task"],
		)
		for op in op_lines:
			op_lines_by_parent.setdefault(op.parent, []).append(op)

	result = []
	for v in vehicles:
		assignments = []

		custodian_id = v.custom_custodian or v.employee
		if custodian_id:
			emp = _get_employee(custodian_id, employee_cache)
			if emp:
				acq = getdate(v.acquisition_date) if v.acquisition_date else getdate(v.creation)
				cust_start = max(acq, r_start)
				cust_end = r_end
				if cust_start <= cust_end:
					assignments.append({
						"id": "custodian:{}".format(v.name),
						"kind": "custodian",
						"start": str(cust_start),
						"end": str(cust_end),
						"title": emp.get("employee_name", ""),
						"subtitle": emp.get("designation", "") or "",
						"color": "blue",
						"reference": {"doctype": "Employee", "name": custodian_id},
					})

		for ro in ro_map.get(v.name, []):
			ro_start = getdate(ro.creation)
			ro_end = getdate(ro.sla_delivery_by) if ro.sla_delivery_by else r_end
			block_start = max(ro_start, r_start)
			block_end = min(ro_end, r_end)
			if block_start > block_end:
				continue

			ops = op_lines_by_parent.get(ro.name, [])
			if ops:
				seen = {}
				for op in ops:
					key = op.assigned_to or ""
					if key in seen:
						continue
					seen[key] = True
					user_display = user_fullnames.get(op.assigned_to, op.assigned_to or "Unassigned")
					subtitle_parts = [op.assigned_to or "Unassigned"]
					if op.operation_name:
						subtitle_parts.append(op.operation_name)
					assignments.append({
						"id": "repair:{}:{}".format(ro.name, op.assigned_to or ""),
						"kind": "repair",
						"start": str(block_start),
						"end": str(block_end),
						"title": ro.name,
						"subtitle": " - ".join(subtitle_parts),
						"color": "amber",
						"reference": {"doctype": "Repair Order", "name": ro.name},
					})
			else:
				assignments.append({
					"id": "repair:{}".format(ro.name),
					"kind": "repair",
					"start": str(block_start),
					"end": str(block_end),
					"title": ro.name,
					"subtitle": ro.problem_summary or "",
					"color": "amber",
					"reference": {"doctype": "Repair Order", "name": ro.name},
				})

		result.append({
			"name": v.name,
			"license_plate": v.license_plate,
			"make": v.make,
			"model": v.model,
			"year": v.year,
			"thumbnail_url": v.custom_image,
			"status": v.custom_status or "Active",
			"vehicle_type": v.custom_vehicle_type or "Car",
			"assignments": assignments,
		})

	return {
		"range": {"start": str(r_start), "end": str(r_end)},
		"vehicles": result,
	}


def _get_employee(employee_id, cache):
	if employee_id in cache:
		return cache[employee_id]
	try:
		emp = frappe.db.get_value(
			"Employee",
			employee_id,
			["name", "employee_name", "image", "designation"],
			as_dict=True,
		)
	except Exception:
		emp = None
	cache[employee_id] = emp
	return emp


def _get_user_fullnames():
	users = frappe.get_all("User", fields=["name", "full_name"])
	return {u.name: u.full_name or u.name for u in users}
