import secrets

import frappe
from frappe import _
from frappe.model.document import Document


class FleetSettings(Document):
	def validate(self):
		for f in ("default_alert_days", "service_alert_km", "service_alert_days", "gps_log_retention_days", "max_speed_kmh"):
			if (self.get(f) or 0) < 0:
				frappe.throw(_("{0} cannot be negative").format(_(self.meta.get_label(f))))
		if self.post_journal_entries and not self.accrual_account:
			frappe.throw(_("Set the credit account to post journal entries automatically."))

	def on_update(self):
		frappe.clear_cache(doctype="Fleet Settings")


@frappe.whitelist()
def generate_gps_token():
	frappe.only_for(("System Manager", "Fleet Manager"))
	token = secrets.token_urlsafe(32)
	doc = frappe.get_doc("Fleet Settings")
	doc.gps_api_token = token
	doc.save(ignore_permissions=True)
	return token
