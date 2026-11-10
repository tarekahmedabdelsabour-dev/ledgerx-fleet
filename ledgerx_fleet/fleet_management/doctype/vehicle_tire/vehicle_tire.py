import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate

from ledgerx_fleet.utils import logic


class VehicleTire(Document):
	def validate(self):
		odo = frappe.db.get_value("Vehicle", self.vehicle, "last_odometer") if self.vehicle else None
		before = self.get_doc_before_save()
		if self.status == "Mounted":
			if not self.vehicle or not self.position:
				frappe.throw(_("Vehicle and Position are required for a mounted tire"))
			clash = frappe.db.exists(
				"Vehicle Tire",
				{"vehicle": self.vehicle, "position": self.position, "status": "Mounted",
					"name": ["!=", self.name or ""]},
			)
			if clash and self.position != "Other":
				frappe.throw(_("Position {0} on {1} already has tire {2}").format(
					_(self.position), frappe.bold(self.vehicle), frappe.bold(clash)))
			if not self.mounted_on:
				self.mounted_on = nowdate()
			if self.mount_odometer is None or self.mount_odometer == 0:
				self.mount_odometer = odo or 0
			self.removed_on = None
			self.removal_odometer = None
			current = odo
		else:
			if before and before.status == "Mounted":
				self.removed_on = self.removed_on or nowdate()
				self.removal_odometer = self.removal_odometer or odo or 0
			current = self.removal_odometer
		if self.mount_odometer is not None and current is not None:
			self.km_run, self.remaining_km = logic.tire_km(self.mount_odometer, current, self.expected_life_km)
