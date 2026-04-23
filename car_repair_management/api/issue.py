import json
import frappe
from frappe.utils import getdate, nowdate, flt, now_datetime


@frappe.whitelist()
def get_issues(date_from=None, date_to=None, vehicle=None, source=None,
               category=None, severity=None, status=None, assigned_to=None,
               search=None, limit_start=0, limit_page_length=20):
	"""Get issues with KPIs - uses Frappe core Issue DocType with custom fields."""
	filters = {}

	if date_from and date_to:
		filters["creation"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		filters["creation"] = [">=", getdate(date_from)]
	elif date_to:
		filters["creation"] = ["<=", getdate(date_to)]

	if vehicle:
		filters["custom_vehicle"] = vehicle
	if source:
		filters["custom_source"] = source
	if category:
		filters["custom_category"] = category
	if severity:
		filters["custom_severity"] = severity
	if status:
		filters["status"] = status
	if assigned_to:
		filters["custom_assigned_to"] = assigned_to

	or_filters = None
	if search:
		or_filters = [
			["subject", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
			["custom_vehicle", "like", f"%{search}%"],
		]

	# KPIs
	all_issues = frappe.get_all(
		"Issue",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "status", "custom_severity", "creation", "sla_resolution_date", "first_responded_on"],
	)

	total = len(all_issues)
	today = getdate(nowdate())
	new_count = sum(1 for i in all_issues if i.status == "Open")
	open_count = sum(1 for i in all_issues if i.status in ("Open", "Replied"))
	critical_open = sum(
		1 for i in all_issues
		if i.status in ("Open", "Replied") and i.custom_severity == "Critical"
	)

	# Avg triage time (time to first response)
	triage_times = []
	for i in all_issues:
		if i.first_responded_on and i.creation:
			delta = (getdate(i.first_responded_on) - getdate(i.creation)).days
			triage_times.append(max(delta, 0))
	avg_triage = round(sum(triage_times) / len(triage_times), 1) if triage_times else 0

	# Avg resolution time
	resolution_times = []
	for i in all_issues:
		if i.sla_resolution_date and i.creation:
			delta = (getdate(i.sla_resolution_date) - getdate(i.creation)).days
			resolution_times.append(max(delta, 0))
	avg_resolve = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0

	kpis = {
		"new_issues": new_count,
		"open_issues": open_count,
		"avg_time_to_triage": avg_triage,
		"avg_time_to_resolve": avg_resolve,
		"critical_open": critical_open,
	}

	records = frappe.get_all(
		"Issue",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "subject", "custom_vehicle", "custom_severity", "status",
			"custom_category", "raised_by", "creation", "custom_assigned_to",
			"custom_linked_work_order", "custom_linked_inspection",
			"custom_linked_fault", "custom_source", "modified", "owner",
			"custom_workflow_state",
		],
		order_by="modified desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	return {"kpis": kpis, "records": records, "total": total}


@frappe.whitelist()
def get_issue_detail(name):
	"""Get issue detail with activity and relationships."""
	doc = frappe.get_doc("Issue", name)

	# Get comments/activity
	comments = frappe.get_all(
		"Comment",
		filters={"reference_doctype": "Issue", "reference_name": name, "comment_type": ["in", ["Comment", "Info"]]},
		fields=["name", "comment_by", "creation", "content", "comment_type"],
		order_by="creation desc",
		limit=50,
	)

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Issue", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	# Determine available actions
	available_actions = []
	employee = _get_current_employee()
	workflow_state = doc.get("custom_workflow_state") or ""
	vehicle_role = _get_employee_vehicle_role(employee, doc.get("custom_vehicle"))

	if workflow_state == "Pending Custodian Approval" and vehicle_role == "custodian":
		available_actions.append("approve")
		available_actions.append("reject")

	if workflow_state == "Submitted" and not doc.get("custom_linked_work_order"):
		available_actions.append("create_work_order")

	if workflow_state in ("Submitted", "Pending Custodian Approval") and doc.status != "Closed":
		available_actions.append("close")

	if doc.status != "Closed":
		available_actions.append("mark_duplicate")

	if doc.get("custom_linked_work_order"):
		available_actions.append("open_draft_ro")

	return {
		"doc": doc.as_dict(),
		"comments": comments,
		"audit_trail": versions,
		"available_actions": available_actions,
	}


@frappe.whitelist()
def get_faults(date_from=None, date_to=None, vehicle=None, detection_type=None,
               fault_code=None, component_system=None, confirmed=None, severity=None,
               status=None, search=None, limit_start=0, limit_page_length=20):
	"""Get vehicle faults list."""
	filters = {}

	if date_from and date_to:
		filters["reported_date"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		filters["reported_date"] = [">=", getdate(date_from)]
	elif date_to:
		filters["reported_date"] = ["<=", getdate(date_to)]

	if vehicle:
		filters["vehicle"] = vehicle
	if detection_type:
		filters["detection_type"] = detection_type
	if fault_code:
		filters["fault_code"] = ["like", f"%{fault_code}%"]
	if component_system:
		filters["component_system"] = component_system
	if confirmed:
		filters["confirmed"] = confirmed
	if severity:
		filters["severity"] = severity
	if status:
		filters["status"] = status

	or_filters = None
	if search:
		or_filters = [
			["title", "like", f"%{search}%"],
			["vehicle", "like", f"%{search}%"],
			["fault_code", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
		]

	records = frappe.get_all(
		"Vehicle Fault",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "title", "vehicle", "fault_code", "detection_type",
			"severity", "confirmed", "status", "linked_work_order",
			"linked_inspection", "reported_by", "reported_date",
			"resolved_date", "component_system", "evidence",
			"owner", "creation", "modified",
		],
		order_by="reported_date desc, creation desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	total = frappe.db.count("Vehicle Fault", filters=filters)

	return {"records": records, "total": total}


@frappe.whitelist()
def get_fault_detail(name):
	"""Get fault detail with occurrence history."""
	doc = frappe.get_doc("Vehicle Fault", name)

	# Occurrence history - same vehicle, similar fault code or component
	occurrence_filters = {"vehicle": doc.vehicle, "name": ["!=", name]}
	if doc.component_system:
		occurrence_filters["component_system"] = doc.component_system

	occurrence_history = frappe.get_all(
		"Vehicle Fault",
		filters=occurrence_filters,
		fields=["name", "title", "fault_code", "reported_date", "severity", "status", "resolved_date"],
		order_by="reported_date desc",
		limit=20,
	)

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Vehicle Fault", "docname": name},
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
def convert_issue_to_work_order(issue_name, order_for="Company", customer=None, company=None):
	"""Convert an issue to a Repair Order, linking them together."""
	issue = frappe.get_doc("Issue", issue_name)

	# Guard: only allow when workflow state is Submitted, empty, or not set
	ws = issue.get("custom_workflow_state") or ""
	if ws and ws not in ("Submitted", ""):
		frappe.throw(f"Cannot create work order: issue workflow state is '{ws}'")

	if order_for == "Customer" and not customer:
		frappe.throw("Customer is required when order is for a Customer")
	if order_for == "Company" and not company:
		company = frappe.defaults.get_user_default("Company") or frappe.defaults.get_global_default("company")
		if not company:
			frappe.throw("Company is required when order is for the Company")

	# Map severity to RO priority
	severity_priority_map = {
		"Critical": "Urgent",
		"High": "High",
		"Medium": "Normal",
		"Low": "Low",
	}
	priority = severity_priority_map.get(issue.custom_severity or "", "Normal")

	ro = frappe.get_doc({
		"doctype": "Repair Order",
		"naming_series": "RO-.YYYY.-.#####",
		"vehicle": issue.custom_vehicle,
		"order_for": order_for,
		"customer": customer if order_for == "Customer" else None,
		"company": company if order_for == "Company" else None,
		"problem_summary": issue.subject,
		"problem_details": issue.description,
		"priority": priority,
		"status": "Draft",
	})
	ro.insert(ignore_permissions=True)

	issue.custom_linked_work_order = ro.name
	issue.custom_workflow_state = "Work Order Created"
	issue.save(ignore_permissions=True)

	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "Issue",
		"reference_name": issue_name,
		"content": f"Work order {ro.name} created from this issue",
	}).insert(ignore_permissions=True)

	frappe.db.commit()
	return ro.name


@frappe.whitelist()
def mark_issue_duplicate(issue_name, duplicate_of):
	"""Mark an issue as duplicate and close it."""
	issue = frappe.get_doc("Issue", issue_name)

	# Use "Replied" if "Closed" is not a valid status option
	try:
		issue.status = "Closed"
		issue.flags.ignore_permissions = True
		issue.save()
	except Exception:
		issue.reload()
		issue.status = "Replied"
		issue.flags.ignore_permissions = True
		issue.save()

	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "Issue",
		"reference_name": issue_name,
		"content": f"Marked as duplicate of {duplicate_of}",
	}).insert(ignore_permissions=True)

	frappe.db.commit()
	return "ok"


