import frappe
from frappe.model.document import Document


class FleetReplacementSettings(Document):
	def validate(self):
		self.total_weight = (
			(self.weight_age or 0)
			+ (self.weight_mileage or 0)
			+ (self.weight_cost_ratio or 0)
			+ (self.weight_downtime or 0)
			+ (self.weight_maintenance_frequency or 0)
		)
		if self.total_weight != 100:
			frappe.throw(
				f"Scoring weights must sum to 100. Current total: {self.total_weight}",
				title="Invalid Weights",
			)

		if (self.keep_max_score or 0) >= (self.monitor_max_score or 0):
			frappe.throw(
				"Keep Max Score must be less than Monitor Max Score.",
				title="Invalid Recommendation Thresholds",
			)


def get_criteria():
	"""Return replacement criteria dict from the Single DocType, falling back to defaults."""
	try:
		doc = frappe.get_single("Fleet Replacement Settings")
		return {
			"age_threshold": doc.age_threshold or 8,
			"mileage_threshold": doc.mileage_threshold or 200000,
			"cost_to_value_ratio": doc.cost_to_value_ratio_threshold or 0.5,
			"downtime_threshold": doc.downtime_threshold or 30,
			"maintenance_freq_threshold": doc.maintenance_frequency_threshold or 6,
			"weights": {
				"age": doc.weight_age or 20,
				"mileage": doc.weight_mileage or 20,
				"cost_ratio": doc.weight_cost_ratio or 25,
				"downtime": doc.weight_downtime or 20,
				"maintenance_freq": doc.weight_maintenance_frequency or 15,
			},
			"keep_max_score": doc.keep_max_score or 40,
			"monitor_max_score": doc.monitor_max_score or 70,
		}
	except Exception:
		# DocType not yet created or migrated — use defaults
		return {
			"age_threshold": 8,
			"mileage_threshold": 200000,
			"cost_to_value_ratio": 0.5,
			"downtime_threshold": 30,
			"maintenance_freq_threshold": 6,
			"weights": {
				"age": 20,
				"mileage": 20,
				"cost_ratio": 25,
				"downtime": 20,
				"maintenance_freq": 15,
			},
			"keep_max_score": 40,
			"monitor_max_score": 70,
		}
