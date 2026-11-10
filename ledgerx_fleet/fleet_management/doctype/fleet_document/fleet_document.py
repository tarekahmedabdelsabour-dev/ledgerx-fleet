import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate

from ledgerx_fleet.utils import logic
from ledgerx_fleet.utils.fleet import DEFAULT_DOC_ALERT_DAYS, get_settings


def alert_days_for(document_type):
	days = frappe.db.get_value("Fleet Document Type", document_type, "alert_days")
	return days or get_settings().default_alert_days or DEFAULT_DOC_ALERT_DAYS


class FleetDocument(Document):
	def validate(self):
		if self.applies_to == "Vehicle":
			self.driver = None
		else:
			self.vehicle = None
		subject = self.vehicle or self.driver
		self.title = f"{self.document_type} - {subject}" if subject else self.document_type
		if self.issue_date and self.expiry_date and logic.to_date(self.expiry_date) < logic.to_date(self.issue_date):
			frappe.throw(_("Expiry Date cannot be before Issue Date"))
		self.refresh_status()

	def refresh_status(self):
		if self.status == "Renewed":
			return
		self.days_left = logic.days_left(self.expiry_date, nowdate())
		self.status = logic.document_status(self.expiry_date, nowdate(), alert_days_for(self.document_type))

	def after_insert(self):
		"""A newer document of the same type for the same subject supersedes older ones."""
		field = "vehicle" if self.applies_to == "Vehicle" else "driver"
		older = frappe.get_all(
			"Fleet Document",
			filters={
				field: self.get(field),
				"document_type": self.document_type,
				"name": ["!=", self.name],
				"expiry_date": ["<", self.expiry_date],
				"status": ["!=", "Renewed"],
			},
			pluck="name",
		)
		for name in older:
			frappe.db.set_value(
				"Fleet Document", name, {"status": "Renewed", "renewed_by": self.name}, update_modified=False
			)