@frappe.whitelist()
def close_issue_with_reason(issue_name, reason):
	"""Close an issue with a resolution reason."""
	issue = frappe.get_doc("Issue", issue_name)
	issue.custom_resolution_notes = reason

	try:
		issue.status = "Closed"
		issue.flags.ignore_permissions = True
		issue.save()
	except Exception:
		issue.reload()
		issue.custom_resolution_notes = reason
		issue.status = "Replied"
		issue.flags.ignore_permissions = True
		issue.save()

	frappe.db.commit()
	return "ok"


@frappe.whitelist()
def get_recalls(manufacturer=None, model=None, year_from=None, year_to=None,
                status=None, priority=None, search=None,
                limit_start=0, limit_page_length=20):
	"""Get vehicle recalls list."""
	filters = {}

	if manufacturer:
		filters["manufacturer"] = manufacturer
	if model:
		filters["affected_models"] = ["like", f"%{model}%"]
	if status:
		filters["status"] = status
	if priority:
		filters["priority"] = priority

	or_filters = None
	if search:
		or_filters = [
			["title", "like", f"%{search}%"],
			["manufacturer", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
		]

	records = frappe.get_all(
		"Vehicle Recall",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "title", "manufacturer", "affected_models", "affected_years",
			"issue_type", "recall_start_date", "deadline", "status", "priority",
			"vehicles_affected", "vehicles_completed", "compliance_pct",
			"external_reference", "owner", "creation", "modified",
		],
		order_by="creation desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)

	total = frappe.db.count("Vehicle Recall", filters=filters)

	return {"records": records, "total": total}


@frappe.whitelist()
def get_recall_detail(name):
	"""Get recall detail with affected vehicles and progress."""
	doc = frappe.get_doc("Vehicle Recall", name)

	# Find affected vehicles by matching manufacturer/model/year
	vehicle_filters = {}
	if doc.manufacturer:
		vehicle_filters["make"] = doc.manufacturer
	if doc.affected_models:
		models = [m.strip() for m in doc.affected_models.split(",") if m.strip()]
		if models:
			vehicle_filters["model"] = ["in", models]

	affected_vehicles = []
	if vehicle_filters:
		affected_vehicles = frappe.get_all(
			"Vehicle",
			filters=vehicle_filters,
			fields=["name", "license_plate", "make", "model", "year"],
			limit=100,
		)

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Vehicle Recall", "docname": name},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=20,
	)

	return {
		"doc": doc.as_dict(),
		"affected_vehicles": affected_vehicles,
		"audit_trail": versions,
	}


