"""Shared Frappe-side helpers for Fleet Management."""
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, nowdate

from ledgerx_fleet.utils import logic

DEFAULT_DOC_ALERT_DAYS = 30


def get_settings():
	return frappe.get_cached_doc("Fleet Settings")


# ------------------------------------------------------------------ vehicle helpers
def update_vehicle_odometer(vehicle, odometer):
	"""Raise the stored odometer; it never goes backwards."""
	if not vehicle or odometer is None:
		return
	current = frappe.db.get_value("Vehicle", vehicle, "last_odometer") or 0
	if int(odometer) > int(current):
		frappe.db.set_value("Vehicle", vehicle, "last_odometer", int(odometer), update_modified=False)


def set_vehicle_status(vehicle, status, only_if=None):
	if not vehicle:
		return
	current = frappe.db.get_value("Vehicle", vehicle, "fleet_status")
	if only_if and current not in only_if:
		return
	if current != status:
		frappe.db.set_value("Vehicle", vehicle, "fleet_status", status, update_modified=False)


def vehicle_label(vehicle):
	return frappe.bold(vehicle)


# ------------------------------------------------------------------ documents
def expired_mandatory_documents(applies_to, name, on_date=None):
	"""Names of mandatory document types that have no valid (non-expired) document on `on_date`."""
	on_date = getdate(on_date or nowdate())
	types = frappe.get_all(
		"Fleet Document Type", filters={"applies_to": applies_to, "mandatory": 1}, pluck="name"
	)
	if not types:
		return []
	field = "vehicle" if applies_to == "Vehicle" else "driver"
	valid = set(
		frappe.get_all(
			"Fleet Document",
			filters={field: name, "document_type": ["in", types], "expiry_date": [">=", on_date],
				"status": ["!=", "Renewed"]},
			pluck="document_type",
		)
	)
	return [t for t in types if t not in valid]


def assert_documents_valid(vehicle=None, driver=None, on_date=None):
	if not get_settings().block_expired_documents:
		return
	problems = []
	if vehicle:
		missing = expired_mandatory_documents("Vehicle", vehicle, on_date)
		if missing:
			problems.append(_("Vehicle {0}: {1}").format(vehicle_label(vehicle), ", ".join(_(m) for m in missing)))
	if driver:
		missing = expired_mandatory_documents("Driver", driver, on_date)
		if missing:
			problems.append(_("Driver {0}: {1}").format(frappe.bold(driver), ", ".join(_(m) for m in missing)))
	if problems:
		frappe.throw(
			_("Missing or expired mandatory documents:") + "<br>" + "<br>".join(problems),
			title=_("Documents Not Valid"),
		)


# ------------------------------------------------------------------ availability
def find_conflicts(vehicle, start, end, exclude=None):
	"""Human readable conflicts for `vehicle` between start and end.

	exclude = (doctype, name) of the document being saved.
	Looks at trips, rental contracts and active work orders.
	"""
	if not vehicle or not start:
		return []
	start = logic.to_datetime(start)
	end = logic.to_datetime(end) if end else start + timedelta(days=1)
	out = []
	ex_dt, ex_name = exclude or (None, None)

	trips = frappe.db.sql(
		"""select name, planned_start, planned_end from `tabFleet Trip`
		where docstatus < 2 and status not in ('Completed', 'Cancelled')
		and (vehicle = %(v)s or trailer = %(v)s)
		and planned_start <= %(end)s and ifnull(planned_end, date_add(planned_start, interval 1 day)) >= %(start)s""",
		{"v": vehicle, "start": start, "end": end},
		as_dict=True,
	)
	for t in trips:
		if not (ex_dt == "Fleet Trip" and ex_name == t.name):
			out.append(_("Trip {0} ({1} → {2})").format(t.name, t.planned_start, t.planned_end or "-"))

	rentals = frappe.db.sql(
		"""select c.name, c.from_date, c.to_date from `tabRental Contract` c
		join `tabRental Vehicle` v on v.parent = c.name
		where c.docstatus < 2 and c.status in ('Reserved', 'Active', 'Overdue') and v.vehicle = %(v)s
		and c.from_date <= %(end)s and c.to_date >= %(start)s""",
		{"v": vehicle, "start": start, "end": end},
		as_dict=True,
	)
	for r in rentals:
		if not (ex_dt == "Rental Contract" and ex_name == r.name):
			out.append(_("Rental {0} ({1} → {2})").format(r.name, r.from_date, r.to_date))

	orders = frappe.db.sql(
		"""select name, start_date, completion_date from `tabFleet Work Order`
		where docstatus < 2 and vehicle = %(v)s and status in ('In Progress', 'Waiting Parts')
		and ifnull(start_date, %(sd)s) <= %(ed)s and ifnull(completion_date, '2999-12-31') >= %(sd)s""",
		{"v": vehicle, "sd": start.date(), "ed": end.date()},
		as_dict=True,
	)
	for w in orders:
		if not (ex_dt == "Fleet Work Order" and ex_name == w.name):
			out.append(_("Work Order {0} (in workshop)").format(w.name))
	return out


