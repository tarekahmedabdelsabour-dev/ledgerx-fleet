import frappe
from frappe import _
from frappe.utils import add_days, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	cond, vals = ["status != 'Renewed'"], {}
	if filters.applies_to:
		cond.append("applies_to = %(applies_to)s")
		vals["applies_to"] = filters.applies_to
	if filters.status:
		cond.append("status = %(status)s")
		vals["status"] = filters.status
	if filters.within_days:
		cond.append("expiry_date <= %(limit)s")
		vals["limit"] = add_days(nowdate(), int(filters.within_days))
	columns = [
		{"label": _("Applies To"), "fieldname": "applies_to", "fieldtype": "Data", "width": 90},
		{"label": _("Vehicle"), "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 130},
		{"label": _("Driver"), "fieldname": "driver", "fieldtype": "Link", "options": "Driver", "width": 140},
		{"label": _("Document Type"), "fieldname": "document_type", "fieldtype": "Link", "options": "Fleet Document Type", "width": 170},
		{"label": _("Document No"), "fieldname": "document_no", "fieldtype": "Data", "width": 120},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 100},
		{"label": _("Days Left"), "fieldname": "days_left", "fieldtype": "Int", "width": 90},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Document"), "fieldname": "name", "fieldtype": "Link", "options": "Fleet Document", "width": 130},
	]
	data = frappe.db.sql(
		f"""select name, applies_to, vehicle, driver, document_type, document_no, expiry_date, days_left, status
		from `tabFleet Document` where {' and '.join(cond)} order by expiry_date""",
		vals, as_dict=True,
	)
	for d in data:
		d.applies_to = _(d.applies_to)
		d.status = _(d.status)
	return columns, data
