import frappe
from frappe.utils import getdate, nowdate, add_days, flt, now_datetime


STANDARD_REPORTS = [
	{"id": "fleet_health_score", "title": "Fleet Health Score", "category": "Fleet Overview", "report_type": "KPI", "description": "Composite fleet health score", "module": "Vehicles"},
	{"id": "age_distribution", "title": "Age Distribution", "category": "Fleet Overview", "report_type": "Chart", "description": "Vehicle fleet age distribution", "module": "Vehicles"},
	{"id": "utilization_overview", "title": "Utilization Overview", "category": "Fleet Overview", "report_type": "Chart", "description": "Fleet utilization rates", "module": "Vehicles"},
	{"id": "downtime_summary", "title": "Downtime Summary", "category": "Fleet Overview", "report_type": "Table", "description": "Vehicle downtime analysis", "module": "Vehicles"},
	{"id": "mileage_by_vehicle", "title": "Mileage by Vehicle", "category": "Utilization & Meter", "report_type": "Table", "description": "Mileage readings by vehicle", "module": "Vehicles"},
	{"id": "low_use_vehicles", "title": "Low-Use Vehicles", "category": "Utilization & Meter", "report_type": "Table", "description": "Vehicles with minimal activity", "module": "Vehicles"},
	{"id": "fuel_vs_mileage", "title": "Fuel vs Mileage Efficiency", "category": "Utilization & Meter", "report_type": "Chart", "description": "Fuel consumption vs distance", "module": "Vehicles"},
	{"id": "wo_volume_trend", "title": "Work Order Volume Trend", "category": "Work Orders & Repairs", "report_type": "Chart", "description": "Work order creation trends", "module": "Repair Orders"},
	{"id": "wo_avg_resolution", "title": "Average Resolution Time", "category": "Work Orders & Repairs", "report_type": "KPI", "description": "Average time to complete WOs", "module": "Repair Orders"},
	{"id": "wo_backlog_status", "title": "Backlog by Status", "category": "Work Orders & Repairs", "report_type": "Chart", "description": "WO backlog by status", "module": "Repair Orders"},
	{"id": "wo_cost_variance", "title": "Cost vs Estimate Variance", "category": "Work Orders & Repairs", "report_type": "Table", "description": "Actual vs estimated cost", "module": "Repair Orders"},
	{"id": "wo_rework_rate", "title": "Repeat Repairs / Rework", "category": "Work Orders & Repairs", "report_type": "KPI", "description": "Rate of repeat repairs", "module": "Repair Orders"},
	{"id": "low_stock_items", "title": "Low Stock / Out of Stock", "category": "Parts & Inventory", "report_type": "Table", "description": "Items below reorder level", "module": "Parts"},
	{"id": "fast_moving_items", "title": "Fast-Moving Items", "category": "Parts & Inventory", "report_type": "Table", "description": "Most consumed parts", "module": "Parts"},
	{"id": "wo_consumption", "title": "Work Order Consumption", "category": "Parts & Inventory", "report_type": "Table", "description": "Parts consumed by WOs", "module": "Parts"},
	{"id": "inspection_pass_fail", "title": "Pass/Fail Trends", "category": "Inspections", "report_type": "Chart", "description": "Inspection pass/fail rates", "module": "Inspections"},
	{"id": "overdue_schedules", "title": "Overdue Schedules", "category": "Inspections", "report_type": "Table", "description": "Overdue inspection schedules", "module": "Inspections"},
	{"id": "failure_hotspots", "title": "Failure Hotspots", "category": "Inspections", "report_type": "Chart", "description": "Top failed components", "module": "Inspections"},
	{"id": "inspector_productivity", "title": "Inspector Productivity", "category": "Inspections", "report_type": "Table", "description": "Inspections per inspector", "module": "Inspections"},
	{"id": "issues_new_vs_resolved", "title": "New vs Resolved Trend", "category": "Issues & Faults", "report_type": "Chart", "description": "Issue creation vs resolution", "module": "Issues"},
	{"id": "issues_mttr", "title": "Mean Time to Resolve", "category": "Issues & Faults", "report_type": "KPI", "description": "Avg time to resolution", "module": "Issues"},
	{"id": "top_fault_codes", "title": "Top Fault Codes", "category": "Issues & Faults", "report_type": "Table", "description": "Most common fault codes", "module": "Issues"},
	{"id": "high_severity_open", "title": "High Severity Open Issues", "category": "Issues & Faults", "report_type": "Table", "description": "Open high/critical issues", "module": "Issues"},
	{"id": "expenses_by_category", "title": "Expenses by Category", "category": "Financials", "report_type": "Chart", "description": "Expense breakdown", "module": "Expenses"},
	{"id": "cost_per_vehicle", "title": "Cost per Vehicle", "category": "Financials", "report_type": "Table", "description": "Costs per vehicle", "module": "Expenses"},
	{"id": "cost_per_km", "title": "Cost per KM", "category": "Financials", "report_type": "Table", "description": "Operating cost per km", "module": "Expenses"},
	{"id": "invoice_aging", "title": "Invoice Aging", "category": "Financials", "report_type": "Table", "description": "Outstanding invoice aging", "module": "Invoices"},
	{"id": "top_customers_revenue", "title": "Top Customers by Revenue", "category": "Customers", "report_type": "Table", "description": "Top revenue customers", "module": "Customers"},
	{"id": "customer_outstanding", "title": "Outstanding Balance", "category": "Customers", "report_type": "Table", "description": "Customer outstanding balances", "module": "Customers"},
	{"id": "employee_wo_completed", "title": "Work Orders Completed", "category": "Employees", "report_type": "Table", "description": "WOs completed per employee", "module": "Employees"},
	{"id": "employee_avg_completion", "title": "Avg Completion Time", "category": "Employees", "report_type": "KPI", "description": "Avg WO completion time", "module": "Employees"},
	{"id": "employee_workload", "title": "Workload Distribution", "category": "Employees", "report_type": "Chart", "description": "Current workload spread", "module": "Employees"},
]