def assert_vehicle_free(vehicle, start, end, exclude=None, label=None):
	conflicts = find_conflicts(vehicle, start, end, exclude)
	if conflicts:
		frappe.throw(
			_("{0} is not available:").format(frappe.bold(label or vehicle)) + "<br>" + "<br>".join(conflicts),
			title=_("Vehicle Not Available"),
		)


def find_driver_at(vehicle, when):
	"""Driver responsible for `vehicle` at `when` (assignment first, then trip)."""
	when = logic.to_datetime(when)
	d = when.date()
	row = frappe.db.sql(
		"""select driver from `tabFleet Assignment` where vehicle = %s and from_date <= %s
		and (to_date is null or to_date >= %s) order by from_date desc limit 1""",
		(vehicle, d, d),
	)
	if row:
		return row[0][0]
	row = frappe.db.sql(
		"""select driver from `tabFleet Trip` where docstatus < 2 and vehicle = %s and planned_start <= %s
		and ifnull(planned_end, date_add(planned_start, interval 1 day)) >= %s limit 1""",
		(vehicle, when, when),
	)
	return row[0][0] if row else None


def find_rental_at(vehicle, when):
	when = logic.to_datetime(when)
	row = frappe.db.sql(
		"""select c.name, c.customer from `tabRental Contract` c join `tabRental Vehicle` v on v.parent = c.name
		where c.docstatus = 1 and c.status in ('Active', 'Overdue', 'Returned') and v.vehicle = %s
		and c.from_date <= %s and ifnull(c.actual_return, c.to_date) >= %s limit 1""",
		(vehicle, when, when),
	)
	return (row[0][0], row[0][1]) if row else (None, None)


# ------------------------------------------------------------------ accounting
def _is_pl(account):
	return frappe.db.get_value("Account", account, "report_type") == "Profit and Loss"


def post_journal_entry(doc, debit_account, amount, remark, posting_date=None):
	"""Dr expense / Cr accrual account, tagged with the cost center. Returns the Journal Entry name or None."""
	settings = get_settings()
	amount = flt(amount)
	if not settings.post_journal_entries or amount <= 0:
		return None
	credit = settings.accrual_account
	if not debit_account or not credit:
		frappe.throw(
			_("Set the expense accounts and the credit account in Fleet Settings, or switch off automatic posting."),
			title=_("Accounting Not Configured"),
		)
	cc = doc.get("cost_center") or settings.default_cost_center
	rows = []
	for acc, side in ((debit_account, "debit"), (credit, "credit")):
		row = {"account": acc, f"{side}_in_account_currency": amount}
		if cc and _is_pl(acc):
			row["cost_center"] = cc
		rows.append(row)
	je = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"company": doc.company,
			"posting_date": posting_date or nowdate(),
			"user_remark": remark,
			"accounts": rows,
		}
	)
	je.flags.ignore_permissions = True
	je.insert()
	je.submit()
	return je.name


def cancel_linked(doctype, name):
	if not name:
		return
	if frappe.db.get_value(doctype, name, "docstatus") == 1:
		d = frappe.get_doc(doctype, name)
		d.flags.ignore_permissions = True
		d.cancel()


# ------------------------------------------------------------------ notifications
def fleet_manager_users():
	users = frappe.get_all(
		"Has Role", filters={"role": "Fleet Manager", "parenttype": "User"}, pluck="parent"
	)
	if not users:
		return []
	return frappe.get_all(
		"User", filters={"name": ["in", users], "enabled": 1, "user_type": "System User"}, pluck="name"
	)


def alert_recipients():
	emails = set()
	for u in fleet_manager_users():
		email = frappe.db.get_value("User", u, "email")
		if email:
			emails.add(email)
	extra = get_settings().alert_email_recipients or ""
	for e in extra.replace(";", ",").split(","):
		e = e.strip()
		if e:
			emails.add(e)
	return sorted(emails)


def cost_center_for(vehicle):
	return frappe.db.get_value("Vehicle", vehicle, "fleet_cost_center") if vehicle else None
