import frappe


@frappe.whitelist()
def setup_issue_custom_fields():
	"""Add custom fields to the Issue DocType for vehicle fleet management."""
	fields = [
		{
			"dt": "Issue",
			"fieldname": "custom_vehicle",
			"fieldtype": "Link",
			"label": "Vehicle",
			"options": "Vehicle",
			"insert_after": "subject",
			"module": "Car Repair Management",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_category",
			"fieldtype": "Select",
			"label": "Issue Category",
			"options": "\nMechanical\nElectrical\nBody/Paint\nInterior\nSafety\nCompliance\nOther",
			"insert_after": "custom_vehicle",
			"module": "Car Repair Management",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_severity",
			"fieldtype": "Select",
			"label": "Severity",
			"options": "\nLow\nMedium\nHigh\nCritical",
			"insert_after": "custom_category",
			"module": "Car Repair Management",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_source",
			"fieldtype": "Select",
			"label": "Issue Source",
			"options": "\nInspection\nDriver Report\nMechanic\nCustomer\nSensor\nOther",
			"insert_after": "custom_severity",
			"module": "Car Repair Management",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_assigned_to",
			"fieldtype": "Link",
			"label": "Assigned To",
			"options": "User",
			"insert_after": "custom_source",
			"module": "Car Repair Management",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_linked_work_order",
			"fieldtype": "Link",
			"label": "Linked Work Order",
			"options": "Repair Order",
			"insert_after": "custom_assigned_to",
			"module": "Car Repair Management",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_linked_inspection",
			"fieldtype": "Link",
			"label": "Linked Inspection",
			"options": "Vehicle Inspection",
			"insert_after": "custom_linked_work_order",
			"module": "Car Repair Management",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_linked_fault",
			"fieldtype": "Link",
			"label": "Linked Fault",
			"options": "Vehicle Fault",
			"insert_after": "custom_linked_inspection",
			"module": "Car Repair Management",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_resolution_notes",
			"fieldtype": "Text Editor",
			"label": "Resolution Notes",
			"insert_after": "resolution_details",
			"module": "Car Repair Management",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_workflow_state",
			"fieldtype": "Select",
			"label": "Workflow State",
			"options": "\nDraft\nPending Custodian Approval\nRejected\nSubmitted\nWork Order Created",
			"insert_after": "custom_resolution_notes",
			"module": "Car Repair Management",
			"default": "Draft",
		},
		{
			"dt": "Issue",
			"fieldname": "custom_requested_by_employee",
			"fieldtype": "Link",
			"label": "Requested By (Employee)",
			"options": "Employee",
			"insert_after": "custom_workflow_state",
			"module": "Car Repair Management",
			"read_only": 1,
		},
		{
			"dt": "Issue",
			"fieldname": "custom_approved_by",
			"fieldtype": "Link",
			"label": "Approved By",
			"options": "Employee",
			"insert_after": "custom_requested_by_employee",
			"module": "Car Repair Management",
			"read_only": 1,
		},
		{
			"dt": "Issue",
			"fieldname": "custom_approved_on",
			"fieldtype": "Datetime",
			"label": "Approved On",
			"insert_after": "custom_approved_by",
			"module": "Car Repair Management",
			"read_only": 1,
		},
		{
			"dt": "Issue",
			"fieldname": "custom_rejected_by",
			"fieldtype": "Link",
			"label": "Rejected By",
			"options": "Employee",
			"insert_after": "custom_approved_on",
			"module": "Car Repair Management",
			"read_only": 1,
		},
		{
			"dt": "Issue",
			"fieldname": "custom_rejected_on",
			"fieldtype": "Datetime",
			"label": "Rejected On",
			"insert_after": "custom_rejected_by",
			"module": "Car Repair Management",
			"read_only": 1,
		},
		{
			"dt": "Issue",
			"fieldname": "custom_rejection_reason",
			"fieldtype": "Small Text",
			"label": "Rejection Reason",
			"insert_after": "custom_rejected_on",
			"module": "Car Repair Management",
			"read_only": 1,
		},
	]

	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	custom_fields = {}
	for f in fields:
		dt = f.pop("dt")
		custom_fields.setdefault(dt, []).append(f)

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
	return "Custom fields created successfully"
