import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate

from ledgerx_fleet.utils import logic


class FleetAssignment(Document):
	def validate(self):
		if self.to_date and logic.to_date(self.to_date) < logic.to_date(self.from_date):
			frappe.throw(_("To Date cannot be before From Date"))
		self.check_overlap("vehicle", _("Vehicle"))
		self.check_overlap("driver", _("Driver"))
		self.status = "Ended" if self.to_date and logic.to_date(self.to_date) < logic.to_date(nowdate()) else "Active"
		if not self.start_odometer:
			self.start_odometer = frappe.db.get_value("Vehicle", self.vehicle, "last_odometer")

	def check_overlap(self, field, label):
		rows = frappe.get_all(
			"Fleet Assignment",
			filters={field: self.get(field), "name": ["!=", self.name or ""]},
			fields=["name", "from_date", "to_date"],
		)
		for r in rows:
			if logic.ranges_overlap(logic.to_date(self.from_date), logic.to_date(self.to_date),
					logic.to_date(r.from_date), logic.to_date(r.to_date)):
				frappe.throw(
					_("{0} {1} is already assigned in {2}").format(label, frappe.bold(self.get(field)), r.name)
				)

	def on_update(self):
		sync_current_driver(self.vehicle)

	def on_trash(self):
		sync_current_driver(self.vehicle, exclude=self.name)


def sync_current_driver(vehicle, exclude=None):
	today = nowdate()
	row = frappe.db.sql(
		"""select driver from `tabFleet Assignment` where vehicle = %s and from_date <= %s
		and (to_date is null or to_date >= %s) and name != %s order by from_date desc limit 1""",
		(vehicle, today, today, exclude or ""),
	)
	driver = row[0][0] if row else None
	old = frappe.db.get_value("Vehicle", vehicle, "current_driver")
	frappe.db.set_value("Vehicle", vehicle, "current_driver", driver, update_modified=False)
	if old and old != driver:
		frappe.db.set_value("Driver", old, "current_vehicle", None, update_modified=False)
	if driver:
		frappe.db.set_value("Driver", driver, "current_vehicle", vehicle, update_modified=False)
