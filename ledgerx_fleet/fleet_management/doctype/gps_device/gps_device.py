import frappe
from frappe.model.document import Document


class GPSDevice(Document):
	def on_update(self):
		if self.vehicle and self.status == "Active":
			frappe.db.set_value("Vehicle", self.vehicle, "gps_device", self.name, update_modified=False)