REPORT_CATEGORIES = [
	"Fleet Overview", "Utilization & Meter", "Work Orders & Repairs",
	"Parts & Inventory", "Inspections", "Issues & Faults",
	"Financials", "Customers", "Employees",
]


@frappe.whitelist()
def get_reports_home():
	"""Get Reports Home KPIs and insights."""
	today = getdate(nowdate())
	thirty_days_ago = add_days(today, -30)

	open_wo = frappe.db.count("Repair Order", filters={
		"status": ["in", ["Draft", "Scheduled", "In Progress", "Awaiting Parts", "On Hold"]],
		"docstatus": ["!=", 2],
	})

	overdue_inspections = 0
	try:
		overdue_inspections = frappe.db.count("Inspection Schedule", filters={
			"next_due": ["<", today], "status": ["!=", "Inactive"],
		})
	except Exception:
		pass

	total_expenses_30d = 0
	try:
		exps = frappe.get_all("Vehicle Expense",
			filters={"expense_date": [">=", thirty_days_ago]}, fields=["amount"])
		total_expenses_30d = sum(flt(e.amount) for e in exps)
	except Exception:
		pass

	outstanding_invoices = 0
	try:
		si = frappe.get_all("Sales Invoice",
			filters={"docstatus": 1, "outstanding_amount": [">", 0]},
			fields=["outstanding_amount"])
		outstanding_invoices = round(sum(flt(s.outstanding_amount) for s in si), 2)
	except Exception:
		pass

	fleet_utilization = 0
	try:
		total_v = frappe.db.count("Vehicle")
		if total_v:
			active = frappe.db.sql("""
				SELECT COUNT(DISTINCT vehicle) as cnt FROM `tabRepair Order`
				WHERE creation >= %s AND docstatus != 2
			""", thirty_days_ago, as_dict=True)
			fleet_utilization = round((active[0].cnt / total_v) * 100, 1) if active else 0
	except Exception:
		pass

	kpis = {
		"open_work_orders": open_wo,
		"overdue_inspections": overdue_inspections,
		"total_expenses_30d": round(total_expenses_30d, 2),
		"outstanding_invoices": outstanding_invoices,
		"fleet_utilization": fleet_utilization,
	}

	top_cost_vehicles = []
	try:
		top_cost_vehicles = frappe.db.sql("""
			SELECT vehicle, SUM(amount) as total_cost FROM `tabVehicle Expense`
			WHERE expense_date >= %s AND vehicle IS NOT NULL AND vehicle != ''
			GROUP BY vehicle ORDER BY total_cost DESC LIMIT 5
		""", thirty_days_ago, as_dict=True)
	except Exception:
		pass

	recurring_failures = []
	try:
		recurring_failures = frappe.db.sql("""
			SELECT item_name, COUNT(*) as failure_count
			FROM `tabInspection Item Failure`
			WHERE item_name IS NOT NULL AND item_name != ''
			GROUP BY item_name ORDER BY failure_count DESC LIMIT 5
		""", as_dict=True)
	except Exception:
		pass

	worst_downtime = []
	try:
		worst_downtime = frappe.db.sql("""
			SELECT vehicle, COUNT(*) as wo_count,
				SUM(DATEDIFF(IFNULL(modified, NOW()), creation)) as total_days
			FROM `tabRepair Order`
			WHERE status IN ('In Progress', 'Awaiting Parts', 'On Hold')
				AND vehicle IS NOT NULL AND vehicle != '' AND docstatus != 2
			GROUP BY vehicle ORDER BY total_days DESC LIMIT 5
		""", as_dict=True)
	except Exception:
		pass

	overdue_reminders = []
	try:
		overdue_reminders = frappe.get_all("Inspection Schedule",
			filters={"next_due": ["<", today], "status": ["!=", "Inactive"]},
			fields=["name", "title", "vehicle", "next_due"],
			order_by="next_due asc", limit=5)
	except Exception:
		pass

	insights = {
		"top_cost_vehicles": top_cost_vehicles,
		"recurring_failures": recurring_failures,
		"worst_downtime": worst_downtime,
		"overdue_reminders": overdue_reminders,
	}

	return {"kpis": kpis, "insights": insights, "categories": REPORT_CATEGORIES}


@frappe.whitelist()
def get_reports_library(search=None, category=None, report_type=None,
                        limit_start=0, limit_page_length=50):
	"""Get catalog of available reports."""
	reports = list(STANDARD_REPORTS)
	if search:
		sl = search.lower()
		reports = [r for r in reports if sl in r["title"].lower() or sl in r["description"].lower()]
	if category:
		reports = [r for r in reports if r["category"] == category]
	if report_type:
		reports = [r for r in reports if r["report_type"] == report_type]

	total = len(reports)
	paginated = reports[int(limit_start):int(limit_start) + int(limit_page_length)]
	return {"reports": paginated, "total": total, "categories": REPORT_CATEGORIES}


@frappe.whitelist()
def get_report_data(report_id, date_from=None, date_to=None, filters=None,
                    limit_start=0, limit_page_length=50):
	"""Execute a specific report and return data."""
	import json as _json
	if filters and isinstance(filters, str):
		filters = _json.loads(filters)

	today = getdate(nowdate())
	if not date_from:
		date_from = str(add_days(today, -30))
	if not date_to:
		date_to = str(today)

	d_from, d_to = getdate(date_from), getdate(date_to)
	report_def = next((r for r in STANDARD_REPORTS if r["id"] == report_id), None)
	if not report_def:
		frappe.throw(f"Report '{report_id}' not found")

	handler = REPORT_HANDLERS.get(report_id)
	if handler:
		result = handler(d_from, d_to, filters, int(limit_start), int(limit_page_length))
	else:
		result = {"chart_data": None, "table_data": [], "kpis": {}, "total": 0}

	result["report"] = report_def
	result["date_from"] = str(d_from)
	result["date_to"] = str(d_to)
	result["last_refreshed"] = str(now_datetime())
	return result


