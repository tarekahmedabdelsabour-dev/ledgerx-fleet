import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ledgerx_fleet.utils import fleet

# category -> Fleet Settings field holding its expense account
EXPENSE_ACCOUNT = {
	"Fuel": "fuel_expense_account",
	"Maintenance": "maintenance_expense_account",
	"Tires": "maintenance_expense_account",
	"Wash": "maintenance_expense_account",
	"Toll": "other_expense_account",
	"Parking": "other_expense_account",
	"Other": "other_expense_account",
}


class DriverExpense(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))
		if self.category == "Fuel" and flt(self.litres) <= 0:
			frappe.throw(_("Enter the litres for a fuel expense"))
		if not self.company or not self.cost_center:
			s = fleet.get_settings()
			self.company = self.company or s.company
			self.cost_center = self.cost_center or fleet.cost_center_for(self.vehicle) or s.cost_center
		if self.status == "Rejected" and not self.rejection_reason:
			frappe.throw(_("Enter the rejection reason"))
		if not self.is_new() and self.has_value_changed("status") and self.status != "Pending":
			self.reviewed_by = frappe.session.user

	def on_update(self):
		# Any error here rolls the whole save back, so an expense is never "Approved" without its entry.
		self.sync_journal_entry()
		self.make_fuel_log()

	def sync_journal_entry(self):
		"""Approved -> Dr expense / Cr custody (or Cr accrual when the driver paid personally).
		Moved away from Approved -> the entry is cancelled."""
		if self.status == "Approved" and not self.journal_entry:
			s = fleet.get_settings()
			if not s.post_journal_entries:
				return
			credit = s.custody_account if self.paid_from == "Custody" else s.accrual_account
			debit = s.get(EXPENSE_ACCOUNT[self.category])
			if not credit or not debit:
				frappe.throw(
					_("Set the expense accounts and the credit account in Fleet Settings, or switch off automatic posting."),
					title=_("Accounting Not Configured"),
				)
			je = fleet.post_journal_entry(
				self, debit, self.amount,
				_("Driver expense {0} - {1} - {2}").format(self.name, self.driver, _(self.category)),
				self.expense_date, credit_account=credit,
			)
			if je:
				self.db_set("journal_entry", je)
		elif self.status != "Approved" and self.journal_entry:
			fleet.cancel_linked("Journal Entry", self.journal_entry)
			self.db_set("journal_entry", None)

	def make_fuel_log(self):
		"""An approved fuel expense becomes a draft Fuel Log (consumption statistics), once."""
		if self.status != "Approved" or self.category != "Fuel" or self.fuel_log or not self.odometer:
			return
		try:
			frappe.db.savepoint("lx_driver_fuel")
			fl = frappe.get_doc({
				"doctype": "Fuel Log", "posting_date": self.expense_date, "vehicle": self.vehicle,
				"driver": self.driver, "odometer": self.odometer, "quantity": self.litres,
				"rate": flt(self.amount) / flt(self.litres), "full_tank": 0, "company": self.company,
				"cost_center": self.cost_center, "payment_mode": "Cash", "driver_expense": self.name,
				"station_name": _("Driver expense {0}").format(self.name),
			}).insert(ignore_permissions=True)
			self.db_set("fuel_log", fl.name)
		except Exception:
			frappe.db.rollback(save_point="lx_driver_fuel")
			frappe.log_error(title=f"Driver Expense {self.name}: fuel log", message=frappe.get_traceback())

	def on_trash(self):
		if self.journal_entry:
			frappe.throw(_("Reject this expense first so its journal entry is cancelled"))
