import frappe
from frappe import _


def execute(filters=None):
	f = frappe._dict(filters or {})
	cond, vals = ["docstatus = 1", "date(actual_end) between %(from_date)s and %(to_date)s"], {
		"from_date": f.from_date, "to_date": f.to_date}
	for k in ("company", "vehicle", "customer"):
		if f.get(k):
			cond.append(f"{k} = %({k})s")
			vals[k] = f[k]
	columns = [
		{"label": _("Fleet Trip"), "fieldname": "name", "fieldtype": "Link", "options": "Fleet Trip", "width": 140},
		{"label": _("Actual End"), "fieldname": "actual_end", "fieldtype": "Datetime", "width": 150},
		{"label": _("Vehicle"), "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 120},
		{"label": _("Driver"), "fieldname": "driver", "fieldtype": "Link", "options": "Driver", "width": 130},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
		{"label": _("Origin"), "fieldname": "origin", "fieldtype": "Data", "width": 110},
		{"label": _("Destination"), "fieldname": "destination", "fieldtype": "Data", "width": 110},
		{"label": _("Distance (km)"), "fieldname": "distance", "fieldtype": "Int", "width": 100},
		{"label": _("Revenue"), "fieldname": "revenue", "fieldtype": "Currency", "width": 110},
		{"label": _("Total Expenses"), "fieldname": "total_expenses", "fieldtype": "Currency", "width": 120},
		{"label": _("Profit"), "fieldname": "profit", "fieldtype": "Currency", "width": 110},
	]
	data = frappe.db.sql(
		f"""select name, actual_end, vehicle, driver, customer, origin, destination, distance, revenue,
		total_expenses, profit from `tabFleet Trip` where {' and '.join(cond)} order by actual_end desc""",
		vals, as_dict=True,
	)
	return columns, data
