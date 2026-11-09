import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	cond, vals = ["is_active = 1"], {}
	if filters.vehicle:
		cond.append("vehicle = %(vehicle)s")
		vals["vehicle"] = filters.vehicle
	if filters.status:
		cond.append("status = %(status)s")
		vals["status"] = filters.status
	else:
		cond.append("status in ('Overdue', 'Due Soon')")
	columns = [
		{"label": _("Vehicle"), "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 130},
		{"label": _("Task"), "fieldname": "task", "fieldtype": "Data", "width": 200},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("Current Odometer"), "fieldname": "current_odometer", "fieldtype": "Int", "width": 120},
		{"label": _("Next Due Odometer"), "fieldname": "next_due_odometer", "fieldtype": "Int", "width": 130},
		{"label": _("Remaining (km)"), "fieldname": "remaining_km", "fieldtype": "Int", "width": 120},
		{"label": _("Next Due Date"), "fieldname": "next_due_date", "fieldtype": "Date", "width": 110},
		{"label": _("Remaining (days)"), "fieldname": "remaining_days", "fieldtype": "Int", "width": 120},
		{"label": _("Service Schedule"), "fieldname": "name", "fieldtype": "Link", "options": "Service Schedule", "width": 130},
	]
	data = frappe.db.sql(
		f"""select name, vehicle, task, status, current_odometer, next_due_odometer, remaining_km,
		next_due_date, remaining_days from `tabService Schedule` where {' and '.join(cond)}
		order by field(status, 'Overdue', 'Due Soon', 'OK'), remaining_days""",
		vals, as_dict=True,
	)
	for d in data:
		d.status = _(d.status)
	return columns, data
