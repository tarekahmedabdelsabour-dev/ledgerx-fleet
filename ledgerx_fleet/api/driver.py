"""Backend of the driver's mobile page (/driver).

Every method works for the logged-in user's own Driver record only (Driver.user = session user);
the driver is never taken from the request. Photos arrive as base64 data URLs and are stored as private files.
"""
import base64
import re

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate, now_datetime

from ledgerx_fleet.utils import logic

MAX_PHOTO_BYTES = 3 * 1024 * 1024
DATA_URL = re.compile(r"^data:image/(jpeg|jpg|png|webp);base64,(.+)$", re.S)


def _driver():
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in"), frappe.AuthenticationError)
	name = frappe.db.get_value("Driver", {"user": frappe.session.user, "status": "Active"}, "name")
	if not name:
		frappe.throw(_("Your user is not linked to an active driver. Ask the fleet manager."), frappe.PermissionError)
	return frappe.get_doc("Driver", name)


def _vehicle_of(driver):
	v = frappe.db.get_value("Fleet Assignment", {"driver": driver.name, "status": "Active"}, "vehicle",
		order_by="from_date desc")
	return v or driver.get("current_vehicle")


def _save_photo(doc, fieldname, data_url, required=False, set_field=True):
	if not data_url:
		if required:
			frappe.throw(_("A photo is required"))
		return
	m = DATA_URL.match(data_url.strip())
	if not m:
		frappe.throw(_("Invalid photo"))
	try:
		content = base64.b64decode(m.group(2), validate=False)
	except Exception:
		frappe.throw(_("Invalid photo"))
	if len(content) > MAX_PHOTO_BYTES:
		frappe.throw(_("Photo is too large"))
	ext = "png" if m.group(1) == "png" else ("webp" if m.group(1) == "webp" else "jpg")
	f = frappe.get_doc({
		"doctype": "File", "file_name": f"{doc.name}-{fieldname}.{ext}", "attached_to_doctype": doc.doctype,
		"attached_to_name": doc.name, "attached_to_field": fieldname if set_field else None, "content": content, "is_private": 1,
	}).insert(ignore_permissions=True)
	if set_field:
		doc.db_set(fieldname, f.file_url, update_modified=False)
	return f


def _summary(driver_name):
	entries = frappe.get_all("Driver Custody Entry", filters={"driver": driver_name}, fields=["entry_type", "amount"])
	exps = frappe.get_all("Driver Expense", filters={"driver": driver_name}, fields=["paid_from", "status", "amount"])
	return logic.custody_summary([(e.entry_type, e.amount) for e in entries], [(e.paid_from, e.status, e.amount) for e in exps])


@frappe.whitelist()
def me():
	d = _driver()
	vehicle = _vehicle_of(d)
	today = nowdate()
	logs = {}
	if vehicle:
		for r in frappe.get_all("Driver Odometer Log", filters={"driver": d.name, "log_date": today},
				fields=["log_type", "odometer", "logged_at", "vehicle", "day_distance"]):
			logs[r.log_type] = r
	info = frappe.db.get_value("Vehicle", vehicle, ["license_plate", "make", "model", "last_odometer"], as_dict=True) if vehicle else None
	expenses = frappe.get_all("Driver Expense", filters={"driver": d.name}, limit=15, order_by="creation desc",
		fields=["name", "expense_date", "category", "amount", "paid_from", "status", "rejection_reason"])
	entries = frappe.get_all("Driver Custody Entry", filters={"driver": d.name}, limit=10, order_by="creation desc",
		fields=["posting_date", "entry_type", "amount", "reference"])
	return {
		"driver": d.name, "driver_name": d.full_name, "vehicle": vehicle, "vehicle_info": info,
		"today": today, "start": logs.get("Start of Day"), "end": logs.get("End of Day"),
		"custody": _summary(d.name), "expenses": expenses, "custody_entries": entries,
		"currency": frappe.db.get_default("currency") or "EGP",
	}


@frappe.whitelist(methods=["POST"])
def log_odometer(log_type, odometer, photo=None, latitude=None, longitude=None, notes=None):
	d = _driver()
	if log_type not in ("Start of Day", "End of Day"):
		frappe.throw(_("Invalid log type"))
	vehicle = _vehicle_of(d)
	if not vehicle:
		frappe.throw(_("No vehicle is assigned to you today"))
	if log_type == "End of Day" and not frappe.db.exists(
		"Driver Odometer Log", {"driver": d.name, "log_date": nowdate(), "log_type": "Start of Day"}):
		frappe.throw(_("Record the start of day first"))
	if not photo:
		frappe.throw(_("Take a photo of the odometer"))
	doc = frappe.get_doc({
		"doctype": "Driver Odometer Log", "driver": d.name, "vehicle": vehicle, "log_date": nowdate(),
		"log_type": log_type, "odometer": cint(odometer), "notes": notes,
		"latitude": flt(latitude) or None, "longitude": flt(longitude) or None, "logged_at": now_datetime(),
	})
	doc.insert(ignore_permissions=True)
	_save_photo(doc, "photo", photo, required=True)
	return {"name": doc.name, "day_distance": doc.day_distance}


@frappe.whitelist(methods=["POST"])
def add_expense(category, amount, paid_from="Custody", litres=None, odometer=None, description=None, photo=None):
	d = _driver()
	vehicle = _vehicle_of(d)
	if not vehicle:
		frappe.throw(_("No vehicle is assigned to you today"))
	if category not in ("Fuel", "Maintenance", "Tires", "Toll", "Parking", "Wash", "Other"):
		frappe.throw(_("Invalid category"))
	if paid_from not in ("Custody", "Personal"):
		frappe.throw(_("Invalid payment source"))
	if not photo:
		frappe.throw(_("Take a photo of the receipt"))
	doc = frappe.get_doc({
		"doctype": "Driver Expense", "driver": d.name, "vehicle": vehicle, "expense_date": nowdate(),
		"category": category, "amount": flt(amount), "paid_from": paid_from,
		"litres": flt(litres) or None, "odometer": cint(odometer) or None, "description": description,
		"status": "Pending",
	})
	doc.insert(ignore_permissions=True)
	_save_photo(doc, "receipt", photo, required=True)
	return {"name": doc.name, "custody": _summary(d.name)}


@frappe.whitelist(methods=["POST"])
def report_incident(incident_type, description, severity="Minor", location=None, photo=None, injuries=0):
	d = _driver()
	vehicle = _vehicle_of(d)
	if not vehicle:
		frappe.throw(_("No vehicle is assigned to you today"))
	if incident_type not in ("Breakdown", "Collision", "Theft", "Fire", "Vandalism", "Injury", "Other"):
		frappe.throw(_("Invalid type"))
	if severity not in ("Minor", "Moderate", "Severe", "Total Loss"):
		frappe.throw(_("Invalid severity"))
	if not (description or "").strip():
		frappe.throw(_("Describe what happened"))
	doc = frappe.get_doc({
		"doctype": "Fleet Incident", "vehicle": vehicle, "driver": d.name, "incident_datetime": now_datetime(),
		"incident_type": incident_type, "severity": severity, "location": location, "description": description,
		"injuries": cint(injuries), "status": "Reported",
	})
	doc.insert(ignore_permissions=True)
	if photo:
		f = _save_photo(doc, "attachments", photo, set_field=False)
		if f:
			doc.append("attachments", {"file": f.file_url, "description": _("Reported from the driver page")})
			doc.save(ignore_permissions=True)
	return {"name": doc.name}
