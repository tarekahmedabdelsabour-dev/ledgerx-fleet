"""Link the CRM app (Frappe CRM, served at /crm) to ERPNext and to the Fleet app.

CRM already ships an ERPNext integration (ERPNext CRM Settings): when a deal reaches a chosen status it
creates the ERPNext Customer. This module
  1. switches that integration on once, with sensible defaults (company, create the customer when a deal is "Won"),
     never overriding what an administrator chose afterwards;
  2. adds two buttons to the CRM deal page: "Create Rental Contract" and "Create Fleet Trip".
Everything is skipped silently when CRM is not installed.
"""
import frappe

SCRIPT_NAME = "LedgerX Fleet actions on CRM Deal"
DONE_KEY = "lx_crm_erpnext_link_done"

FORM_SCRIPT = """class CRMDeal {
	onLoad() {
		if (this.doc.__newDocument) return
		this.doc.trigger('setFleetActions')
	}
	setFleetActions() {
		const go = (target) => {
			call("ledgerx_fleet.api.crm.open_from_deal", { deal: this.doc.name, target: target })
				.then((url) => { if (url) window.open(url, '_blank') })
				.catch((e) => toast.error((e && e.messages && e.messages[0]) || __("Could not create the document")))
		}
		call("ledgerx_fleet.api.crm.can_create_fleet_documents").then((ok) => {
			if (!ok) return
			this.actions.push({ label: __("Create Rental Contract"), onClick: () => go("rental") })
			this.actions.push({ label: __("Create Fleet Trip"), onClick: () => go("trip") })
		})
	}
}
"""


def crm_installed():
	return "crm" in frappe.get_installed_apps() and frappe.db.exists("DocType", "ERPNext CRM Settings")


def ensure_crm_link():
	if not crm_installed():
		return
	_ensure_erpnext_integration()
	_ensure_form_script()


def _ensure_erpnext_integration():
	if frappe.db.get_default(DONE_KEY):
		return  # done once; later changes by the administrator are respected
	s = frappe.get_single("ERPNext CRM Settings")
	if not s.enabled:
		company = frappe.db.get_single_value("Fleet Settings", "company") or frappe.defaults.get_global_default("company")
		if not company:
			return  # try again after the company exists (next migrate)
		s.enabled = 1
		s.erpnext_company = company
		s.create_customer_on_status_change = 1
		if frappe.db.exists("CRM Deal Status", "Won"):
			s.deal_status = "Won"
		s.flags.ignore_permissions = True
		s.save()
	frappe.db.set_default(DONE_KEY, "1")


def _ensure_form_script():
	if not frappe.db.exists("DocType", "CRM Form Script"):
		return
	if frappe.db.exists("CRM Form Script", SCRIPT_NAME):
		frappe.db.set_value("CRM Form Script", SCRIPT_NAME, {"script": FORM_SCRIPT, "enabled": 1})
		return
	frappe.get_doc({
		"doctype": "CRM Form Script", "name": SCRIPT_NAME, "dt": "CRM Deal", "view": "Form",
		"script": FORM_SCRIPT, "enabled": 1, "is_standard": 1,
	}).insert(ignore_permissions=True)
