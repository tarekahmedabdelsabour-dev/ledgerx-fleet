"""Scheduled jobs."""
import frappe
from frappe import _
from frappe.utils import add_days, escape_html, getdate, nowdate

from ledgerx_fleet.utils import fleet, logic

MAX_ROWS = 200


def daily():
	settings = fleet.get_settings()
	_safe(end_finished_assignments)
	_safe(update_document_statuses)
	_safe(update_service_schedules)
	_safe(mark_rentals_overdue)
	if settings.enable_expiry_alerts:
		_safe(send_digest)


def daily_long():
	_safe(purge_gps_positions)


def _safe(fn):
	try:
		fn()
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title=f"Fleet job failed: {fn.__name__}")


def end_finished_assignments():
	from ledgerx_fleet.fleet_management.doctype.fleet_assignment.fleet_assignment import sync_current_driver

	today = nowdate()
	rows = frappe.get_all(
		"Fleet Assignment", filters={"status": "Active", "to_date": ["<", today]}, fields=["name", "vehicle"]
	)
	for r in rows:
		frappe.db.set_value("Fleet Assignment", r.name, "status", "Ended", update_modified=False)
		sync_current_driver(r.vehicle)


def update_document_statuses():
	from ledgerx_fleet.fleet_management.doctype.fleet_document.fleet_document import alert_days_for

	today = nowdate()
	cache = {}
	rows = frappe.get_all(
		"Fleet Document",
		filters={"status": ["!=", "Renewed"]},
		fields=["name", "document_type", "expiry_date", "status", "days_left"],
	)
	for r in rows:
		if r.document_type not in cache:
			cache[r.document_type] = alert_days_for(r.document_type)
		status = logic.document_status(r.expiry_date, today, cache[r.document_type])
		left = logic.days_left(r.expiry_date, today)
		if status != r.status or left != r.days_left:
			frappe.db.set_value("Fleet Document", r.name, {"status": status, "days_left": left}, update_modified=False)


def update_service_schedules():
	from ledgerx_fleet.fleet_management.doctype.service_schedule.service_schedule import refresh_all

	refresh_all()


def mark_rentals_overdue():
	from ledgerx_fleet.fleet_management.doctype.rental_contract.rental_contract import mark_overdue

	mark_overdue()


def purge_gps_positions():
	days = fleet.get_settings().gps_log_retention_days or 0
	if days <= 0:
		return
	cutoff = add_days(nowdate(), -int(days))
	while True:
		frappe.db.sql("delete from `tabFleet GPS Position` where position_time < %s limit 10000", cutoff)
		n = frappe.db.sql("select row_count()")[0][0]
		frappe.db.commit()
		if not n:
			break


# --------------------------------------------------------------------------- digest
def _table(title, headers, rows):
	if not rows:
		return ""
	head = "".join(f"<th style='text-align:start;padding:4px 8px;border-bottom:1px solid #ccc'>{escape_html(h)}</th>" for h in headers)
	body = "".join(
		"<tr>" + "".join(f"<td style='padding:4px 8px'>{escape_html(str(c if c is not None else ''))}</td>" for c in r) + "</tr>"
		for r in rows[:MAX_ROWS]
	)
	more = f"<p>… +{len(rows) - MAX_ROWS}</p>" if len(rows) > MAX_ROWS else ""
	return f"<h3>{escape_html(title)} ({len(rows)})</h3><table style='border-collapse:collapse'><tr>{head}</tr>{body}</table>{more}"


def build_digest():
	docs = frappe.db.sql(
		"""select ifnull(vehicle, driver) subject, document_type, expiry_date, status
		from `tabFleet Document` where status in ('Expired', 'Expiring Soon') order by expiry_date""",
		as_dict=True,
	)
	sched = frappe.db.sql(
		"""select vehicle, task, status, remaining_km, remaining_days from `tabService Schedule`
		where status in ('Overdue', 'Due Soon') order by status, vehicle""",
		as_dict=True,
	)
	fines = frappe.db.sql(
		"""select vehicle, violation, amount, due_date from `tabTraffic Fine`
		where status = 'Unpaid' and due_date is not null and due_date <= %s order by due_date""",
		add_days(nowdate(), 7),
		as_dict=True,
	)
	parts = [
		_table(_("Documents"), [_("Vehicle"), _("Document Type"), _("Expiry Date"), _("Status")],
			[(d.subject, d.document_type, d.expiry_date, _(d.status)) for d in docs]),
		_table(_("Maintenance"), [_("Vehicle"), _("Task"), _("Status"), _("Remaining (km)"), _("Remaining (days)")],
			[(s.vehicle, s.task, _(s.status), s.remaining_km, s.remaining_days) for s in sched]),
		_table(_("Traffic Fine"), [_("Vehicle"), _("Violation"), _("Amount"), _("Due Date")],
			[(f.vehicle, f.violation, f.amount, f.due_date) for f in fines]),
	]
	return "".join(p for p in parts if p), len(docs) + len(sched) + len(fines)


def send_digest():
	html, count = build_digest()
	if not count:
		return
	subject = _("Fleet alerts: {0} items need attention").format(count)
	for user in fleet.fleet_manager_users():
		frappe.get_doc(
			{"doctype": "Notification Log", "for_user": user, "type": "Alert", "subject": subject,
				"email_content": html, "document_type": "Fleet Settings", "document_name": "Fleet Settings"}
		).insert(ignore_permissions=True)
	recipients = fleet.alert_recipients()
	if recipients:
		frappe.sendmail(recipients=recipients, subject=subject, message=html, now=False)
