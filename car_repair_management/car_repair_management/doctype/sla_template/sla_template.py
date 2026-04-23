import frappe
from frappe.model.document import Document
from frappe.utils import flt
from jinja2 import Template


class SLATemplate(Document):
	pass


@frappe.whitelist()
def apply_sla_to_repair_order(repair_order_name, sla_template_name=None):
	"""Apply SLA template to a Repair Order, computing response and delivery deadlines."""
	doc = frappe.get_doc("Repair Order", repair_order_name)

	if sla_template_name:
		sla = frappe.get_doc("SLA Template", sla_template_name)
	else:
		sla = _find_matching_sla(doc)

	if not sla:
		return {"message": "No matching SLA template found"}

	# Build Jinja context
	total_minutes = sum(flt(op.planned_minutes) for op in (doc.operations or []))
	context = {
		"doc": doc,
		"priority": doc.priority,
		"intake_channel": doc.intake_channel,
		"operations_count": len(doc.operations or []),
		"total_planned_minutes": total_minutes,
	}

	# Compute response time
	response_hours = sla.response_time_hours
	if not response_hours and sla.response_time_jinja:
		try:
			rendered = Template(sla.response_time_jinja).render(**context)
			response_hours = flt(rendered.strip())
		except Exception:
			frappe.log_error(frappe.get_traceback(), "SLA Jinja: response_time")

	# Compute resolution time
	resolution_hours = sla.resolution_time_hours
	if not resolution_hours and sla.resolution_time_jinja:
		try:
			rendered = Template(sla.resolution_time_jinja).render(**context)
			resolution_hours = flt(rendered.strip())
		except Exception:
			frappe.log_error(frappe.get_traceback(), "SLA Jinja: resolution_time")

	# Set SLA fields on the Repair Order
	from frappe.utils import now_datetime, add_to_date

	base_time = doc.entry_datetime or now_datetime()
	if response_hours:
		doc.sla_response_by = add_to_date(base_time, hours=response_hours)
	if resolution_hours:
		doc.sla_delivery_by = add_to_date(base_time, hours=resolution_hours)

	doc.flags.ignore_validate_update_after_submit = True
	doc.save(ignore_permissions=True)

	return {
		"sla_template": sla.name,
		"response_hours": response_hours,
		"resolution_hours": resolution_hours,
		"sla_response_by": str(doc.sla_response_by) if doc.sla_response_by else None,
		"sla_delivery_by": str(doc.sla_delivery_by) if doc.sla_delivery_by else None,
	}


def _find_matching_sla(doc):
	"""Find the best matching SLA template for a Repair Order."""
	filters = {"enabled": 1}

	# Try exact match on priority + intake_channel
	if doc.priority:
		filters["priority"] = doc.priority
	if doc.intake_channel:
		filters["intake_channel"] = doc.intake_channel

	sla_name = frappe.db.get_value("SLA Template", filters)
	if sla_name:
		return frappe.get_doc("SLA Template", sla_name)

	# Fallback: match on priority only
	filters.pop("intake_channel", None)
	sla_name = frappe.db.get_value("SLA Template", filters)
	if sla_name:
		return frappe.get_doc("SLA Template", sla_name)

	# Fallback: any enabled SLA with no conditions
	sla_name = frappe.db.get_value("SLA Template", {
		"enabled": 1,
		"priority": ["in", ["", None]],
		"intake_channel": ["in", ["", None]],
	})
	if sla_name:
		return frappe.get_doc("SLA Template", sla_name)

	return None
