import frappe
from frappe import _

from ledgerx_fleet.utils import logic


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{"label": _("Driver"), "fieldname": "driver", "fieldtype": "Link", "options": "Driver", "width": 170},
		{"label": _("Driver Name"), "fieldname": "driver_name", "fieldtype": "Data", "width": 170},
		{"label": _("Advances"), "fieldname": "advances", "fieldtype": "Currency", "width": 120},
		{"label": _("Returns"), "fieldname": "returns", "fieldtype": "Currency", "width": 110},
		{"label": _("Spent from Custody"), "fieldname": "spent", "fieldtype": "Currency", "width": 140},
		{"label": _("Pending Review"), "fieldname": "pending", "fieldtype": "Currency", "width": 130},
		{"label": _("Custody Balance"), "fieldname": "custody_balance", "fieldtype": "Currency", "width": 140},
		{"label": _("Owed to Driver"), "fieldname": "owed_to_driver", "fieldtype": "Currency", "width": 130},
	]
	dfilter = {"name": filters.driver} if filters.get("driver") else {}
	drivers = frappe.get_all("Driver", filters=dfilter, fields=["name", "full_name"])
	entries, expenses = {}, {}
	for e in frappe.get_all("Driver Custody Entry", filters={"docstatus": 1}, fields=["driver", "entry_type", "amount"]):
		entries.setdefault(e.driver, []).append((e.entry_type, e.amount))
	for x in frappe.get_all("Driver Expense", fields=["driver", "paid_from", "status", "amount"]):
		expenses.setdefault(x.driver, []).append((x.paid_from, x.status, x.amount))
	rows = []
	for d in drivers:
		if d.name not in entries and d.name not in expenses:
			continue
		r = logic.custody_summary(entries.get(d.name, []), expenses.get(d.name, []))
		rows.append({"driver": d.name, "driver_name": d.full_name, **r})
	return columns, rows
