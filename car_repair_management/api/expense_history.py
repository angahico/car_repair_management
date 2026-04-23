import json

import frappe
from frappe.utils import getdate, nowdate, add_days, flt


@frappe.whitelist()
def get_expense_history(date_from=None, date_to=None, vehicles=None, category=None):
	"""Get expense history with KPIs, breakdowns, records, and efficiency metrics."""
	today = getdate(nowdate())

	vehicle_list = None
	if vehicles:
		if isinstance(vehicles, str):
			vehicle_list = json.loads(vehicles)
		else:
			vehicle_list = vehicles

	fuel_filters = {}
	if date_from and date_to:
		fuel_filters["date"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		fuel_filters["date"] = [">=", getdate(date_from)]
	elif date_to:
		fuel_filters["date"] = ["<=", getdate(date_to)]

	if vehicle_list:
		fuel_filters["license_plate"] = ["in", vehicle_list]

	fuel_filters["fuel_qty"] = [">", 0]

	fuel_logs = frappe.get_all(
		"Vehicle Log",
		filters=fuel_filters,
		fields=[
			"name", "license_plate", "date", "fuel_qty", "price",
			"supplier", "owner",
		],
		order_by="date desc",
	)

	ro_filters = {}
	if date_from and date_to:
		ro_filters["creation"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		ro_filters["creation"] = [">=", getdate(date_from)]
	elif date_to:
		ro_filters["creation"] = ["<=", getdate(date_to)]

	if vehicle_list:
		ro_filters["vehicle"] = ["in", vehicle_list]

	repair_orders = frappe.get_all(
		"Repair Order",
		filters=ro_filters,
		fields=[
			"name", "vehicle", "creation", "total_job_cost", "parts_cost",
			"labor_cost", "other_charges", "status", "customer", "owner",
		],
		order_by="creation desc",
	)

	fuel_spend = 0.0
	maintenance_spend = 0.0
	vehicle_expenses = {}
	month_data = {}
	records = []

	for fl in fuel_logs:
		amount = flt(fl.fuel_qty) * flt(fl.price)
		fuel_spend += amount
		v = fl.license_plate
		vehicle_expenses[v] = vehicle_expenses.get(v, 0) + amount

		month_key = str(fl.date)[:7] if fl.date else None
		if month_key:
			if month_key not in month_data:
				month_data[month_key] = {"fuel": 0, "maintenance": 0, "other": 0}
			month_data[month_key]["fuel"] += amount

		if not category or category == "Fuel":
			records.append({
				"name": fl.name,
				"date": str(fl.date) if fl.date else None,
				"vehicle": v,
				"category": "Fuel",
				"amount": round(amount, 2),
				"vendor": fl.supplier or None,
				"linked_work_order": None,
				"entered_by": fl.owner,
				"has_receipt": False,
				"approval_status": "Approved",
			})

	for ro in repair_orders:
		amount = flt(ro.total_job_cost)
		maintenance_spend += amount
		v = ro.vehicle
		vehicle_expenses[v] = vehicle_expenses.get(v, 0) + amount

		month_key = str(ro.creation)[:7] if ro.creation else None
		if month_key:
			if month_key not in month_data:
				month_data[month_key] = {"fuel": 0, "maintenance": 0, "other": 0}
			month_data[month_key]["maintenance"] += amount

		if not category or category == "Maintenance":
			records.append({
				"name": ro.name,
				"date": str(getdate(ro.creation)) if ro.creation else None,
				"vehicle": v,
				"category": "Maintenance",
				"amount": round(amount, 2),
				"vendor": None,
				"linked_work_order": ro.name,
				"entered_by": ro.owner,
				"has_receipt": False,
				"approval_status": "Approved",
			})

	records.sort(key=lambda r: r["date"] or "", reverse=True)

	total_expenses = fuel_spend + maintenance_spend
	num_vehicles = len(vehicle_expenses)
	avg_per_vehicle = round(total_expenses / num_vehicles, 2) if num_vehicles else 0

	total_mileage = _get_total_mileage(date_from, date_to, vehicle_list)
	cost_per_km = round(total_expenses / total_mileage, 2) if total_mileage else 0

	most_expensive = {"vehicle": "", "amount": 0}
	if vehicle_expenses:
		max_v = max(vehicle_expenses, key=vehicle_expenses.get)
		most_expensive = {"vehicle": max_v, "amount": round(vehicle_expenses[max_v], 2)}

	by_category = [
		{"category": "Fuel", "amount": round(fuel_spend, 2)},
		{"category": "Maintenance", "amount": round(maintenance_spend, 2)},
	]

	by_vehicle = sorted(
		[{"vehicle": v, "amount": round(a, 2)} for v, a in vehicle_expenses.items()],
		key=lambda x: x["amount"],
		reverse=True,
	)

	by_month = []
	for mk in sorted(month_data.keys()):
		by_month.append({
			"month": mk,
			"fuel": round(month_data[mk]["fuel"], 2),
			"maintenance": round(month_data[mk]["maintenance"], 2),
			"other": round(month_data[mk]["other"], 2),
		})

	fuel_cost_per_km = _get_fuel_cost_per_km(date_from, date_to, vehicle_list)

	maintenance_trend = []
	for mk in sorted(month_data.keys()):
		maintenance_trend.append({
			"month": mk,
			"cost": round(month_data[mk]["maintenance"], 2),
		})

	anomalies = _detect_expense_anomalies(vehicle_expenses, avg_per_vehicle)

	return {
		"kpis": {
			"total_expenses": round(total_expenses, 2),
			"fuel_spend": round(fuel_spend, 2),
			"maintenance_spend": round(maintenance_spend, 2),
			"insurance_spend": 0,
			"avg_per_vehicle": avg_per_vehicle,
			"cost_per_km": cost_per_km,
			"most_expensive": most_expensive,
		},
		"breakdown": {
			"by_category": by_category,
			"by_vehicle": by_vehicle,
			"by_month": by_month,
		},
		"records": records,
		"efficiency": {
			"fuel_cost_per_km": fuel_cost_per_km,
			"maintenance_trend": maintenance_trend,
			"budget_warnings": [],
			"anomalies": anomalies,
		},
	}


def _get_total_mileage(date_from, date_to, vehicle_list):
	"""Calculate total fleet mileage for the given period."""
	filters = {}
	if date_from and date_to:
		filters["date"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		filters["date"] = [">=", getdate(date_from)]
	elif date_to:
		filters["date"] = ["<=", getdate(date_to)]

	if vehicle_list:
		filters["license_plate"] = ["in", vehicle_list]

	logs = frappe.get_all(
		"Vehicle Log",
		filters=filters,
		fields=["odometer", "last_odometer"],
	)

	total = 0
	for log in logs:
		delta = (log.odometer or 0) - (log.last_odometer or 0)
		if delta > 0:
			total += delta
	return total


def _get_fuel_cost_per_km(date_from, date_to, vehicle_list):
	"""Calculate fuel cost per km for each vehicle."""
	filters = {"fuel_qty": [">", 0]}
	if date_from and date_to:
		filters["date"] = ["between", [getdate(date_from), getdate(date_to)]]
	elif date_from:
		filters["date"] = [">=", getdate(date_from)]
	elif date_to:
		filters["date"] = ["<=", getdate(date_to)]

	if vehicle_list:
		filters["license_plate"] = ["in", vehicle_list]

	logs = frappe.get_all(
		"Vehicle Log",
		filters=filters,
		fields=["license_plate", "fuel_qty", "price", "odometer", "last_odometer"],
	)

	vehicle_fuel = {}
	vehicle_km = {}
	for log in logs:
		v = log.license_plate
		vehicle_fuel[v] = vehicle_fuel.get(v, 0) + flt(log.fuel_qty) * flt(log.price)
		delta = (log.odometer or 0) - (log.last_odometer or 0)
		if delta > 0:
			vehicle_km[v] = vehicle_km.get(v, 0) + delta

	result = []
	for v in vehicle_fuel:
		km = vehicle_km.get(v, 0)
		cpk = round(vehicle_fuel[v] / km, 2) if km else 0
		result.append({"vehicle": v, "cost_per_km": cpk})

	result.sort(key=lambda x: x["cost_per_km"], reverse=True)
	return result


def _detect_expense_anomalies(vehicle_expenses, avg_per_vehicle):
	"""Detect vehicles with unusually high expenses (> 2x average)."""
	anomalies = []
	if avg_per_vehicle <= 0:
		return anomalies

	for v, amount in vehicle_expenses.items():
		if amount > avg_per_vehicle * 2:
			anomalies.append({
				"vehicle": v,
				"type": "high_expense",
				"description": "Expenses of {} are more than 2x the fleet average of {}".format(
					round(amount, 2), round(avg_per_vehicle, 2)
				),
			})

	return anomalies
