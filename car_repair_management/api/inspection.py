import json
import frappe
from frappe.utils import getdate, nowdate, add_days, flt, now_datetime


@frappe.whitelist()
def get_inspection_history(date_from=None, date_to=None, vehicles=None, inspector=None,
                           inspection_type=None, result=None, form_template=None,
                           has_failures=None, search=None, limit_start=0, limit_page_length=20):
	"""Get inspection history with KPIs and records."""
	filters = {}

	if date_from and date_to:
		filters["inspection_date"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		filters["inspection_date"] = [">=", getdate(date_from)]
	elif date_to:
		filters["inspection_date"] = ["<=", getdate(date_to)]

	vehicle_list = _parse_list(vehicles)
	if vehicle_list:
		filters["vehicle"] = ["in", vehicle_list]
	if inspector:
		filters["inspector"] = inspector
	if inspection_type:
		filters["inspection_type"] = inspection_type
	if result:
		filters["result"] = result
	if form_template:
		filters["form_template"] = form_template
	if has_failures:
		filters["failures_count"] = [">", 0]

	or_filters = {}
	if search:
		or_filters = [
			["name", "like", f"%{search}%"],
			["vehicle", "like", f"%{search}%"],
			["title", "like", f"%{search}%"],
		]

	# KPIs - get all matching inspections for aggregation
	all_inspections = frappe.get_all(
		"Vehicle Inspection",
		filters=filters,
		or_filters=or_filters if or_filters else None,
		fields=["name", "result", "score", "failures_count", "follow_up_required", "follow_up_due_date", "status"],
	)

	total = len(all_inspections)
	pass_count = sum(1 for i in all_inspections if i.result == "Pass")
	fail_count = sum(1 for i in all_inspections if i.result == "Fail")
	scores = [flt(i.score) for i in all_inspections if i.score]
	avg_score = round(sum(scores) / len(scores), 1) if scores else 0

	today = getdate(nowdate())
	overdue_followups = sum(
		1 for i in all_inspections
		if i.follow_up_required and i.follow_up_due_date and getdate(i.follow_up_due_date) < today
	)

	kpis = {
		"total_inspections": total,
		"pass_rate": round(pass_count / total * 100, 1) if total else 0,
		"fail_count": fail_count,
		"average_score": avg_score,
		"overdue_followups": overdue_followups,
	}

	# Paginated records
	records = frappe.get_all(
		"Vehicle Inspection",
		filters=filters,
		or_filters=or_filters if or_filters else None,
		fields=[
			"name", "inspection_date", "vehicle", "form_template", "inspection_type",
			"inspector", "result", "score", "failures_count", "follow_up_required",
			"linked_work_order", "status", "title", "owner", "creation", "modified",
		],
		order_by="inspection_date desc, creation desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	return {"kpis": kpis, "records": records, "total": total}


@frappe.whitelist()
def get_inspection_detail(name):
	"""Get full inspection detail with checklist responses and failures."""
	doc = frappe.get_doc("Vehicle Inspection", name)

	failures = frappe.get_all(
		"Inspection Item Failure",
		filters={"inspection": name},
		fields=["name", "item_name", "severity", "status", "failure_reason",
				"resolution_type", "linked_work_order", "assigned_to", "evidence",
				"reported_date", "resolved_date", "is_recurring", "notes"],
		order_by="severity desc",
	)

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Vehicle Inspection", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	return {
		"doc": doc.as_dict(),
		"failures": failures,
		"audit_trail": versions,
	}


@frappe.whitelist()
def update_inspection(name, updates):
	"""Update editable fields on a Vehicle Inspection."""
	if isinstance(updates, str):
		updates = json.loads(updates)

	ALLOWED_FIELDS = {
		"status", "result", "score", "inspection_date", "inspection_type",
		"form_template", "inspector", "findings", "notes",
		"follow_up_required", "follow_up_due_date", "follow_up_assigned_to",
	}

	VALID_STATUSES = ("Draft", "In Progress", "Completed", "Cancelled")
	VALID_RESULTS = ("", "Pass", "Conditional", "Fail")

	if "status" in updates and updates["status"] not in VALID_STATUSES:
		frappe.throw(f"Invalid status: {updates['status']}. Must be one of {VALID_STATUSES}")

	if "result" in updates and updates["result"] is not None and updates["result"] not in VALID_RESULTS:
		frappe.throw(f"Invalid result: {updates['result']}. Must be one of {VALID_RESULTS}")

	if "score" in updates and updates["score"] is not None:
		score = flt(updates["score"])
		if score < 0 or score > 100:
			frappe.throw("Score must be between 0 and 100")

	if "follow_up_required" in updates and not updates["follow_up_required"]:
		updates["follow_up_due_date"] = None
		updates["follow_up_assigned_to"] = None

	doc = frappe.get_doc("Vehicle Inspection", name)
	for field, value in updates.items():
		if field in ALLOWED_FIELDS:
			doc.set(field, value)

	doc.save(ignore_permissions=True)

	return get_inspection_detail(name)


@frappe.whitelist()
def get_item_failures(date_from=None, date_to=None, vehicle=None, component=None,
                      severity=None, status=None, form_template=None, is_recurring=None,
                      search=None, limit_start=0, limit_page_length=20):
	"""Get item failures with KPIs."""
	filters = {}

	if date_from and date_to:
		filters["reported_date"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		filters["reported_date"] = [">=", getdate(date_from)]
	elif date_to:
		filters["reported_date"] = ["<=", getdate(date_to)]

	if vehicle:
		filters["vehicle"] = vehicle
	if component:
		filters["item_name"] = ["like", f"%{component}%"]
	if severity:
		filters["severity"] = severity
	if status:
		filters["status"] = status
	if is_recurring:
		filters["is_recurring"] = 1

	or_filters = None
	if search:
		or_filters = [
			["item_name", "like", f"%{search}%"],
			["vehicle", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
		]

	all_failures = frappe.get_all(
		"Inspection Item Failure",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "status", "item_name", "is_recurring", "reported_date", "resolved_date"],
	)

	total = len(all_failures)
	open_count = sum(1 for f in all_failures if f.status == "Open")
	recurring_count = sum(1 for f in all_failures if f.is_recurring)

	# Most failed component
	component_counts = {}
	for f in all_failures:
		component_counts[f.item_name] = component_counts.get(f.item_name, 0) + 1
	most_failed = max(component_counts, key=component_counts.get) if component_counts else ""

	# Avg resolution time
	resolution_times = []
	for f in all_failures:
		if f.resolved_date and f.reported_date:
			delta = (getdate(f.resolved_date) - getdate(f.reported_date)).days
			resolution_times.append(delta)
	avg_resolution = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0

	kpis = {
		"total_failures": total,
		"open_failures": open_count,
		"recurring_failures": recurring_count,
		"most_failed_component": most_failed,
		"avg_time_to_resolution": avg_resolution,
	}

	records = frappe.get_all(
		"Inspection Item Failure",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "reported_date", "vehicle", "item_name", "severity",
			"inspection", "status", "resolution_type", "linked_work_order",
			"assigned_to", "evidence", "is_recurring", "failure_reason",
			"owner", "creation", "modified",
		],
		order_by="reported_date desc, creation desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	return {"kpis": kpis, "records": records, "total": total}


@frappe.whitelist()
def get_failure_detail(name):
	"""Get failure detail with occurrence history."""
	doc = frappe.get_doc("Inspection Item Failure", name)

	# Get other failures of the same component on the same vehicle
	occurrence_history = frappe.get_all(
		"Inspection Item Failure",
		filters={
			"item_name": doc.item_name,
			"vehicle": doc.vehicle,
			"name": ["!=", name],
		},
		fields=["name", "reported_date", "severity", "status", "inspection", "resolved_date"],
		order_by="reported_date desc",
		limit=20,
	)

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Inspection Item Failure", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	return {
		"doc": doc.as_dict(),
		"occurrence_history": occurrence_history,
		"audit_trail": versions,
	}


@frappe.whitelist()
def get_schedules(date_from=None, date_to=None, vehicle=None, form_template=None,
                  inspector=None, status=None, frequency=None,
                  search=None, limit_start=0, limit_page_length=20):
	"""Get inspection schedules."""
	filters = {}

	if date_from and date_to:
		filters["scheduled_date"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		filters["scheduled_date"] = [">=", getdate(date_from)]
	elif date_to:
		filters["scheduled_date"] = ["<=", getdate(date_to)]

	if vehicle:
		filters["vehicle"] = vehicle
	if form_template:
		filters["form_template"] = form_template
	if inspector:
		filters["assigned_to"] = inspector
	if status:
		filters["status"] = status
	if frequency:
		filters["frequency"] = frequency

	or_filters = None
	if search:
		or_filters = [
			["title", "like", f"%{search}%"],
			["vehicle", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
		]

	records = frappe.get_all(
		"Inspection Schedule",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "title", "vehicle", "form_template", "scheduled_date",
			"frequency", "assigned_to", "status", "last_completed", "next_due",
			"auto_create_inspection", "owner", "creation", "modified",
		],
		order_by="next_due asc, scheduled_date asc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	total = frappe.db.count("Inspection Schedule", filters=filters)

	return {"records": records, "total": total}


@frappe.whitelist()
def get_schedule_detail(name):
	"""Get schedule detail with completion history."""
	doc = frappe.get_doc("Inspection Schedule", name)

	completed_inspections = frappe.get_all(
		"Vehicle Inspection",
		filters={"vehicle": doc.vehicle, "form_template": doc.form_template} if doc.form_template else {"vehicle": doc.vehicle},
		fields=["name", "inspection_date", "result", "score", "inspector", "status"],
		order_by="inspection_date desc",
		limit=20,
	)

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Inspection Schedule", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	return {
		"doc": doc.as_dict(),
		"completion_history": completed_inspections,
		"audit_trail": versions,
	}


@frappe.whitelist()
def get_form_templates(search=None, category=None, status=None, limit_start=0, limit_page_length=20):
	"""Get inspection form templates."""
	filters = {}
	if category:
		filters["category"] = category
	if status:
		filters["status"] = status

	or_filters = None
	if search:
		or_filters = [
			["title", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
		]

	records = frappe.get_all(
		"Inspection Form Template",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "title", "category", "description", "status",
			"version", "usage_count", "owner", "creation", "modified",
		],
		order_by="modified desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	# Get item count per template
	for r in records:
		r["item_count"] = frappe.db.count(
			"Inspection Form Item",
			filters={"parent": r["name"], "parenttype": "Inspection Form Template"},
		)

	total = frappe.db.count("Inspection Form Template", filters=filters)

	return {"records": records, "total": total}


@frappe.whitelist()
def get_form_template_detail(name):
	"""Get form template with all items."""
	doc = frappe.get_doc("Inspection Form Template", name)
	return {"doc": doc.as_dict()}


@frappe.whitelist()
def create_schedule(data):
	"""Create a new Inspection Schedule from JSON data."""
	if isinstance(data, str):
		data = json.loads(data)

	ALLOWED_FIELDS = {
		"title", "vehicle", "form_template", "assigned_to", "status",
		"frequency", "scheduled_date", "next_due", "auto_create_inspection",
		"notify_before_days", "notes",
	}

	doc = frappe.new_doc("Inspection Schedule")
	for field, value in data.items():
		if field in ALLOWED_FIELDS:
			doc.set(field, value)

	if not doc.next_due and doc.scheduled_date:
		doc.next_due = doc.scheduled_date

	doc.insert(ignore_permissions=True)

	return doc.as_dict()


@frappe.whitelist()
def update_schedule(name, updates):
	"""Update an Inspection Schedule."""
	if isinstance(updates, str):
		updates = json.loads(updates)

	ALLOWED_FIELDS = {
		"title", "vehicle", "form_template", "assigned_to", "status",
		"frequency", "scheduled_date", "next_due", "auto_create_inspection",
		"notify_before_days", "notes",
	}

	VALID_STATUSES = ("Active", "Paused", "Completed", "Cancelled")

	if "status" in updates and updates["status"] not in VALID_STATUSES:
		frappe.throw(f"Invalid status: {updates['status']}. Must be one of {VALID_STATUSES}")

	doc = frappe.get_doc("Inspection Schedule", name)
	for field, value in updates.items():
		if field in ALLOWED_FIELDS:
			doc.set(field, value)

	doc.save(ignore_permissions=True)

	return get_schedule_detail(name)


@frappe.whitelist()
def generate_inspection_now(schedule_name):
	"""Create a Vehicle Inspection from a schedule."""
	doc = frappe.get_doc("Inspection Schedule", schedule_name)

	inspection = frappe.new_doc("Vehicle Inspection")
	inspection.title = f"Scheduled: {doc.title}"
	inspection.vehicle = doc.vehicle
	inspection.form_template = doc.form_template
	inspection.inspection_date = now_datetime()
	inspection.inspection_type = "Periodic"
	inspection.inspector = doc.assigned_to
	inspection.status = "Draft"
	inspection.insert(ignore_permissions=True)

	FREQUENCY_DAYS = {
		"Daily": 1,
		"Weekly": 7,
		"Bi-Weekly": 14,
		"Monthly": 30,
		"Quarterly": 90,
		"Semi-Annually": 182,
		"Annually": 365,
	}

	doc.last_completed = nowdate()
	doc.last_inspection = inspection.name

	days = FREQUENCY_DAYS.get(doc.frequency)
	if days:
		doc.next_due = add_days(nowdate(), days)

	doc.save(ignore_permissions=True)

	return inspection.as_dict()


@frappe.whitelist()
def cancel_schedule(name):
	"""Set schedule status to Cancelled."""
	doc = frappe.get_doc("Inspection Schedule", name)
	doc.status = "Cancelled"
	doc.save(ignore_permissions=True)

	return {"status": "Cancelled"}


@frappe.whitelist()
def update_failure(name, updates):
	"""Update an Inspection Item Failure."""
	if isinstance(updates, str):
		updates = json.loads(updates)

	ALLOWED_FIELDS = {
		"status", "resolution_type", "linked_work_order", "assigned_to",
		"resolved_date", "notes", "severity", "is_recurring",
	}

	VALID_STATUSES = ("Open", "Converted", "Resolved", "Ignored")

	if "status" in updates and updates["status"] not in VALID_STATUSES:
		frappe.throw(f"Invalid status: {updates['status']}. Must be one of {VALID_STATUSES}")

	doc = frappe.get_doc("Inspection Item Failure", name)
	for field, value in updates.items():
		if field in ALLOWED_FIELDS:
			doc.set(field, value)

	if doc.status == "Resolved" and not doc.resolved_date:
		doc.resolved_date = nowdate()

	doc.save(ignore_permissions=True)

	return get_failure_detail(name)


@frappe.whitelist()
def create_work_order_from_failure(name):
	"""Create a Repair Order from a failure."""
	doc = frappe.get_doc("Inspection Item Failure", name)

	customer = frappe.db.get_value("Asset", {"vehicle": doc.vehicle}, "custodian")

	ro = frappe.new_doc("Repair Order")
	ro.order_for = "Customer"
	ro.customer = customer
	ro.vehicle = doc.vehicle
	ro.status = "Draft"
	ro.problem_description = f"Failure: {doc.item_name}\nReason: {doc.failure_reason or 'N/A'}"
	ro.insert(ignore_permissions=True)

	doc.linked_work_order = ro.name
	doc.status = "Converted"
	doc.resolution_type = "Work Order"
	doc.save(ignore_permissions=True)

	return {"repair_order": ro.name}


def _parse_list(value):
	"""Parse a list parameter that may be a JSON string."""
	if not value:
		return None
	if isinstance(value, str):
		try:
			return json.loads(value)
		except (json.JSONDecodeError, ValueError):
			return [value]
	return value
