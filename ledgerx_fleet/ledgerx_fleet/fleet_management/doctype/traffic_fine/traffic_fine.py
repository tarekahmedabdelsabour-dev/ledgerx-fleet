import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from ledgerx_fleet.utils import fleet


class TrafficFine(Document):
	def validate(self):
		s = fleet.get_settings()
		if not self.company:
			self.company = s.company
		if not self.cost_center:
			self.cost_center = fleet.cost_center_for(self.vehicle) or s.default_cost_center
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))
		contract, customer = fleet.find_rental_at(self.vehicle, self.fine_datetime)
		if contract and not self.rental_contract:
			self.rental_contract = contract
			self.customer = customer
			if not self.driver:
				self.responsibility = "Customer"
		if not self.driver and self.responsibility != "Customer":
			self.driver = fleet.find_driver_at(self.vehicle, self.fine_datetime)
		if self.deduct_from_salary:
			if self.responsibility != "Driver":
				frappe.throw(_("Salary deduction applies only when the driver is responsible"))
			if not self.driver or not frappe.db.get_value("Driver", self.driver, "employee"):
				frappe.throw(_("The driver must be linked to an Employee to deduct from salary"))
		if self.status == "Paid" and not self.paid_date:
			self.paid_date = nowdate()

	def on_update(self):
		s = fleet.get_settings()
		if self.status == "Paid" and self.responsibility == "Company" and not self.journal_entry:
			je = fleet.post_journal_entry(
				self, s.fine_expense_account, self.amount,
				_("Traffic fine {0} - {1}").format(self.name, self.vehicle), self.paid_date,
			)
			if je:
				self.db_set("journal_entry", je)
		if self.deduct_from_salary and self.status != "Cancelled" and not self.additional_salary:
			self.create_additional_salary(s)

	def create_additional_salary(self, s):
		if not s.fine_salary_component:
			frappe.throw(_("Set 'Salary Component for Fine Deductions' in Fleet Settings"))
		employee = frappe.db.get_value("Driver", self.driver, "employee")
		company = frappe.db.get_value("Employee", employee, "company") or self.company
		doc = frappe.get_doc(
			{
				"doctype": "Additional Salary",
				"employee": employee,
				"salary_component": s.fine_salary_component,
				"amount": self.amount,
				"payroll_date": nowdate(),
				"company": company,
				"currency": frappe.db.get_value("Company", company, "default_currency"),
				"ref_doctype": "Traffic Fine",
				"ref_docname": self.name,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()  # left as a draft: HR reviews and submits it
		self.db_set("additional_salary", doc.name)
		frappe.msgprint(_("Additional Salary {0} created as draft for HR review").format(doc.name), alert=True)

	def on_trash(self):
		if self.additional_salary and frappe.db.get_value("Additional Salary", self.additional_salary, "docstatus") == 1:
			frappe.throw(_("Cancel Additional Salary {0} first").format(self.additional_salary))
