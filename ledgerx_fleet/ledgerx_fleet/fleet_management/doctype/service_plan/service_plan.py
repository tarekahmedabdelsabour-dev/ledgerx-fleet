import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class ServicePlan(Document):
	def validate(self):
		seen = set()
		for t in self.tasks:
			if not (t.interval_km or t.interval_days):
				frappe.throw(_("Row {0}: set an interval in km or days for {1}").format(t.idx, frappe.bold(t.task)))
			if t.task.lower() in seen:
				frappe.throw(_("Row {0}: duplicate task {1}").format(t.idx, frappe.bold(t.task)))
			seen.add(t.task.lower())


def apply_plan(plan, vehicle):
	"""Create the missing Service Schedules of `plan` for `vehicle`. Baseline = today / current odometer."""
	if not plan or not vehicle:
		return 0
	odo = frappe.db.get_value("Vehicle", vehicle, "last_odometer") or 0
	existing = {
		r.lower() for r in frappe.get_all("Service Schedule", filters={"vehicle": vehicle}, pluck="task")
	}
	created = 0
	for t in frappe.get_doc("Service Plan", plan).tasks:
		if t.task.lower() in existing:
			continue
		frappe.get_doc(
			{
				"doctype": "Service Schedule",
				"vehicle": vehicle,
				"task": t.task,
				"category": t.category,
				"interval_km": t.interval_km,
				"interval_days": t.interval_days,
				"last_service_date": nowdate(),
				"last_service_odometer": odo,
				"source_plan": plan,
			}
		).insert(ignore_permissions=True)
		created += 1
	return created


@frappe.whitelist()
def apply_plan_to_vehicle(plan, vehicle):
	frappe.has_permission("Service Schedule", "create", throw=True)
	return apply_plan(plan, vehicle)
