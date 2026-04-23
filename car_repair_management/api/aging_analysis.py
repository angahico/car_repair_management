import json
from statistics import median

import frappe
from frappe.utils import getdate, nowdate, add_days, flt

from car_repair_management.car_repair_management.doctype.fleet_replacement_settings.fleet_replacement_settings import (
	get_criteria,
)

AGE_BRACKETS = [
	{"label": "0-2 years", "min": 0, "max": 2},
	{"label": "3-5 years", "min": 3, "max": 5},
	{"label": "6-8 years", "min": 6, "max": 8},
	{"label": "9+ years", "min": 9, "max": 999},
]


@frappe.whitelist()
def get_aging_analysis(vehicles=None, department=None):
	"""Get fleet aging analysis with distribution, cost correlation, and risk dashboard."""
	today = getdate(nowdate())
	one_year_ago = add_days(today, -365)

	vehicle_filters = {}
	vehicle_list = None
	if vehicles:
		if isinstance(vehicles, str):
			vehicle_list = json.loads(vehicles)
		else:
			vehicle_list = vehicles
		if vehicle_list:
			vehicle_filters["name"] = ["in", vehicle_list]

	all_vehicles = frappe.get_all(
		"Vehicle",
		filters=vehicle_filters,
		fields=[
			"name", "license_plate", "make", "model", "year",
			"acquisition_date", "creation", "vehicle_value",
			"last_odometer", "repair_cost_to_date",
		],
	)

	total_vehicles = len(all_vehicles)
	if not total_vehicles:
		return _empty_result()

	replacement_threshold = get_criteria().get("age_threshold", 8)

	ro_map = {}
	v_names = [v.name for v in all_vehicles]
	if v_names:
		recent_ros = frappe.get_all(
			"Repair Order",
			filters={
				"vehicle": ["in", v_names],
				"creation": [">=", one_year_ago],
			},
			fields=["name", "vehicle", "creation", "modified", "status", "total_job_cost"],
		)
		for ro in recent_ros:
			ro_map.setdefault(ro.vehicle, []).append(ro)

	bracket_vehicles = {b["label"]: [] for b in AGE_BRACKETS}
	bracket_costs = {b["label"]: [] for b in AGE_BRACKETS}
	bracket_downtime = {b["label"]: [] for b in AGE_BRACKETS}
	ages = []
	approaching = []
	beyond = []

	for v in all_vehicles:
		acq_date = getdate(v.acquisition_date) if v.acquisition_date else getdate(v.creation)
		age_years = round((today - acq_date).days / 365.25, 1)
		ages.append(age_years)

		bracket_label = None
		for b in AGE_BRACKETS:
			if b["min"] <= age_years <= b["max"]:
				bracket_label = b["label"]
				break
		if not bracket_label:
			bracket_label = AGE_BRACKETS[-1]["label"]

		bracket_vehicles[bracket_label].append(v.name)

		vehicle_ros = ro_map.get(v.name, [])
		annual_cost = sum(flt(ro.total_job_cost) for ro in vehicle_ros)
		bracket_costs[bracket_label].append(annual_cost)

		downtime_days = 0
		for ro in vehicle_ros:
			start = getdate(ro.creation)
			end = getdate(ro.modified) if ro.status in ("Closed", "Delivered") else today
			downtime_days += max((end - start).days, 0)
		bracket_downtime[bracket_label].append(downtime_days)

		if age_years >= replacement_threshold:
			beyond.append({"vehicle": v.name, "age": age_years})
		elif age_years >= replacement_threshold - 1:
			approaching.append({"vehicle": v.name, "age": age_years, "threshold": replacement_threshold})

	brackets = []
	for b in AGE_BRACKETS:
		label = b["label"]
		count = len(bracket_vehicles[label])
		pct = round(count / total_vehicles * 100, 1) if total_vehicles else 0
		brackets.append({
			"label": label,
			"count": count,
			"pct": pct,
			"vehicles": bracket_vehicles[label],
		})

	avg_age = round(sum(ages) / len(ages), 1) if ages else 0
	median_age = round(median(ages), 1) if ages else 0

	maintenance_by_bracket = []
	downtime_by_bracket = []
	for b in AGE_BRACKETS:
		label = b["label"]
		costs = bracket_costs[label]
		avg_cost = round(sum(costs) / len(costs), 2) if costs else 0
		maintenance_by_bracket.append({"bracket": label, "avg_cost": avg_cost})

		dt = bracket_downtime[label]
		avg_dt = round(sum(dt) / len(dt), 1) if dt else 0
		downtime_by_bracket.append({"bracket": label, "avg_days": avg_dt})

	risk_pct = round(
		(len(approaching) + len(beyond)) / total_vehicles * 100, 1
	) if total_vehicles else 0

	forecasted_12m = 0
	forecasted_24m = 0
	for v in all_vehicles:
		acq_date = getdate(v.acquisition_date) if v.acquisition_date else getdate(v.creation)
		age_in_12m = ((today - acq_date).days + 365) / 365.25
		age_in_24m = ((today - acq_date).days + 730) / 365.25
		current_age = (today - acq_date).days / 365.25

		if current_age < replacement_threshold <= age_in_12m:
			forecasted_12m += 1
		if current_age < replacement_threshold <= age_in_24m:
			forecasted_24m += 1

	return {
		"distribution": {
			"brackets": brackets,
			"avg_age": avg_age,
			"median_age": median_age,
			"total_vehicles": total_vehicles,
		},
		"aging_vs_cost": {
			"maintenance_by_bracket": maintenance_by_bracket,
			"downtime_by_bracket": downtime_by_bracket,
		},
		"risk_dashboard": {
			"approaching_threshold": approaching,
			"beyond_lifecycle": beyond,
			"risk_exposure_pct": risk_pct,
			"forecasted_replacements_12m": forecasted_12m,
			"forecasted_replacements_24m": forecasted_24m,
		},
	}


def _empty_result():
	"""Return an empty result structure when no vehicles are found."""
	return {
		"distribution": {
			"brackets": [
				{"label": b["label"], "count": 0, "pct": 0, "vehicles": []}
				for b in AGE_BRACKETS
			],
			"avg_age": 0,
			"median_age": 0,
			"total_vehicles": 0,
		},
		"aging_vs_cost": {
			"maintenance_by_bracket": [
				{"bracket": b["label"], "avg_cost": 0} for b in AGE_BRACKETS
			],
			"downtime_by_bracket": [
				{"bracket": b["label"], "avg_days": 0} for b in AGE_BRACKETS
			],
		},
		"risk_dashboard": {
			"approaching_threshold": [],
			"beyond_lifecycle": [],
			"risk_exposure_pct": 0,
			"forecasted_replacements_12m": 0,
			"forecasted_replacements_24m": 0,
		},
	}
