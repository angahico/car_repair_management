import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, add_days, add_to_date


class WorkshopReportSchedule(Document):
	def before_save(self):
		if self.enabled and not self.next_run:
			self.compute_next_run()

	def compute_next_run(self):
		now = now_datetime()
		if self.frequency == "Daily":
			self.next_run = add_days(now, 1)
		elif self.frequency == "Weekly":
			self.next_run = add_days(now, 7)
		elif self.frequency == "Monthly":
			self.next_run = add_to_date(now, months=1)
