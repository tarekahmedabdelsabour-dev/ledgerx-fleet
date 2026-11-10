import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class DriverOdometerLog(Document):
	def validate(self):
		if not self.odometer or self.odometer <= 0:
			frappe.throw(_("Enter the odometer reading"))
		if not self.logged_at:
			self.logged_at = now_datetime()
		self.check_duplicate()
		if self.is_new():
			last = frappe.db.get_value("Vehicle", self.vehicle, "last_odometer") or 0
			if self.odometer < last:
				frappe.throw(_("Odometer {0} is lower than the last recorded reading {1}").format(self.odometer, last))
		self.day_distance = None
		if self.log_type == "End of Day":
			start = frappe.db.get_value(
				"Driver Odometer Log",
				{"driver": self.driver, "vehicle": self.vehicle, "log_date": self.log_date,
					"log_type": "Start of Day", "name": ("!=", self.name)},
				"odometer",
			)
			if start is not None:
				if self.odometer < start:
					frappe.throw(_("End reading cannot be lower than the start reading {0}").format(start))
				self.day_distance = self.odometer - start

	def check_duplicate(self):
		if frappe.db.exists("Driver Odometer Log", {
			"driver": self.driver, "log_date": self.log_date, "log_type": self.log_type, "name": ("!=", self.name)
		}):
			frappe.throw(_("{0} is already recorded for this driver on {1}").format(_(self.log_type), self.log_date))

	def after_insert(self):
		"""Keep the vehicle odometer current (never goes backwards)."""
		last = frappe.db.get_value("Vehicle", self.vehicle, "last_odometer") or 0
		if self.odometer > last:
			frappe.db.set_value("Vehicle", self.vehicle, "last_odometer", self.odometer)