def _get_current_employee():
	"""Get Employee linked to current session user."""
	return frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")


def _get_employee_vehicle_role(employee, vehicle_name):
	"""Determine if employee is custodian, driver, or other for a vehicle."""
	if not employee or not vehicle_name:
		return "other"
	vehicle = frappe.get_doc("Vehicle", vehicle_name)
	if vehicle.custom_custodian == employee:
		return "custodian"
	for d in (vehicle.custom_drivers or []):
		if d.employee == employee and d.status == "Active":
			return "driver"
	return "other"


@frappe.whitelist()
def search_vehicles(txt=None, limit_page_length=20):
	"""Search vehicles for issue form, bypassing user-permission company restrictions."""
	filters = {}
	or_filters = None
	if txt and txt.strip():
		or_filters = [
			["name", "like", f"%{txt}%"],
			["license_plate", "like", f"%{txt}%"],
			["make", "like", f"%{txt}%"],
			["model", "like", f"%{txt}%"],
		]

	return frappe.get_all(
		"Vehicle",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "license_plate", "make", "model"],
		order_by="modified desc",
		limit_page_length=int(limit_page_length),
		ignore_permissions=True,
	)


@frappe.whitelist()
def search_link_options(doctype, txt=None, limit_page_length=20):
	"""Search Customer or Company records, bypassing user-permission restrictions."""
	if doctype not in ("Customer", "Company"):
		frappe.throw("Only Customer and Company searches are allowed")

	filters = {}
	if txt and txt.strip():
		filters["name"] = ["like", f"%{txt}%"]

	return frappe.get_all(
		doctype,
		filters=filters,
		fields=["name"],
		order_by="modified desc",
		limit_page_length=int(limit_page_length),
		ignore_permissions=True,
	)


