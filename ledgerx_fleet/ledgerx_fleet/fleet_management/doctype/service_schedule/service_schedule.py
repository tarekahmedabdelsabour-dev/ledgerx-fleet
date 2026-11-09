import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate

from ledgerx_fleet.utils import logic
from ledgerx_fleet.utils.fleet import get_settings


def compute(doc_like, current_odo, today=None):
	"""Return the computed fields for a schedule (dict-like with the stored fields)."""
	s = get_settings()
	today = today or nowdate()
	nd, no = logic.next_due(
		doc_like.get("last_service_date"), doc_like.get("last_service_odometer"),
		doc_like.get("interval_days"), doc_like.get("interval_km"),
	)
	status = "Disabled"
	if doc_like.get("is_active"):
		status = logic.schedule_status(nd, no, today, current_odo, s.service_alert_days, s.service_alert_km)
	return {
		"next_due_date": nd,
		"next_due_odometer": no,
		"current_odometer": current_odo,
		"remaining_km": None if no is None or current_odo is None else int(no) - int(current_odo),
		"remaining_days": None if nd is None else logic.days_left(nd, today),
		"status": status,
	}


class ServiceSchedule(Document):
	def validate(self):
		if not (self.interval_km or self.interval_days):
			frappe.throw(_("Set an interval in km or days"))
		dup = frappe.db.exists(
			"Service Schedule", {"vehicle": self.vehicle, "task": self.task, "name": ["!=", self.name or ""]}
		)
		if dup:
			frappe.throw(_("{0} already has a schedule for {1}: {2}").format(
				frappe.bold(self.vehicle), frappe.bold(self.task), dup))
		odo = frappe.db.get_value("Vehicle", self.vehicle, "last_odometer") or 0
		for k, v in compute(self, odo).items():
			self.set(k, v)


def refresh_all():
	"""Recompute every active schedule in one pass and write only the rows that changed."""
	today = nowdate()
	rows = frappe.db.sql(
		"""select s.name, s.is_active, s.last_service_date, s.last_service_odometer, s.interval_km,
		s.interval_days, s.status, s.remaining_km, s.remaining_days, v.last_odometer
		from `tabService Schedule` s join `tabVehicle` v on v.name = s.vehicle""",
		as_dict=True,
	)
	changed = []
	for r in rows:
		new = compute(r, r.last_odometer or 0, today)
		if (new["status"], new["remaining_km"], new["remaining_days"]) != (r.status, r.remaining_km, r.remaining_days):
			frappe.db.set_value("Service Schedule", r.name, new, update_modified=False)
			if new["status"] in ("Due Soon", "Overdue") and new["status"] != r.status:
				changed.append(r.name)
	return changed