@frappe.whitelist()
def get_saved_reports(search=None, limit_start=0, limit_page_length=20):
	"""Get user's saved report variants."""
	filters = {"owner": frappe.session.user}
	if search:
		filters["title"] = ["like", f"%{search}%"]

	reports = frappe.get_all("Workshop Saved Report",
		filters=filters,
		fields=["name", "title", "report_id", "report_title", "category", "report_type",
				"filters_json", "date_from", "date_to", "shared_with", "last_run",
				"owner", "creation", "modified"],
		order_by="modified desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length))

	# Also include reports shared with user
	shared = frappe.get_all("Workshop Saved Report",
		filters={"shared_with": ["like", f"%{frappe.session.user}%"],
				 "owner": ["!=", frappe.session.user]},
		fields=["name", "title", "report_id", "report_title", "category", "report_type",
				"filters_json", "date_from", "date_to", "shared_with", "last_run",
				"owner", "creation", "modified"],
		order_by="modified desc", limit_page_length=50)

	seen = {r.name for r in reports}
	for s in shared:
		if s.name not in seen:
			reports.append(s)

	total = frappe.db.count("Workshop Saved Report", {"owner": frappe.session.user})
	return {"reports": reports, "total": total}


@frappe.whitelist()
def save_report(title, report_id, filters_json=None, date_from=None, date_to=None,
				description=None, shared_with=None):
	"""Save a report variant."""
	report_def = next((r for r in STANDARD_REPORTS if r["id"] == report_id), None)
	if not report_def:
		frappe.throw(f"Report '{report_id}' not found")

	doc = frappe.get_doc({
		"doctype": "Workshop Saved Report",
		"title": title,
		"report_id": report_id,
		"report_title": report_def["title"],
		"category": report_def["category"],
		"report_type": report_def["report_type"],
		"filters_json": filters_json or "{}",
		"date_from": date_from,
		"date_to": date_to,
		"description": description,
		"shared_with": shared_with,
	})
	doc.insert()
	return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
def delete_saved_report(name):
	"""Delete a saved report (owner or admin only)."""
	doc = frappe.get_doc("Workshop Saved Report", name)
	if doc.owner != frappe.session.user and "System Manager" not in frappe.get_roles():
		frappe.throw("Only the owner or an admin can delete this report")
	doc.delete()
	return {"success": True}


@frappe.whitelist()
def duplicate_saved_report(name):
	"""Duplicate a saved report."""
	doc = frappe.get_doc("Workshop Saved Report", name)
	new_doc = frappe.get_doc({
		"doctype": "Workshop Saved Report",
		"title": f"{doc.title} (Copy)",
		"report_id": doc.report_id,
		"report_title": doc.report_title,
		"category": doc.category,
		"report_type": doc.report_type,
		"filters_json": doc.filters_json,
		"date_from": doc.date_from,
		"date_to": doc.date_to,
		"description": doc.description,
	})
	new_doc.insert()
	return {"name": new_doc.name, "title": new_doc.title}


@frappe.whitelist()
def get_scheduled_reports(search=None, limit_start=0, limit_page_length=20):
	"""Get scheduled report configurations."""
	filters = {}
	if search:
		filters["title"] = ["like", f"%{search}%"]

	reports = frappe.get_all("Workshop Report Schedule",
		filters=filters,
		fields=["name", "title", "report_id", "report_title", "frequency",
				"delivery_method", "export_format", "recipients", "enabled",
				"last_sent", "next_run", "last_status", "delivery_time",
				"owner", "creation", "modified"],
		order_by="modified desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length))

	total = frappe.db.count("Workshop Report Schedule", filters)
	return {"reports": reports, "total": total}


@frappe.whitelist()
def create_report_schedule(title, report_id, frequency, delivery_method="Email",
						   export_format="CSV", recipients=None, filters_json=None,
						   date_from=None, date_to=None, delivery_time=None):
	"""Create a new report schedule."""
	report_def = next((r for r in STANDARD_REPORTS if r["id"] == report_id), None)
	if not report_def:
		frappe.throw(f"Report '{report_id}' not found")

	doc = frappe.get_doc({
		"doctype": "Workshop Report Schedule",
		"title": title,
		"report_id": report_id,
		"report_title": report_def["title"],
		"frequency": frequency,
		"delivery_method": delivery_method,
		"export_format": export_format,
		"recipients": recipients,
		"filters_json": filters_json or "{}",
		"date_from": date_from,
		"date_to": date_to,
		"delivery_time": delivery_time,
		"enabled": 1,
	})
	doc.insert()
	return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
def toggle_report_schedule(name, enabled):
	"""Enable or disable a report schedule."""
	doc = frappe.get_doc("Workshop Report Schedule", name)
	doc.enabled = int(enabled)
	if doc.enabled:
		doc.compute_next_run()
	doc.save()
	return {"name": doc.name, "enabled": doc.enabled}


@frappe.whitelist()
def delete_report_schedule(name):
	"""Delete a report schedule."""
	frappe.delete_doc("Workshop Report Schedule", name)
	return {"success": True}


@frappe.whitelist()
def run_report_now(name):
	"""Execute a scheduled report immediately."""
	import csv
	import io

	doc = frappe.get_doc("Workshop Report Schedule", name)
	report_def = next((r for r in STANDARD_REPORTS if r["id"] == doc.report_id), None)
	if not report_def:
		frappe.throw(f"Report '{doc.report_id}' not found")

	handler = REPORT_HANDLERS.get(doc.report_id)
	if not handler:
		doc.last_status = "Failed"
		doc.last_sent = now_datetime()
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"success": False, "message": "No handler for this report"}

	today = getdate(nowdate())
	d_from = getdate(doc.date_from) if doc.date_from else add_days(today, -30)
	d_to = getdate(doc.date_to) if doc.date_to else today

	try:
		result = handler(d_from, d_to, None, 0, 500)
	except Exception as e:
		doc.last_status = "Failed"
		doc.last_sent = now_datetime()
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.log_error(f"Report execution failed: {e}")
		return {"success": False, "message": str(e)}

	table_data = result.get("table_data", [])
	kpis = result.get("kpis", {})

	# Generate CSV
	csv_content = ""
	if table_data:
		output = io.StringIO()
		if isinstance(table_data[0], dict):
			cols = list(table_data[0].keys())
		else:
			cols = []
		if cols:
			writer = csv.DictWriter(output, fieldnames=cols)
			writer.writeheader()
			for row in table_data:
				writer.writerow(row if isinstance(row, dict) else {})
			csv_content = output.getvalue()

	# Delivery
	try:
		if doc.delivery_method == "Email" and doc.recipients:
			recipients = [r.strip() for r in doc.recipients.split(",") if r.strip()]
			if recipients and csv_content:
				frappe.sendmail(
					recipients=recipients,
					subject=f"Scheduled Report: {doc.title}",
					message=f"<p>Please find attached the scheduled report <strong>{report_def['title']}</strong>.</p>"
						f"<p>Date range: {d_from} to {d_to}</p>"
						f"<p>KPIs: {', '.join(f'{k}: {v}' for k, v in kpis.items()) if kpis else 'N/A'}</p>",
					attachments=[{
						"fname": f"{doc.report_id}_{d_from}_{d_to}.csv",
						"fcontent": csv_content.encode("utf-8"),
					}],
				)
		elif doc.delivery_method == "In-App":
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Report Ready: {doc.title}",
				"for_user": doc.owner,
				"type": "Alert",
				"email_content": f"Report '{report_def['title']}' has been generated. Date range: {d_from} to {d_to}.",
			}).insert(ignore_permissions=True)

		doc.last_status = "Sent"
	except Exception as e:
		frappe.log_error(f"Report delivery failed: {e}")
		doc.last_status = "Failed"

	doc.last_sent = now_datetime()
	doc.compute_next_run()
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"success": True, "status": doc.last_status, "last_sent": str(doc.last_sent)}


