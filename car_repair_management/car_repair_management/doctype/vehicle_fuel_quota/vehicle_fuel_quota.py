import frappe
from frappe.model.document import Document
from frappe.utils import flt


class VehicleFuelQuota(Document):
	def validate(self):
		self.remaining_liters = flt(self.quota_liters) - flt(self.consumed_liters)
		if self.remaining_liters <= 0:
			self.status = "Exhausted"
