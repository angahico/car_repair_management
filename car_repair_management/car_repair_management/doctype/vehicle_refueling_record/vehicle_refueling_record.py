import frappe
from frappe.model.document import Document
from frappe.utils import flt


class VehicleRefuelingRecord(Document):
	def validate(self):
		self.total_cost = flt(self.liters) * flt(self.cost_per_liter)

	def after_insert(self):
		self.update_quota()

	def on_trash(self):
		self.reverse_quota()

	def update_quota(self):
		if not self.quota_link:
			return
		quota = frappe.get_doc("Vehicle Fuel Quota", self.quota_link)
		quota.consumed_liters = flt(quota.consumed_liters) + flt(self.liters)
		quota.remaining_liters = flt(quota.quota_liters) - flt(quota.consumed_liters)
		if quota.remaining_liters <= 0:
			quota.status = "Exhausted"
		quota.save(ignore_permissions=True)

	def reverse_quota(self):
		if not self.quota_link:
			return
		quota = frappe.get_doc("Vehicle Fuel Quota", self.quota_link)
		quota.consumed_liters = max(0, flt(quota.consumed_liters) - flt(self.liters))
		quota.remaining_liters = flt(quota.quota_liters) - flt(quota.consumed_liters)
		if quota.remaining_liters > 0 and quota.status == "Exhausted":
			quota.status = "Active"
		quota.save(ignore_permissions=True)