@frappe.whitelist()
def create_issue(subject, vehicle, severity=None, category=None, source=None, description=None, assigned_to=None):
	"""Create an issue with workflow state based on the creator's role."""
	employee = _get_current_employee()

	role = _get_employee_vehicle_role(employee, vehicle) if employee else "other"

	if role == "custodian":
		workflow_state = "Submitted"
	elif role == "driver":
		workflow_state = "Pending Custodian Approval"
	else:
		workflow_state = "Submitted"

	if employee:
		employee_name = frappe.db.get_value("Employee", employee, "employee_name") or employee
	else:
		employee_name = frappe.session.user

	issue = frappe.get_doc({
		"doctype": "Issue",
		"subject": subject,
		"description": description,
		"custom_vehicle": vehicle,
		"custom_severity": severity,
		"custom_category": category,
		"custom_source": source or "Driver Report",
		"custom_assigned_to": assigned_to,
		"custom_requested_by_employee": employee,
		"raised_by": frappe.session.user,
		"custom_workflow_state": workflow_state,
	})
	issue.insert(ignore_permissions=True)

	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "Issue",
		"reference_name": issue.name,
		"content": f"Issue created by {employee_name} as {role}",
	}).insert(ignore_permissions=True)

	frappe.db.commit()
	return {"name": issue.name, "workflow_state": workflow_state}


@frappe.whitelist()
def approve_issue(issue_name):
	"""Approve an issue pending custodian approval."""
	issue = frappe.get_doc("Issue", issue_name)

	if issue.get("custom_workflow_state") != "Pending Custodian Approval":
		frappe.throw("Issue is not pending custodian approval")

	employee = _get_current_employee()
	if not employee:
		frappe.throw("No Employee record found for current user")

	role = _get_employee_vehicle_role(employee, issue.get("custom_vehicle"))
	if role != "custodian":
		frappe.throw("Only the vehicle custodian can approve this issue")

	employee_name = frappe.db.get_value("Employee", employee, "employee_name") or employee

	issue.custom_workflow_state = "Submitted"
	issue.custom_approved_by = employee
	issue.custom_approved_on = now_datetime()
	issue.save(ignore_permissions=True)

	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "Issue",
		"reference_name": issue_name,
		"content": f"Issue approved by {employee_name}",
	}).insert(ignore_permissions=True)

	frappe.db.commit()
	return "ok"


@frappe.whitelist()
def reject_issue(issue_name, reason=None):
	"""Reject an issue pending custodian approval."""
	issue = frappe.get_doc("Issue", issue_name)

	if issue.get("custom_workflow_state") != "Pending Custodian Approval":
		frappe.throw("Issue is not pending custodian approval")

	employee = _get_current_employee()
	if not employee:
		frappe.throw("No Employee record found for current user")

	employee_name = frappe.db.get_value("Employee", employee, "employee_name") or employee

	issue.custom_workflow_state = "Rejected"
	issue.custom_rejected_by = employee
	issue.custom_rejected_on = now_datetime()
	issue.custom_rejection_reason = reason
	issue.save(ignore_permissions=True)

	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "Issue",
		"reference_name": issue_name,
		"content": f"Issue rejected by {employee_name}. Reason: {reason}",
	}).insert(ignore_permissions=True)

	frappe.db.commit()
	return "ok"
