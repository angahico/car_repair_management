import frappe
from frappe.utils import getdate, nowdate, add_days, flt


@frappe.whitelist()
def get_employees(search=None, department=None, designation=None, status=None,
				  supervisor=None, limit_start=0, limit_page_length=20):
	"""Get employees with KPIs and work order counts."""
	filters = {}

	if department:
		filters["department"] = department
	if designation:
		filters["designation"] = designation
	if status:
		filters["status"] = status
	if supervisor:
		filters["reports_to"] = supervisor

	or_filters = None
	if search:
		or_filters = [
			["name", "like", f"%{search}%"],
			["employee_name", "like", f"%{search}%"],
			["cell_number", "like", f"%{search}%"],
			["company_email", "like", f"%{search}%"],
		]

	# All matching for KPIs
	all_employees = frappe.get_all(
		"Employee",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "status"],
	)

	total = len(all_employees)
	active_count = sum(1 for e in all_employees if e.status == "Active")

	# Work orders in progress
	try:
		assigned_wo = frappe.db.count(
			"Repair Order",
			filters={"status": ["in", ["In Progress", "Scheduled", "Awaiting Parts"]]},
		)
	except Exception:
		assigned_wo = 0

	# Avg resolution time
	try:
		completed = frappe.get_all(
			"Repair Order",
			filters={"status": ["in", ["Delivered", "Closed"]]},
			fields=["creation", "modified"],
			limit=100,
		)
		times = []
		for ro in completed:
			if ro.creation and ro.modified:
				delta = (getdate(ro.modified) - getdate(ro.creation)).days
				times.append(max(delta, 0))
		avg_res = round(sum(times) / len(times), 1) if times else 0
	except Exception:
		avg_res = 0

	kpis = {
		"total_employees": total,
		"active_employees": active_count,
		"assigned_work_orders": assigned_wo,
		"avg_resolution_time": avg_res,
	}

	# Paginated records
	records = frappe.get_all(
		"Employee",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "employee_name", "department", "designation", "status",
			"image", "cell_number", "company_email", "date_of_joining",
			"reports_to", "modified", "owner", "creation",
		],
		order_by="modified desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	# Get assigned WO counts per employee
	wo_counts = {}
	try:
		wos = frappe.get_all(
			"Repair Order",
			filters={"status": ["not in", ["Cancelled", "Closed", "Delivered"]]},
			fields=["assigned_to"],
		)
		for wo in wos:
			if wo.get("assigned_to"):
				wo_counts[wo.assigned_to] = wo_counts.get(wo.assigned_to, 0) + 1
	except Exception:
		pass

	for r in records:
		r["assigned_wo_count"] = wo_counts.get(r["name"], 0)

	return {"kpis": kpis, "records": records, "total": total}


@frappe.whitelist()
def get_employee_detail(name):
	"""Get employee detail with performance and assignments."""
	doc = frappe.get_doc("Employee", name)

	# Vehicle assignments — drivers (from Vehicle Driver child table) + custodian
	vehicle_assignments = []
	try:
		driver_entries = frappe.get_all(
			"Vehicle Driver",
			filters={"employee": name},
			fields=["parent", "status", "assigned_date", "ended_date"],
		)
		if driver_entries:
			vehicle_names = list({d.parent for d in driver_entries})
			vehicle_map = {}
			for v in frappe.get_all(
				"Vehicle",
				filters={"name": ["in", vehicle_names]},
				fields=["name", "license_plate", "make", "model", "custom_status as vehicle_status"],
			):
				vehicle_map[v.name] = v
			for d in driver_entries:
				veh = vehicle_map.get(d.parent, {})
				vehicle_assignments.append({
					"vehicle": d.parent,
					"license_plate": veh.get("license_plate") or d.parent,
					"make": veh.get("make"),
					"model": veh.get("model"),
					"vehicle_status": veh.get("vehicle_status"),
					"role": "Driver",
					"assignment_status": d.status,
					"assigned_date": d.assigned_date,
					"ended_date": d.ended_date,
				})

		# Custodian assignments
		custodian_vehicles = frappe.get_all(
			"Vehicle",
			filters={"custom_custodian": name},
			fields=["name", "license_plate", "make", "model", "custom_status as vehicle_status"],
		)
		# Avoid duplicating vehicles already listed as driver
		driver_vehicle_set = {d.parent for d in driver_entries}
		for v in custodian_vehicles:
			vehicle_assignments.append({
				"vehicle": v.name,
				"license_plate": v.license_plate or v.name,
				"make": v.make,
				"model": v.model,
				"vehicle_status": v.vehicle_status,
				"role": "Custodian",
				"assignment_status": "Active",
				"assigned_date": None,
				"ended_date": None,
			})
	except Exception:
		pass

	# Repair orders — assigned via Repair Operation Line child table
	# The child links to User, so resolve employee -> user_id first
	user_id = doc.get("user_id")
	ro_names = []
	try:
		if user_id:
			op_lines = frappe.get_all(
				"Repair Operation Line",
				filters={"assigned_to": user_id},
				fields=["parent"],
			)
			ro_names = list({o.parent for o in op_lines})
		if ro_names:
			repair_orders = frappe.get_all(
				"Repair Order",
				filters={"name": ["in", ro_names]},
				fields=["name", "vehicle", "status", "creation", "total_job_cost", "modified"],
				order_by="creation desc",
				limit=20,
			)
		else:
			repair_orders = []
	except Exception:
		repair_orders = []

	# Performance — based on the same repair orders
	completed_count = 0
	active_count = 0
	avg_days = 0
	try:
		if ro_names:
			all_orders = frappe.get_all(
				"Repair Order",
				filters={"name": ["in", ro_names]},
				fields=["status", "creation", "modified"],
			)
		else:
			all_orders = []
		completed_count = sum(1 for o in all_orders if o.status in ("Delivered", "Closed"))
		active_count = sum(1 for o in all_orders if o.status in ("In Progress", "Scheduled", "Awaiting Parts"))
		comp_times = []
		for o in all_orders:
			if o.status in ("Delivered", "Closed") and o.creation and o.modified:
				delta = (getdate(o.modified) - getdate(o.creation)).days
				comp_times.append(max(delta, 0))
		avg_days = round(sum(comp_times) / len(comp_times), 1) if comp_times else 0
	except Exception:
		pass

	performance = {
		"completed_wo_count": completed_count,
		"active_wo_count": active_count,
		"avg_completion_days": avg_days,
	}

	# Audit trail
	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Employee", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	return {
		"doc": doc.as_dict(),
		"vehicle_assignments": vehicle_assignments,
		"repair_orders": repair_orders,
		"performance": performance,
		"audit_trail": versions,
	}
