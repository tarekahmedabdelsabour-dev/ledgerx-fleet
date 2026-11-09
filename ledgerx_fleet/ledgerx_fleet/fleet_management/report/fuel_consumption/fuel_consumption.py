import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	cond, vals = ["docstatus = 1", "posting_date between %(from_date)s and %(to_date)s"], {
		"from_date": filters.from_date, "to_date": filters.to_date}
	for f in ("company", "vehicle"):
		if filters.get(f):
			cond.append(f"{f} = %({f})s")
			vals[f] = filters[f]
	columns = [
		{"label": _("Vehicle"), "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": _("Fills"), "fieldname": "fills", "fieldtype": "Int", "width": 70},
		{"label": _("Quantity (L / kWh)"), "fieldname": "liters", "fieldtype": "Float", "width": 130},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		{"label": _("Distance (km)"), "fieldname": "km", "fieldtype": "Int", "width": 110},
		{"label": _("Consumption (L/100 km)"), "fieldname": "avg_consumption", "fieldtype": "Float", "precision": 2, "width": 150},
		{"label": _("Cost per km"), "fieldname": "cost_per_km", "fieldtype": "Currency", "width": 110},
	]
	rows = frappe.db.sql(
		f"""select vehicle, count(*) fills, sum(quantity) liters, sum(amount) amount, sum(distance) km,
		avg(nullif(consumption, 0)) avg_consumption from `tabFuel Log` where {' and '.join(cond)}
		group by vehicle order by amount desc""",
		vals, as_dict=True,
	)
	for r in rows:
		r.cost_per_km = (r.amount / r.km) if r.km else 0
	return columns, rows
