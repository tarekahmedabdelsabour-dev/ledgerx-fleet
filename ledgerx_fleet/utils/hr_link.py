"""Fleet <-> HR: attendance from the driver screen and a per-kilometre incentive in payroll.

Everything here is best effort and silent: a failure is logged but never blocks the driver from
recording the odometer or an expense.
"""
import frappe
from frappe import _
from frappe.utils import add_days, add_months, flt, get_first_day, get_last_day, get_datetime, getdate, nowdate, time_diff_in_hours


def employee_of(driver):
	"""Employee behind a driver: the Employee field on the driver, else the employee with the same login user."""
	emp = driver.get("employee") if hasattr(driver, "get") else None
	if emp:
		return emp
	user = driver.get("user")
	if user:
		return frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
	return None


def mark_present(employee, date=None):
	"""Present attendance for the day (HR module). Does nothing when one already exists."""
	if not employee or not frappe.db.exists("DocType", "Attendance"):
		return None
	date = getdate(date or nowdate())
	try:
		if frappe.db.exists("Attendance", {"employee": employee, "attendance_date": date, "docstatus": ["<", 2]}):
			return None
		company = frappe.db.get_value("Employee", employee, "company")
		doc = frappe.get_doc({"doctype": "Attendance", "employee": employee, "attendance_date": date,
			"status": "Present", "company": company}).insert(ignore_permissions=True)
		doc.submit()
		return doc.name
	except Exception:
		frappe.log_error(title="LedgerX: attendance from the screen failed")
		return None


def set_hours(employee, date, started_at, ended_at):
	"""Working hours on the day's attendance (submitted record, so a direct update)."""
	try:
		name = frappe.db.get_value("Attendance", {"employee": employee, "attendance_date": getdate(date), "docstatus": 1}, "name")
		if name and started_at and ended_at:
			hours = round(max(0, time_diff_in_hours(get_datetime(ended_at), get_datetime(started_at))), 2)
			frappe.db.set_value("Attendance", name, "working_hours", hours, update_modified=False)
	except Exception:
		frappe.log_error(title="LedgerX: working hours from the screen failed")


def on_day_event(driver, log_type, log):
	employee = employee_of(driver)
	if not employee:
		return
	if log_type == "Start of Day":
		mark_present(employee, log.log_date)
	else:
		start = frappe.db.get_value("Driver Odometer Log", {"driver": driver.name, "log_date": log.log_date,
			"log_type": "Start of Day"}, "logged_at")
		set_hours(employee, log.log_date, start, log.logged_at)


def month_km(driver_name, from_date, to_date):
	r = frappe.db.sql("SELECT COALESCE(SUM(day_distance),0) FROM `tabDriver Odometer Log` WHERE driver=%s "
		"AND log_type='End of Day' AND log_date BETWEEN %s AND %s", (driver_name, from_date, to_date))
	return flt(r[0][0])


def incentive_rate():
	s = frappe.get_cached_doc("Fleet Settings")
	return flt(s.get("incentive_per_km")), s.get("driver_incentive_component")


def create_incentives(from_date, to_date):
	"""Draft Additional Salary per driver: kilometres driven in the period x rate. Skips ones already made."""
	rate, component = incentive_rate()
	if rate <= 0 or not component:
		return []
	made = []
	for d in frappe.get_all("Driver", filters={"status": "Active"}, fields=["name", "employee", "user"]):
		employee = employee_of(d)
		if not employee:
			continue
		amount = round(month_km(d.name, from_date, to_date) * rate, 2)
		if amount <= 0:
			continue
		if frappe.db.exists("Additional Salary", {"employee": employee, "salary_component": component,
				"ref_doctype": "Driver", "ref_docname": d.name, "payroll_date": to_date, "docstatus": ["<", 2]}):
			continue
		company = frappe.db.get_value("Employee", employee, "company")
		doc = frappe.get_doc({"doctype": "Additional Salary", "employee": employee, "salary_component": component,
			"amount": amount, "payroll_date": to_date, "company": company, "overwrite_salary_structure_amount": 1,
			"ref_doctype": "Driver", "ref_docname": d.name}).insert(ignore_permissions=True)
		made.append(doc.name)
	return made


def monthly_incentives():
	"""Scheduler: on the 1st, last month's incentives as drafts for HR to review."""
	last = add_months(getdate(nowdate()), -1)
	create_incentives(get_first_day(last), get_last_day(last))
