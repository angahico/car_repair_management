import json

import frappe
from frappe.utils import getdate, nowdate, add_days, flt
from datetime import datetime


@frappe.whitelist()
def get_meter_history(date_from=None, date_to=None, vehicles=None, source=None):
	"""Get meter/odometer history with KPIs, trend data, anomaly detection, and integrity checks."""
	today = getdate(nowdate())

	filters = {}
	if date_from:
		filters["date"] = [">=", getdate(date_from)]
	if date_to:
		if "date" in filters:
			filters["date"] = ["between", [getdate(date_from), getdate(date_to)]]
		else:
			filters["date"] = ["<=", getdate(date_to)]

	vehicle_list = None
	if vehicles:
		if isinstance(vehicles, str):
			vehicle_list = json.loads(vehicles)
		else:
			vehicle_list = vehicles
		if vehicle_list:
			filters["license_plate"] = ["in", vehicle_list]

	logs = frappe.get_all(
		"Vehicle Log",
		filters=filters,
		fields=[
			"name", "license_plate", "date", "odometer", "last_odometer",
			"employee", "owner", "fuel_qty", "price",
		],
		order_by="date desc, creation desc",
	)

	records = []
	vehicle_km = {}
	daily_km = {}

	for log in logs:
		reading = log.odometer or 0
		prev_reading = log.last_odometer or 0
		delta = reading - prev_reading

		anomaly = None
		if delta < 0:
			anomaly = {"type": "negative_delta", "description": "Odometer reading decreased from {} to {}".format(prev_reading, reading)}
		elif delta > 1000:
			anomaly = {"type": "unrealistic_jump", "description": "Jump of {} km in a single log entry".format(delta)}

		records.append({
			"name": log.name,
			"date": str(log.date) if log.date else None,
			"vehicle": log.license_plate,
			"reading": reading,
			"reading_delta": delta,
			"source": "Manual",
			"recorded_by": log.owner,
			"anomaly": anomaly,
			"notes": "",
		})

		v = log.license_plate
		vehicle_km[v] = vehicle_km.get(v, 0) + max(delta, 0)

		date_key = str(log.date) if log.date else None
		if date_key:
			if date_key not in daily_km:
				daily_km[date_key] = {"total_km": 0, "vehicle_data": {}}
			daily_km[date_key]["total_km"] += max(delta, 0)
			daily_km[date_key]["vehicle_data"][v] = daily_km[date_key]["vehicle_data"].get(v, 0) + max(delta, 0)

	total_fleet_mileage = sum(vehicle_km.values())
	num_vehicles_with_data = len(vehicle_km)
	avg_km = round(total_fleet_mileage / num_vehicles_with_data, 1) if num_vehicles_with_data else 0

	highest_usage = {"vehicle": "", "km": 0}
	lowest_usage = {"vehicle": "", "km": 0}
	if vehicle_km:
		max_v = max(vehicle_km, key=vehicle_km.get)
		min_v = min(vehicle_km, key=vehicle_km.get)
		highest_usage = {"vehicle": max_v, "km": vehicle_km[max_v]}
		lowest_usage = {"vehicle": min_v, "km": vehicle_km[min_v]}

	trend = []
	for date_key in sorted(daily_km.keys()):
		trend.append({
			"date": date_key,
			"total_km": daily_km[date_key]["total_km"],
			"vehicle_data": daily_km[date_key]["vehicle_data"],
		})

	all_vehicles_filters = {}
	if vehicle_list:
		all_vehicles_filters["name"] = ["in", vehicle_list]
	all_vehicles = frappe.get_all("Vehicle", filters=all_vehicles_filters, fields=["name"])
	total_vehicles = len(all_vehicles)

	threshold_date = add_days(today, -30)
	recent_logs = frappe.get_all(
		"Vehicle Log",
		filters={"date": [">=", threshold_date]},
		fields=["license_plate"],
		group_by="license_plate",
	)
	vehicles_with_recent = set(r.license_plate for r in recent_logs)
	all_vehicle_names = set(v.name for v in all_vehicles)
	missing_vehicles = all_vehicle_names - vehicles_with_recent

	last_readings = {}
	if missing_vehicles:
		for mv in missing_vehicles:
			last_log = frappe.get_all(
				"Vehicle Log",
				filters={"license_plate": mv},
				fields=["date"],
				order_by="date desc",
				limit=1,
			)
			last_date = last_log[0].date if last_log else None
			days_since = (today - getdate(last_date)).days if last_date else 999
			last_readings[mv] = {
				"vehicle": mv,
				"last_reading_date": str(last_date) if last_date else None,
				"days_since": days_since,
			}

	inconsistent_vehicles = list(set(
		r["vehicle"] for r in records if r["anomaly"] and r["anomaly"]["type"] == "negative_delta"
	))

	return {
		"kpis": {
			"total_fleet_mileage": total_fleet_mileage,
			"avg_km_per_vehicle": avg_km,
			"highest_usage": highest_usage,
			"lowest_usage": lowest_usage,
			"sensor_pct": 0,
			"missing_reading_alerts": len(missing_vehicles),
		},
		"trend": trend,
		"records": records,
		"integrity": {
			"inconsistent_vehicles": inconsistent_vehicles,
			"missing_readings": list(last_readings.values()),
			"manual_override_pct": 100,
			"total_vehicles": total_vehicles,
			"vehicles_with_readings": num_vehicles_with_data,
		},
	}
