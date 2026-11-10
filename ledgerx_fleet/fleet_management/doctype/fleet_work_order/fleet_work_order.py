import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from ledgerx_fleet.utils import fleet
from ledgerx_fleet.utils import logic


class FleetWorkOrder(Document):
	def validate(self):
		s = fleet.get_settings()
		if not self.company:
			self.company = s.company
		if not self.cost_center:
			self.cost_center = fleet.cost_center_for(self.vehicle) or s.cost_center
		if not self.odometer:
			self.odometer = frappe.db.get_value("Vehicle", self.vehicle, "last_odometer") or 0
		for p in self.parts:
			p.amount = flt(p.qty) * flt(p.rate)
			if not p.warehouse and s.issue_parts_from_stock:
				p.warehouse = s.default_warehouse
		self.parts_cost = sum(flt(p.amount) for p in self.parts)
		task_total = sum(flt(t.task_cost) for t in self.tasks)
		if task_total:
			self.labor_cost = task_total
		self.total_cost = flt(self.parts_cost) + flt(self.labor_cost) + flt(self.other_cost)
		if self.workshop_type == "External" and not self.supplier:
			frappe.msgprint(_("Choose the supplier of the external workshop"), indicator="orange", alert=True)
		if self.completion_date and self.start_date and logic.to_date(self.completion_date) < logic.to_date(self.start_date):
			frappe.throw(_("Completion Date cannot be before Start Date"))
		if self.status == "Completed" and self.docstatus == 0:
			frappe.throw(_("Submit the work order to complete it"))
		if self.status in ("In Progress", "Waiting Parts") and not self.start_date:
			self.start_date = nowdate()

	def on_update(self):
		if self.docstatus == 0 and self.status in ("In Progress", "Waiting Parts"):
			fleet.set_vehicle_status(self.vehicle, "In Maintenance", only_if=("Active", "In Maintenance", None, ""))

	def before_submit(self):
		if self.status == "Cancelled":
			frappe.throw(_("A cancelled work order cannot be submitted"))

	def on_submit(self):
		self.db_set("status", "Completed")
		fleet.update_vehicle_odometer(self.vehicle, self.odometer)
		self.update_schedules()
		self.release_vehicle()
		s = fleet.get_settings()
		to_expense = flt(self.labor_cost) + flt(self.other_cost)
		if s.issue_parts_from_stock and self.parts:
			self.db_set("stock_entry", self.issue_parts(s))
		else:
			to_expense += flt(self.parts_cost)
		je = fleet.post_journal_entry(
			self, s.maintenance_expense_account, to_expense,
			_("Work order {0} - {1}").format(self.name, self.vehicle), self.completion_date,
		)
		if je:
			self.db_set("journal_entry", je)
		self.update_incident()

	def on_cancel(self):
		self.db_set("status", "Cancelled")
		fleet.cancel_linked("Journal Entry", self.journal_entry)
		fleet.cancel_linked("Stock Entry", self.stock_entry)
		self.release_vehicle()
		self.update_incident()

	def release_vehicle(self):
		busy = frappe.db.exists(
			"Fleet Work Order",
			{"vehicle": self.vehicle, "docstatus": ["<", 2], "status": ["in", ["In Progress", "Waiting Parts"]],
				"name": ["!=", self.name]},
		)
		if not busy:
			fleet.set_vehicle_status(self.vehicle, "Active", only_if=("In Maintenance",))

	def update_schedules(self):
		for t in self.tasks:
			if t.schedule:
				frappe.db.set_value(
					"Service Schedule", t.schedule,
					{"last_service_date": self.completion_date, "last_service_odometer": self.odometer,
						"last_work_order": self.name},
					update_modified=False,
				)
				sch = frappe.get_doc("Service Schedule", t.schedule)
				sch.flags.ignore_permissions = True
				sch.save()

	def update_incident(self):
		if self.incident:
			from ledgerx_fleet.fleet_management.doctype.fleet_incident.fleet_incident import refresh_costs

			refresh_costs(self.incident)

	def issue_parts(self, s):
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Issue",
				"company": self.company,
				"posting_date": self.completion_date,
				"remarks": _("Work order {0} - {1}").format(self.name, self.vehicle),
				"items": [
					{
						"item_code": p.item_code,
						"qty": p.qty,
						"s_warehouse": p.warehouse,
						"basic_rate": p.rate,
						"expense_account": s.maintenance_expense_account,
						"cost_center": self.cost_center,
					}
					for p in self.parts
				],
			}
		)
		se.flags.ignore_permissions = True
		se.insert()
		se.submit()
		return se.name
