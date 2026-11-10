import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class DriverCustodyEntry(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))
		s = frappe.get_cached_doc("Fleet Settings")
		self.company = self.company or s.company
		self.cost_center = self.cost_center or s.cost_center
