import frappe

def update_job_costing_snapshots():
    # Iterate Repair Orders and update/create Job Costing snapshot
    ros = frappe.get_all("Repair Order", fields=["name", "project", "vehicle", "parts_cost", "labor_cost", "other_charges", "total_job_cost"])
    for ro in ros:
        jc = frappe.get_all("Job Costing", filters={"repair_order": ro.name}, limit=1)
        if jc:
            doc = frappe.get_doc("Job Costing", jc[0].name)
        else:
            doc = frappe.get_doc({"doctype": "Job Costing"})
            doc.repair_order = ro.name
        doc.project = ro.project
        doc.vehicle = ro.vehicle
        doc.parts_cost = ro.parts_cost
        doc.labor_cost = ro.labor_cost
        doc.other_charges = ro.other_charges
        doc.margin_snapshot = 0
        doc.save(ignore_permissions=True)


def execute_scheduled_reports():
	"""Execute any scheduled reports that are due."""
	from frappe.utils import now_datetime, getdate, nowdate, add_days

	now = now_datetime()
	schedules = frappe.get_all("Workshop Report Schedule",
		filters={"enabled": 1, "next_run": ["<=", now]},
		fields=["name"])

	for sched in schedules:
		try:
			from car_repair_management.api.reports import run_report_now
			run_report_now(sched.name)
		except Exception as e:
			frappe.log_error(f"Scheduled report execution failed for {sched.name}: {e}")
			try:
				doc = frappe.get_doc("Workshop Report Schedule", sched.name)
				doc.last_status = "Failed"
				doc.save(ignore_permissions=True)
			except Exception:
				pass
