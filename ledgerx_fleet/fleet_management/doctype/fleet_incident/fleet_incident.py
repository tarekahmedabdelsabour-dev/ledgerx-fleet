import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ledgerx_fleet.utils import fleet


def repair_cost(incident):
	return flt(
		frappe.db.sql(
			"select ifnull(sum(total_cost), 0) from `tabFleet Work Order` where docstatus = 1 and incident = %s",
			incident,
		)[0][0]
	)


def net_loss(repair, other, approved, claim_status):
	received = flt(approved) if claim_status in ("Approved", "Paid") else 0
	return flt(repair) + flt(other) - received


def refresh_costs(incident):
	doc = frappe.get_doc("Fleet Incident", incident)
	doc.flags.ignore_permissions = True
	doc.save()


class FleetIncident(Document):
	def validate(self):
		s = fleet.get_settings()
		if not self.company:
			self.company = s.company
		if not self.cost_center:
			self.cost_center = fleet.cost_center_for(self.vehicle) or s.default_cost_center
		if not self.driver:
			self.driver = fleet.find_driver_at(self.vehicle, self.incident_datetime)
		if self.name:
			self.work_orders_cost = repair_cost(self.name)
		self.net_loss = net_loss(self.work_orders_cost, self.other_cost, self.approved_amount, self.claim_status)
		if self.claim_status in ("Filed", "Approved", "Rejected", "Paid") and not self.claim_no:
			frappe.msgprint(_("Enter the Claim No"), indicator="orange", alert=True)

	def on_update(self):
		if self.incident_type in ("Theft",) or self.severity == "Total Loss":
			fleet.set_vehicle_status(self.vehicle, "Out of Service", only_if=("Active", "On Trip", None, ""))
