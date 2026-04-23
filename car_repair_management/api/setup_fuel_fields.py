import frappe


@frappe.whitelist()
def setup_fuel_custom_fields():
	"""Add fuel quota custom fields to the Vehicle DocType."""
	fields = [
		{
			"dt": "Vehicle",
			"fieldname": "custom_fuel_quota_section",
			"fieldtype": "Section Break",
			"label": "Fuel Quota Settings",
			"insert_after": "custom_drivers",
			"module": "Car Repair Management",
		},
		{
			"dt": "Vehicle",
			"fieldname": "custom_fuel_capacity_liters",
			"fieldtype": "Float",
			"label": "Fuel Tank Capacity (Liters)",
			"insert_after": "custom_fuel_quota_section",
			"module": "Car Repair Management",
			"precision": "2",
			"description": "Tank capacity in liters, used for fuel quota calculation",
		},
		{
			"dt": "Vehicle",
			"fieldname": "custom_km_per_liter",
			"fieldtype": "Float",
			"label": "KM per Liter",
			"insert_after": "custom_fuel_capacity_liters",
			"module": "Car Repair Management",
			"precision": "2",
			"description": "Average fuel efficiency in km/l",
		},
		{
			"dt": "Vehicle",
			"fieldname": "custom_column_break_fuel",
			"fieldtype": "Column Break",
			"insert_after": "custom_km_per_liter",
			"module": "Car Repair Management",
		},
		{
			"dt": "Vehicle",
			"fieldname": "custom_monthly_fuel_quota",
			"fieldtype": "Float",
			"label": "Monthly Fuel Quota (Liters)",
			"insert_after": "custom_column_break_fuel",
			"module": "Car Repair Management",
			"precision": "2",
			"description": "Override monthly quota. If 0, auto-calculated as capacity × 2",
		},
	]

	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	custom_fields = {}
	for f in fields:
		dt = f.pop("dt")
		custom_fields.setdefault(dt, []).append(f)

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
	return "Fuel custom fields created successfully"