@frappe.whitelist()
def get_pinned_reports():
	"""Get user's pinned/favorite report IDs."""
	pinned = frappe.db.get_default("workshop_pinned_reports", frappe.session.user) or "[]"
	import json as _json
	try:
		report_ids = _json.loads(pinned)
	except Exception:
		report_ids = []
	# Return report definitions for pinned IDs
	reports = [r for r in STANDARD_REPORTS if r["id"] in report_ids]
	return {"reports": reports, "pinned_ids": report_ids}


@frappe.whitelist()
def toggle_pin_report(report_id):
	"""Pin or unpin a report for the current user."""
	import json as _json
	pinned = frappe.db.get_default("workshop_pinned_reports", frappe.session.user) or "[]"
	try:
		report_ids = _json.loads(pinned)
	except Exception:
		report_ids = []
	if report_id in report_ids:
		report_ids.remove(report_id)
		is_pinned = False
	else:
		report_ids.append(report_id)
		is_pinned = True
	frappe.db.set_default("workshop_pinned_reports", _json.dumps(report_ids), frappe.session.user)
	return {"is_pinned": is_pinned, "pinned_ids": report_ids}


# ── Report handlers ─────────────────────────────────────────────────────────

def _rpt_wo_volume_trend(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT DATE_FORMAT(creation, '%%Y-%%m') as month, COUNT(*) as count
		FROM `tabRepair Order` WHERE creation BETWEEN %s AND %s AND docstatus != 2
		GROUP BY month ORDER BY month
	""", (d_from, d_to), as_dict=True)
	return {"chart_data": {"labels": [d.month for d in data], "values": [d.count for d in data]},
			"table_data": data, "kpis": {"total_orders": sum(d.count for d in data)}, "total": len(data)}


def _rpt_wo_backlog_status(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT status, COUNT(*) as count FROM `tabRepair Order`
		WHERE docstatus != 2 GROUP BY status ORDER BY count DESC
	""", as_dict=True)
	return {"chart_data": {"labels": [d.status for d in data], "values": [d.count for d in data]},
			"table_data": data,
			"kpis": {"total_open": sum(d.count for d in data if d.status not in ("Delivered", "Closed", "Cancelled"))},
			"total": len(data)}


def _rpt_wo_avg_resolution(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT AVG(DATEDIFF(modified, creation)) as avg_days, COUNT(*) as total
		FROM `tabRepair Order` WHERE status IN ('Delivered','Closed')
		AND creation BETWEEN %s AND %s AND docstatus != 2
	""", (d_from, d_to), as_dict=True)
	return {"chart_data": None, "table_data": [],
			"kpis": {"avg_resolution_days": round(flt(data[0].avg_days), 1) if data else 0,
					 "total_completed": data[0].total if data else 0}, "total": 0}


def _rpt_wo_cost_variance(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT name, vehicle, total_job_cost, status, creation FROM `tabRepair Order`
		WHERE creation BETWEEN %s AND %s AND docstatus != 2 AND total_job_cost > 0
		ORDER BY total_job_cost DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": None, "table_data": data,
			"kpis": {"avg_cost": round(sum(flt(d.total_job_cost) for d in data) / len(data), 2) if data else 0},
			"total": len(data)}


def _rpt_wo_rework_rate(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT vehicle, COUNT(*) as wo_count FROM `tabRepair Order`
		WHERE creation BETWEEN %s AND %s AND docstatus != 2
		AND vehicle IS NOT NULL AND vehicle != ''
		GROUP BY vehicle HAVING wo_count > 1 ORDER BY wo_count DESC
	""", (d_from, d_to), as_dict=True)
	total_wo = frappe.db.count("Repair Order", {"creation": ["between", [d_from, d_to]], "docstatus": ["!=", 2]})
	rework = sum(d.wo_count - 1 for d in data)
	return {"chart_data": None, "table_data": data[:length],
			"kpis": {"rework_rate": round((rework / total_wo) * 100, 1) if total_wo else 0,
					 "repeat_vehicles": len(data)}, "total": len(data)}


