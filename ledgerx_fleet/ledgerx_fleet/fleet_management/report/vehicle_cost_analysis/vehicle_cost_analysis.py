import frappe
from frappe import _


def _sum(sql, vals, key):
	return {r.vehicle: r[key] or 0 for r in frappe.db.sql(sql, vals, as_dict=True)}


def execute(filters=None):
	f = frappe._dict(filters or {})
	vals = {"from_date": f.from_date, "to_date": f.to_date, "company": f.company or "%", "cc": f.cost_center or "%"}
	vsql = "and vehicle = %(vehicle)s" if f.vehicle else ""
	if f.vehicle:
		vals["vehicle"] = f.vehicle

	fuel = _sum(
		f"""select vehicle, sum(amount) v from `tabFuel Log` where docstatus = 1 {vsql}
		and posting_date between %(from_date)s and %(to_date)s and company like %(company)s
		and ifnull(cost_center, '') like %(cc)s group by vehicle""", vals, "v")
	maint = _sum(
		f"""select vehicle, sum(total_cost) v from `tabFleet Work Order` where docstatus = 1 {vsql}
		and completion_date between %(from_date)s and %(to_date)s and company like %(company)s
		and ifnull(cost_center, '') like %(cc)s group by vehicle""", vals, "v")
	fines = _sum(
		f"""select vehicle, sum(amount) v from `tabTraffic Fine` where status != 'Cancelled'
		and responsibility = 'Company' {vsql} and date(fine_datetime) between %(from_date)s and %(to_date)s
		and company like %(company)s and ifnull(cost_center, '') like %(cc)s group by vehicle""", vals, "v")
	trips = frappe.db.sql(
		f"""select vehicle, sum(revenue) revenue, sum(total_expenses) expenses, sum(distance) km
		from `tabFleet Trip` where docstatus = 1 {vsql} and date(actual_end) between %(from_date)s and %(to_date)s
		and company like %(company)s and ifnull(cost_center, '') like %(cc)s group by vehicle""",
		vals, as_dict=True)
	trips = {t.vehicle: t for t in trips}
	rental = _sum(
		f"""select v.vehicle, sum(v.line_amount + v.extra_km * ifnull(v.extra_km_rate, 0)) v
		from `tabRental Vehicle` v join `tabRental Contract` c on c.name = v.parent
		where c.docstatus = 1 and c.status = 'Returned' {vsql.replace('vehicle =', 'v.vehicle =')}
		and date(c.actual_return) between %(from_date)s and %(to_date)s and c.company like %(company)s
		and ifnull(c.cost_center, '') like %(cc)s group by v.vehicle""", vals, "v")

	vehicles = set(fuel) | set(maint) | set(fines) | set(trips) | set(rental)
	rows = []
	for v in sorted(vehicles):
		t = trips.get(v)
		trip_exp = (t.expenses if t else 0) or 0
		revenue = ((t.revenue if t else 0) or 0) + rental.get(v, 0)
		cost = fuel.get(v, 0) + maint.get(v, 0) + fines.get(v, 0) + trip_exp
		km = (t.km if t else 0) or 0
		rows.append({
			"vehicle": v, "fuel": fuel.get(v, 0), "maintenance": maint.get(v, 0), "fines": fines.get(v, 0),
			"trip_expenses": trip_exp, "total_cost": cost, "revenue": revenue, "net": revenue - cost,
			"km": km, "cost_per_km": (cost / km) if km else 0,
		})
	cur = lambda label, fn, w=120: {"label": _(label), "fieldname": fn, "fieldtype": "Currency", "width": w}
	columns = [
		{"label": _("Vehicle"), "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		cur("Fuel", "fuel"), cur("Maintenance", "maintenance"), cur("Traffic Fine", "fines"),
		cur("Trip Expense", "trip_expenses"), cur("Total Cost", "total_cost"), cur("Revenue", "revenue"),
		cur("Profit", "net"),
		{"label": _("Distance (km)"), "fieldname": "km", "fieldtype": "Int", "width": 110},
		cur("Cost per km", "cost_per_km", 110),
	]
	return columns, rows
