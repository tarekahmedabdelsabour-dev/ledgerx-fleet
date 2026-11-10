import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class DriverExpense(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))
		if self.category == "Fuel" and flt(self.litres) <= 0:
			frappe.throw(_("Enter the litres for a fuel expense"))
		if not self.company or not self.cost_center:
			from ledgerx_fleet.utils import fleet

			s = frappe.get_cached_doc("Fleet Settings")
			self.company = self.company or s.company
			self.cost_center = self.cost_center or fleet.cost_center_for(self.vehicle) or s.cost_center
		if self.status == "Rejected" and not self.rejection_reason:
			frappe.throw(_("Enter the rejection reason"))
		if not self.is_new() and self.has_value_changed("status") and self.status != "Pending":
			self.reviewed_by = frappe.session.user

	def on_update(self):
		"""Approved fuel expenses become a draft Fuel Log (once)."""
		if self.status == "Approved" and self.category == "Fuel" and not self.fuel_log and self.odometer:
			try:
				fl = frappe.get_doc({
					"doctype": "Fuel Log", "posting_date": self.expense_date, "vehicle": self.vehicle,
					"driver": self.driver, "odometer": self.odometer, "quantity": self.litres,
					"rate": flt(self.amount) / flt(self.litres), "full_tank": 0, "company": self.company,
					"cost_center": self.cost_center, "payment_mode": "Cash",
					"station_name": _("Driver expense {0}").format(self.name),
				}).insert(ignore_permissions=True)
				self.db_set("fuel_log", fl.name)
			except Exception:
				frappe.log_error(title=f"Driver Expense {self.name}: fuel log", message=frappe.get_traceback())
