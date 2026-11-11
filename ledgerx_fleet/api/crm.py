"""Server side of the fleet buttons on the CRM deal page (see integrations/crm.py)."""
from urllib.parse import urlencode

import frappe
from frappe import _

TARGETS = {"rental": ("Rental Contract", "rental-contract"), "trip": ("Fleet Trip", "fleet-trip")}


@frappe.whitelist()
def can_create_fleet_documents():
	return bool(
		frappe.has_permission("Rental Contract", "create") and frappe.has_permission("Fleet Trip", "create")
	)


def customer_for_deal(deal):
	"""The ERPNext Customer of a CRM Deal; created now when it does not exist yet."""
	from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
		create_customer_from_deal,
		get_local_customer,
	)

	settings = frappe.get_single("ERPNext CRM Settings")
	if not settings.enabled:
		frappe.throw(_("LedgerX is not integrated with the CRM"))
	customer = get_local_customer(deal)
	if not customer:
		customer = create_customer_from_deal(frappe.get_doc("CRM Deal", deal), settings)
	if not customer:
		frappe.throw(_("Could not create the customer"))
	return customer


@frappe.whitelist()
def open_from_deal(deal, target):
	"""Return the desk URL of a new Rental Contract / Fleet Trip prefilled with the deal's customer."""
	if target not in TARGETS:
		frappe.throw(_("Invalid type"))
	doctype, route = TARGETS[target]
	frappe.has_permission(doctype, "create", throw=True)
	frappe.has_permission("CRM Deal", "read", deal, throw=True)
	customer = customer_for_deal(deal)
	query = {"customer": customer, "crm_deal": deal}
	if target == "trip":
		query["trip_type"] = "Customer Haulage"
	return f"/desk/{route}/new?{urlencode(query)}"
