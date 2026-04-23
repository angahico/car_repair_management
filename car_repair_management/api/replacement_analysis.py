import json

import frappe
from frappe.utils import getdate, nowdate, add_days, flt
from datetime import date

from car_repair_management.car_repair_management.doctype.fleet_replacement_settings.fleet_replacement_settings import (
	get_criteria,
)


@frappe.whitelist()
def get_replacement_analysis(vehicles=None, department=None):
	"""Get replacement analysis with scoring, recommendations, and scatter data for all vehicles."""
	today = getdate(nowdate())
	one_year_ago = add_days(today, -365)
	criteria = get_criteria()
	weights = criteria["weights"]

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

	ro_map = {}
	if all_vehicles:
		v_names = [v.name for v in all_vehicles]
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

	candidates = []
	scatter_data = []

	for v in all_vehicles:
		acq_date = getdate(v.acquisition_date) if v.acquisition_date else getdate(v.creation)
		age_years = round((today - acq_date).days / 365.25, 1)

		lifetime_cost = flt(v.repair_cost_to_date)
		book_value = flt(v.vehicle_value)
		cost_to_value = round(lifetime_cost / book_value, 2) if book_value else 0

		vehicle_ros = ro_map.get(v.name, [])
		maintenance_count = len(vehicle_ros)

		downtime_days = 0
		for ro in vehicle_ros:
			start = getdate(ro.creation)
			end = getdate(ro.modified) if ro.status in ("Closed", "Delivered") else today
			downtime_days += max((end - start).days, 0)

		odometer = v.last_odometer or 0

		age_score = min(100, (age_years / criteria["age_threshold"]) * 100) * weights["age"] / 100
		mileage_score = min(100, (odometer / criteria["mileage_threshold"]) * 100) * weights["mileage"] / 100
		cost_ratio_score = min(100, (cost_to_value / criteria["cost_to_value_ratio"]) * 100) * weights["cost_ratio"] / 100
		downtime_score = min(100, (downtime_days / criteria["downtime_threshold"]) * 100) * weights["downtime"] / 100
		maint_score = min(100, (maintenance_count / criteria["maintenance_freq_threshold"]) * 100) * weights["maintenance_freq"] / 100

		replacement_score = int(round(age_score + mileage_score + cost_ratio_score + downtime_score + maint_score))
		replacement_score = min(replacement_score, 100)

		if replacement_score <= criteria.get("keep_max_score", 40):
			recommendation = "Keep"
		elif replacement_score <= criteria.get("monitor_max_score", 70):
			recommendation = "Monitor"
		else:
			recommendation = "Replace"

		candidates.append({
			"vehicle": v.name,
			"license_plate": v.license_plate,
			"make": v.make,
			"model": v.model,
			"age_years": age_years,
			"total_lifetime_cost": lifetime_cost,
			"current_book_value": book_value,
			"cost_to_value_ratio": cost_to_value,
			"downtime_days": downtime_days,
			"maintenance_count": maintenance_count,
			"replacement_score": replacement_score,
			"recommendation": recommendation,
		})

		scatter_data.append({
			"vehicle": v.name,
			"age": age_years,
			"cost": lifetime_cost,
			"downtime": downtime_days,
			"recommendation": recommendation,
		})

	candidates.sort(key=lambda c: c["replacement_score"], reverse=True)
	scatter_data.sort(key=lambda s: s["age"])

	return {
		"criteria": criteria,
		"candidates": candidates,
		"scatter_data": scatter_data,
	}


@frappe.whitelist()
def run_financial_simulation(
	vehicle, resale_value=0, acquisition_cost=0,
	maintenance_reduction_pct=0, downtime_reduction_pct=0,
):
	"""Run a 3-5 year financial simulation comparing keep vs replace scenarios."""
	today = getdate(nowdate())
	one_year_ago = add_days(today, -365)

	resale_value = flt(resale_value)
	acquisition_cost = flt(acquisition_cost)
	maintenance_reduction_pct = flt(maintenance_reduction_pct)
	downtime_reduction_pct = flt(downtime_reduction_pct)

	v = frappe.get_doc("Vehicle", vehicle)
	acq_date = getdate(v.acquisition_date) if v.acquisition_date else getdate(v.creation)
	age_years = round((today - acq_date).days / 365.25, 1)

	recent_ros = frappe.get_all(
		"Repair Order",
		filters={
			"vehicle": vehicle,
			"creation": [">=", one_year_ago],
		},
		fields=["creation", "modified", "total_job_cost", "status"],
	)

	annual_maintenance = sum(flt(ro.total_job_cost) for ro in recent_ros)
	annual_downtime = 0
	for ro in recent_ros:
		start = getdate(ro.creation)
		end = getdate(ro.modified) if ro.status in ("Closed", "Delivered") else today
		annual_downtime += max((end - start).days, 0)

	fuel_logs = frappe.get_all(
		"Vehicle Log",
		filters={
			"license_plate": vehicle,
			"date": [">=", one_year_ago],
			"fuel_qty": [">", 0],
		},
		fields=["fuel_qty", "price"],
	)
	annual_fuel = sum(flt(fl.fuel_qty) * flt(fl.price) for fl in fuel_logs)

	growth_factor = 1.10

	keep_projection = []
	replace_projection = []
	cumulative_keep = 0
	cumulative_replace = acquisition_cost - resale_value

	for year in range(1, 6):
		keep_maint = annual_maintenance * (growth_factor ** year)
		keep_fuel = annual_fuel
		keep_total = keep_maint + keep_fuel
		cumulative_keep += keep_total

		replace_maint = annual_maintenance * (1 - maintenance_reduction_pct / 100)
		replace_fuel = annual_fuel * 0.95
		replace_total = replace_maint + replace_fuel
		cumulative_replace += replace_total

		keep_projection.append({
			"year": year,
			"maintenance": round(keep_maint, 2),
			"fuel": round(keep_fuel, 2),
			"total": round(keep_total, 2),
			"cumulative": round(cumulative_keep, 2),
		})

		replace_projection.append({
			"year": year,
			"maintenance": round(replace_maint, 2),
			"fuel": round(replace_fuel, 2),
			"total": round(replace_total, 2),
			"cumulative": round(cumulative_replace, 2),
		})

	net_savings_5y = cumulative_keep - cumulative_replace
	breakeven_year = None
	running_keep = 0
	running_replace = acquisition_cost - resale_value
	for year in range(1, 6):
		running_keep += keep_projection[year - 1]["total"]
		running_replace += replace_projection[year - 1]["total"]
		if running_keep >= running_replace and breakeven_year is None:
			breakeven_year = year

	return {
		"vehicle": vehicle,
		"inputs": {
			"resale_value": resale_value,
			"acquisition_cost": acquisition_cost,
			"maintenance_reduction_pct": maintenance_reduction_pct,
			"downtime_reduction_pct": downtime_reduction_pct,
		},
		"current_annual": {
			"maintenance": round(annual_maintenance, 2),
			"fuel": round(annual_fuel, 2),
			"downtime_days": annual_downtime,
		},
		"keep_projection": keep_projection,
		"replace_projection": replace_projection,
		"summary": {
			"net_savings_5y": round(net_savings_5y, 2),
			"breakeven_year": breakeven_year,
			"recommendation": "Replace" if net_savings_5y > 0 else "Keep",
		},
	}