def _rpt_fleet_health(d_from, d_to, filters, start, length):
	total_v = frappe.db.count("Vehicle") or 1
	insp = frappe.get_all("Vehicle Inspection",
		filters={"inspection_date": ["between", [d_from, d_to]]}, fields=["result"])
	pc = sum(1 for i in insp if i.result == "Pass")
	insp_score = round((pc / len(insp)) * 100, 1) if insp else 100
	open_issues = frappe.db.count("Issue", {"status": "Open"})
	issue_score = max(0, round(100 - (open_issues / total_v) * 20, 1))
	open_faults = 0
	try:
		open_faults = frappe.db.count("Vehicle Fault", {"status": ["in", ["Open", "Investigating"]]})
	except Exception:
		pass
	fault_score = max(0, round(100 - (open_faults / total_v) * 25, 1))
	composite = round((insp_score + issue_score + fault_score) / 3, 1)
	return {"chart_data": None, "table_data": [],
			"kpis": {"health_score": composite, "inspection_score": insp_score,
					 "issue_score": issue_score, "fault_score": fault_score}, "total": 0}


def _rpt_age_distribution(d_from, d_to, filters, start, length):
	import datetime
	cy = datetime.date.today().year
	data = frappe.db.sql("""
		SELECT CASE
			WHEN (%s - CAST(year AS UNSIGNED)) <= 2 THEN '0-2 years'
			WHEN (%s - CAST(year AS UNSIGNED)) <= 5 THEN '3-5 years'
			WHEN (%s - CAST(year AS UNSIGNED)) <= 10 THEN '6-10 years'
			ELSE '10+ years' END as age_group, COUNT(*) as count
		FROM `tabVehicle` WHERE year IS NOT NULL AND year != '' AND year != '0'
		GROUP BY age_group ORDER BY age_group
	""", (cy, cy, cy), as_dict=True)
	return {"chart_data": {"labels": [d.age_group for d in data], "values": [d.count for d in data]},
			"table_data": data, "kpis": {"total_vehicles": sum(d.count for d in data)}, "total": len(data)}


def _rpt_utilization(d_from, d_to, filters, start, length):
	total_v = frappe.db.count("Vehicle") or 1
	data = frappe.db.sql("""
		SELECT vehicle, COUNT(*) as wo_count FROM `tabRepair Order`
		WHERE creation BETWEEN %s AND %s AND docstatus != 2
		AND vehicle IS NOT NULL AND vehicle != ''
		GROUP BY vehicle ORDER BY wo_count DESC
	""", (d_from, d_to), as_dict=True)
	return {"chart_data": {"labels": [d.vehicle for d in data[:10]], "values": [d.wo_count for d in data[:10]]},
			"table_data": data, "kpis": {"utilization_pct": round((len(data) / total_v) * 100, 1),
			"active_vehicles": len(data), "total_vehicles": total_v}, "total": len(data)}


def _rpt_downtime(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT vehicle, status, COUNT(*) as count,
			SUM(DATEDIFF(IFNULL(modified, NOW()), creation)) as total_days
		FROM `tabRepair Order`
		WHERE status IN ('In Progress','Awaiting Parts','On Hold')
		AND vehicle IS NOT NULL AND vehicle != '' AND docstatus != 2
		GROUP BY vehicle, status ORDER BY total_days DESC LIMIT %s, %s
	""", (start, length), as_dict=True)
	return {"chart_data": None, "table_data": data,
			"kpis": {"vehicles_in_downtime": len(set(d.vehicle for d in data))}, "total": len(data)}


def _rpt_mileage(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT license_plate as vehicle, last_odometer,
			IFNULL(odometer,0) - IFNULL(last_odometer,0) as distance
		FROM `tabVehicle Log` WHERE date BETWEEN %s AND %s
		AND license_plate IS NOT NULL AND license_plate != ''
		ORDER BY distance DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": None, "table_data": data,
			"kpis": {"total_distance": sum(flt(d.distance) for d in data)}, "total": len(data)}


def _rpt_low_use(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT v.name as vehicle, v.make, v.model,
			IFNULL((SELECT SUM(IFNULL(vl.odometer,0)-IFNULL(vl.last_odometer,0))
				FROM `tabVehicle Log` vl WHERE vl.license_plate=v.name
				AND vl.date BETWEEN %s AND %s), 0) as total_mileage
		FROM `tabVehicle` v ORDER BY total_mileage ASC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": None, "table_data": data, "kpis": {}, "total": len(data)}


def _rpt_fuel_mileage(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT license_plate as vehicle, SUM(fuel_qty) as total_fuel,
			SUM(IFNULL(odometer,0)-IFNULL(last_odometer,0)) as total_distance
		FROM `tabVehicle Log` WHERE date BETWEEN %s AND %s
		AND license_plate IS NOT NULL AND license_plate != '' AND fuel_qty > 0
		GROUP BY license_plate ORDER BY total_distance DESC
	""", (d_from, d_to), as_dict=True)
	for d in data:
		d["efficiency"] = round(flt(d.total_distance) / flt(d.total_fuel), 2) if flt(d.total_fuel) else 0
	return {"chart_data": {"labels": [d.vehicle for d in data[:10]],
			"values": [d.efficiency for d in data[:10]]},
			"table_data": data, "kpis": {}, "total": len(data)}


