import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ledgerx_fleet.utils import fleet


class DriverCustodyEntry(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))
		s = fleet.get_settings()
		self.company = self.company or s.company
		self.cost_center = self.cost_center or s.cost_center

	def accounts(self, s):
		"""(debit, credit) for this entry type."""
		if self.entry_type == "Advance":  # company hands cash to the driver
			return s.custody_account, s.cash_account
		if self.entry_type == "Return":  # driver hands cash back
			return s.cash_account, s.custody_account
		return s.accrual_account, s.cash_account  # Reimbursement: company repays what the driver paid

	def on_submit(self):
		s = fleet.get_settings()
		if not s.post_journal_entries:
			return
		debit, credit = self.accounts(s)
		if not debit or not credit:
			frappe.throw(
				_("Set the custody, cash and credit accounts in Fleet Settings, or switch off automatic posting."),
				title=_("Accounting Not Configured"),
			)
		je = fleet.post_journal_entry(
			self, debit, self.amount, _("Driver custody {0} - {1} - {2}").format(self.name, self.driver, _(self.entry_type)),
			self.posting_date, credit_account=credit,
		)
		if je:
			self.db_set("journal_entry", je)

	def on_cancel(self):
		fleet.cancel_linked("Journal Entry", self.journal_entry)