def _rpt_low_stock(d_from, d_to, filters, start, length):
	from frappe.query_builder.functions import Sum
	items = frappe.get_all("Item", filters={"is_stock_item": 1},
		fields=["name", "item_name", "item_group", "stock_uom"])
	# Get reorder levels from Item Reorder child table
	reorder_map = {}
	try:
		reorders = frappe.get_all("Item Reorder",
			fields=["parent", "warehouse_reorder_level"],
			filters={"parenttype": "Item"})
		for r in reorders:
			reorder_map[r.parent] = max(reorder_map.get(r.parent, 0), flt(r.warehouse_reorder_level))
	except Exception:
		pass
	Bin = frappe.qb.DocType("Bin")
	sd = frappe.qb.from_(Bin).select(Bin.item_code, Sum(Bin.actual_qty).as_("total_qty")).groupby(Bin.item_code).run(as_dict=True)
	sm = {s.item_code: flt(s.total_qty) for s in sd}
	result = []
	for it in items:
		qty = sm.get(it.name, 0)
		rl = reorder_map.get(it.name, 0)
		if qty <= 0:
			st = "Out of Stock"
		elif rl and qty <= rl:
			st = "Low"
		else:
			continue
		result.append({"item_code": it.name, "item_name": it.item_name, "item_group": it.item_group,
					   "current_qty": qty, "reorder_level": rl, "stock_status": st})
	result.sort(key=lambda x: x["current_qty"])
	return {"chart_data": None, "table_data": result[start:start+length],
			"kpis": {"low_count": sum(1 for r in result if r["stock_status"]=="Low"),
					 "out_count": sum(1 for r in result if r["stock_status"]=="Out of Stock")},
			"total": len(result)}


def _rpt_fast_moving(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT rpp.item_code, rpp.item_name, SUM(rpp.qty_planned) as total_qty, COUNT(DISTINCT rpp.parent) as wo_count
		FROM `tabRepair Parts Plan` rpp
		INNER JOIN `tabRepair Order` ro ON ro.name=rpp.parent
		WHERE ro.creation BETWEEN %s AND %s AND ro.docstatus != 2
		GROUP BY rpp.item_code, rpp.item_name ORDER BY total_qty DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": {"labels": [d.item_name or d.item_code for d in data[:10]], "values": [d.total_qty for d in data[:10]]},
			"table_data": data, "kpis": {}, "total": len(data)}


def _rpt_wo_consumption(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT rpp.parent as repair_order, rpp.item_code, rpp.item_name, rpp.qty_planned,
			ro.vehicle, ro.status
		FROM `tabRepair Parts Plan` rpp INNER JOIN `tabRepair Order` ro ON ro.name=rpp.parent
		WHERE ro.creation BETWEEN %s AND %s AND ro.docstatus != 2
		ORDER BY ro.creation DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": None, "table_data": data,
			"kpis": {"total_parts_used": sum(flt(d.qty_planned) for d in data)}, "total": len(data)}


def _rpt_insp_pass_fail(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT DATE_FORMAT(inspection_date, '%%Y-%%m') as month,
			SUM(CASE WHEN result='Pass' THEN 1 ELSE 0 END) as pass_count,
			SUM(CASE WHEN result='Fail' THEN 1 ELSE 0 END) as fail_count,
			SUM(CASE WHEN result='Conditional' THEN 1 ELSE 0 END) as conditional_count,
			COUNT(*) as total
		FROM `tabVehicle Inspection` WHERE inspection_date BETWEEN %s AND %s
		GROUP BY month ORDER BY month
	""", (d_from, d_to), as_dict=True)
	t = sum(d.total for d in data) if data else 0
	return {"chart_data": {"labels": [d.month for d in data],
			"pass": [d.pass_count for d in data], "fail": [d.fail_count for d in data]},
			"table_data": data,
			"kpis": {"total_inspections": t,
					 "pass_rate": round(sum(d.pass_count for d in data) / t * 100, 1) if t else 0},
			"total": len(data)}


def _rpt_overdue_sched(d_from, d_to, filters, start, length):
	today = getdate(nowdate())
	data = frappe.get_all("Inspection Schedule",
		filters={"next_due": ["<", today], "status": ["!=", "Inactive"]},
		fields=["name", "title", "vehicle", "frequency", "next_due", "status"],
		order_by="next_due asc", limit_start=start, limit_page_length=length)
	total = frappe.db.count("Inspection Schedule", {"next_due": ["<", today], "status": ["!=", "Inactive"]})
	return {"chart_data": None, "table_data": data, "kpis": {"overdue_count": total}, "total": total}


def _rpt_failure_hotspots(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT item_name, COUNT(*) as failure_count,
			SUM(CASE WHEN is_recurring=1 THEN 1 ELSE 0 END) as recurring_count
		FROM `tabInspection Item Failure` WHERE creation BETWEEN %s AND %s
		AND item_name IS NOT NULL AND item_name != ''
		GROUP BY item_name ORDER BY failure_count DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": {"labels": [d.item_name for d in data], "values": [d.failure_count for d in data]},
			"table_data": data, "kpis": {"total_failures": sum(d.failure_count for d in data)}, "total": len(data)}


def _rpt_inspector_prod(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT inspector, COUNT(*) as inspection_count, AVG(score) as avg_score
		FROM `tabVehicle Inspection` WHERE inspection_date BETWEEN %s AND %s
		AND inspector IS NOT NULL AND inspector != ''
		GROUP BY inspector ORDER BY inspection_count DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	for d in data:
		d["avg_score"] = round(flt(d.avg_score), 1)
	return {"chart_data": None, "table_data": data, "kpis": {}, "total": len(data)}


def _rpt_issues_trend(d_from, d_to, filters, start, length):
	new = frappe.db.sql("""
		SELECT DATE_FORMAT(creation, '%%Y-%%m') as month, COUNT(*) as count
		FROM `tabIssue` WHERE creation BETWEEN %s AND %s GROUP BY month ORDER BY month
	""", (d_from, d_to), as_dict=True)
	res = frappe.db.sql("""
		SELECT DATE_FORMAT(sla_resolution_date, '%%Y-%%m') as month, COUNT(*) as count
		FROM `tabIssue` WHERE sla_resolution_date BETWEEN %s AND %s GROUP BY month ORDER BY month
	""", (d_from, d_to), as_dict=True)
	months = sorted(set(d.month for d in new) | set(d.month for d in res))
	nm = {d.month: d.count for d in new}
	rm = {d.month: d.count for d in res}
	return {"chart_data": {"labels": months, "new": [nm.get(m, 0) for m in months],
			"resolved": [rm.get(m, 0) for m in months]},
			"table_data": [{"month": m, "new": nm.get(m, 0), "resolved": rm.get(m, 0)} for m in months],
			"kpis": {"total_new": sum(nm.values()), "total_resolved": sum(rm.values())},
			"total": len(months)}


def _rpt_issues_mttr(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT AVG(DATEDIFF(sla_resolution_date, creation)) as avg_days, COUNT(*) as count
		FROM `tabIssue` WHERE sla_resolution_date IS NOT NULL AND creation BETWEEN %s AND %s
	""", (d_from, d_to), as_dict=True)
	triage = frappe.db.sql("""
		SELECT AVG(TIMESTAMPDIFF(HOUR, creation, first_responded_on)) as avg_hours, COUNT(*) as count
		FROM `tabIssue` WHERE first_responded_on IS NOT NULL AND creation BETWEEN %s AND %s
	""", (d_from, d_to), as_dict=True)
	return {"chart_data": None, "table_data": [],
			"kpis": {"avg_resolution_days": round(flt(data[0].avg_days), 1) if data else 0,
					 "resolved_count": data[0].count if data else 0,
					 "avg_triage_hours": round(flt(triage[0].avg_hours), 1) if triage else 0},
			"total": 0}


def _rpt_top_faults(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT fault_code, component_system, COUNT(*) as count FROM `tabVehicle Fault`
		WHERE creation BETWEEN %s AND %s AND fault_code IS NOT NULL AND fault_code != ''
		GROUP BY fault_code, component_system ORDER BY count DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": None, "table_data": data, "kpis": {}, "total": len(data)}


def _rpt_high_severity(d_from, d_to, filters, start, length):
	data = frappe.get_all("Issue",
		filters={"status": "Open", "custom_severity": ["in", ["High", "Critical"]]},
		fields=["name", "subject", "custom_vehicle", "custom_severity", "custom_category", "creation", "owner"],
		order_by="creation asc", limit_start=start, limit_page_length=length)
	total = frappe.db.count("Issue", {"status": "Open", "custom_severity": ["in", ["High", "Critical"]]})
	return {"chart_data": None, "table_data": data, "kpis": {"count": total}, "total": total}


def _rpt_expenses_cat(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT category, SUM(amount) as total_amount, COUNT(*) as count
		FROM `tabVehicle Expense` WHERE expense_date BETWEEN %s AND %s
		GROUP BY category ORDER BY total_amount DESC
	""", (d_from, d_to), as_dict=True)
	return {"chart_data": {"labels": [d.category for d in data], "values": [flt(d.total_amount) for d in data]},
			"table_data": data, "kpis": {"total": sum(flt(d.total_amount) for d in data)}, "total": len(data)}


def _rpt_cost_vehicle(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT vehicle, SUM(amount) as total_cost, COUNT(*) as expense_count
		FROM `tabVehicle Expense` WHERE expense_date BETWEEN %s AND %s
		AND vehicle IS NOT NULL AND vehicle != ''
		GROUP BY vehicle ORDER BY total_cost DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": None, "table_data": data,
			"kpis": {"avg_cost": round(sum(flt(d.total_cost) for d in data)/len(data), 2) if data else 0},
			"total": len(data)}


def _rpt_cost_km(d_from, d_to, filters, start, length):
	exps = frappe.db.sql("""
		SELECT vehicle, SUM(amount) as total_cost FROM `tabVehicle Expense`
		WHERE expense_date BETWEEN %s AND %s AND vehicle IS NOT NULL AND vehicle != ''
		GROUP BY vehicle
	""", (d_from, d_to), as_dict=True)
	miles = frappe.db.sql("""
		SELECT license_plate as vehicle, SUM(IFNULL(odometer,0)-IFNULL(last_odometer,0)) as total_km
		FROM `tabVehicle Log` WHERE date BETWEEN %s AND %s
		AND license_plate IS NOT NULL AND license_plate != '' GROUP BY license_plate
	""", (d_from, d_to), as_dict=True)
	em = {e.vehicle: flt(e.total_cost) for e in exps}
	mm = {m.vehicle: flt(m.total_km) for m in miles}
	result = []
	for v in set(list(em.keys()) + list(mm.keys())):
		c, k = em.get(v, 0), mm.get(v, 0)
		result.append({"vehicle": v, "total_cost": c, "total_km": k, "cost_per_km": round(c/k, 2) if k > 0 else 0})
	result.sort(key=lambda x: x["cost_per_km"], reverse=True)
	return {"chart_data": None, "table_data": result[start:start+length], "kpis": {}, "total": len(result)}


def _rpt_invoice_aging(d_from, d_to, filters, start, length):
	today = getdate(nowdate())
	si = frappe.get_all("Sales Invoice", filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "customer", "grand_total", "outstanding_amount", "due_date", "posting_date"])
	pi = frappe.get_all("Purchase Invoice", filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "supplier", "grand_total", "outstanding_amount", "due_date", "posting_date"])
	result = []
	for inv in si:
		days = (today - getdate(inv.due_date)).days if inv.due_date else 0
		bucket = "Current" if days <= 0 else "1-30" if days <= 30 else "31-60" if days <= 60 else "61-90" if days <= 90 else "90+"
		result.append({"name": inv.name, "type": "A/R", "party": inv.customer,
					   "amount": flt(inv.outstanding_amount), "days_overdue": max(0, days), "bucket": bucket})
	for inv in pi:
		days = (today - getdate(inv.due_date)).days if inv.due_date else 0
		bucket = "Current" if days <= 0 else "1-30" if days <= 30 else "31-60" if days <= 60 else "61-90" if days <= 90 else "90+"
		result.append({"name": inv.name, "type": "A/P", "party": inv.supplier,
					   "amount": flt(inv.outstanding_amount), "days_overdue": max(0, days), "bucket": bucket})
	result.sort(key=lambda x: x["days_overdue"], reverse=True)
	return {"chart_data": None, "table_data": result[start:start+length],
			"kpis": {"total_ar": sum(r["amount"] for r in result if r["type"]=="A/R"),
					 "total_ap": sum(r["amount"] for r in result if r["type"]=="A/P")}, "total": len(result)}


def _rpt_top_cust_rev(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT customer, SUM(grand_total) as total_revenue, COUNT(*) as invoice_count
		FROM `tabSales Invoice` WHERE posting_date BETWEEN %s AND %s AND docstatus=1
		GROUP BY customer ORDER BY total_revenue DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": None, "table_data": data,
			"kpis": {"total_revenue": sum(flt(d.total_revenue) for d in data)}, "total": len(data)}


def _rpt_cust_outstanding(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT customer, SUM(outstanding_amount) as outstanding, COUNT(*) as invoice_count
		FROM `tabSales Invoice` WHERE docstatus=1 AND outstanding_amount > 0
		GROUP BY customer ORDER BY outstanding DESC LIMIT %s, %s
	""", (start, length), as_dict=True)
	return {"chart_data": None, "table_data": data,
			"kpis": {"total_outstanding": sum(flt(d.outstanding) for d in data)}, "total": len(data)}


def _rpt_emp_wo(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT owner as employee, COUNT(*) as completed_count,
			SUM(total_job_cost) as total_value
		FROM `tabRepair Order` WHERE status IN ('Delivered','Closed')
		AND creation BETWEEN %s AND %s AND docstatus != 2
		AND owner IS NOT NULL AND owner != ''
		GROUP BY owner ORDER BY completed_count DESC LIMIT %s, %s
	""", (d_from, d_to, start, length), as_dict=True)
	return {"chart_data": None, "table_data": data,
			"kpis": {"total_completed": sum(d.completed_count for d in data)}, "total": len(data)}


def _rpt_emp_avg(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT owner as employee, AVG(DATEDIFF(modified, creation)) as avg_days, COUNT(*) as count
		FROM `tabRepair Order` WHERE status IN ('Delivered','Closed')
		AND creation BETWEEN %s AND %s AND docstatus != 2
		AND owner IS NOT NULL AND owner != ''
		GROUP BY owner ORDER BY avg_days ASC
	""", (d_from, d_to), as_dict=True)
	for d in data:
		d["avg_days"] = round(flt(d.avg_days), 1)
	return {"chart_data": None, "table_data": data, "kpis": {}, "total": len(data)}


def _rpt_emp_workload(d_from, d_to, filters, start, length):
	data = frappe.db.sql("""
		SELECT owner as employee, status, COUNT(*) as count FROM `tabRepair Order`
		WHERE status IN ('In Progress','Awaiting Parts','Scheduled')
		AND docstatus != 2 AND owner IS NOT NULL AND owner != ''
		GROUP BY owner, status ORDER BY count DESC
	""", as_dict=True)
	em = {}
	for d in data:
		if d.employee not in em:
			em[d.employee] = {"employee": d.employee, "total": 0, "breakdown": {}}
		em[d.employee]["total"] += d.count
		em[d.employee]["breakdown"][d.status] = d.count
	td = sorted(em.values(), key=lambda x: x["total"], reverse=True)
	return {"chart_data": {"labels": [d["employee"] for d in td[:10]],
			"values": [d["total"] for d in td[:10]]},
			"table_data": td, "kpis": {"total_active_wo": sum(d["total"] for d in td)}, "total": len(td)}


REPORT_HANDLERS = {
	"fleet_health_score": _rpt_fleet_health,
	"age_distribution": _rpt_age_distribution,
	"utilization_overview": _rpt_utilization,
	"downtime_summary": _rpt_downtime,
	"mileage_by_vehicle": _rpt_mileage,
	"low_use_vehicles": _rpt_low_use,
	"fuel_vs_mileage": _rpt_fuel_mileage,
	"wo_volume_trend": _rpt_wo_volume_trend,
	"wo_avg_resolution": _rpt_wo_avg_resolution,
	"wo_backlog_status": _rpt_wo_backlog_status,
	"wo_cost_variance": _rpt_wo_cost_variance,
	"wo_rework_rate": _rpt_wo_rework_rate,
	"low_stock_items": _rpt_low_stock,
	"fast_moving_items": _rpt_fast_moving,
	"wo_consumption": _rpt_wo_consumption,
	"inspection_pass_fail": _rpt_insp_pass_fail,
	"overdue_schedules": _rpt_overdue_sched,
	"failure_hotspots": _rpt_failure_hotspots,
	"inspector_productivity": _rpt_inspector_prod,
	"issues_new_vs_resolved": _rpt_issues_trend,
	"issues_mttr": _rpt_issues_mttr,
	"top_fault_codes": _rpt_top_faults,
	"high_severity_open": _rpt_high_severity,
	"expenses_by_category": _rpt_expenses_cat,
	"cost_per_vehicle": _rpt_cost_vehicle,
	"cost_per_km": _rpt_cost_km,
	"invoice_aging": _rpt_invoice_aging,
	"top_customers_revenue": _rpt_top_cust_rev,
	"customer_outstanding": _rpt_cust_outstanding,
	"employee_wo_completed": _rpt_emp_wo,
	"employee_avg_completion": _rpt_emp_avg,
	"employee_workload": _rpt_emp_workload,
}
