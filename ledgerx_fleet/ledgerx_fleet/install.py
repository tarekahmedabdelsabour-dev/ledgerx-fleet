import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

MODULE = "Fleet Management"
WORKSPACE = "Fleet Management"

ROLES = ("Fleet Manager", "Fleet Operator")

VEHICLE_FIELDS = [
	dict(fieldname="fleet_section", fieldtype="Section Break", label="Fleet Management", insert_after="doors", collapsible=0),
	dict(fieldname="vehicle_type", fieldtype="Link", options="Vehicle Type", label="Vehicle Type",
		insert_after="fleet_section", in_standard_filter=1),
	dict(fieldname="fleet_status", fieldtype="Select", label="Fleet Status", default="Active",
		options="Active\nIn Maintenance\nOn Trip\nRented Out\nOut of Service\nSold",
		insert_after="vehicle_type", in_standard_filter=1, in_list_view=1),
	dict(fieldname="ownership", fieldtype="Select", label="Ownership", options="Owned\nLeased\nRented In",
		insert_after="fleet_status"),
	dict(fieldname="fleet_cost_center", fieldtype="Link", options="Cost Center", label="Fleet Cost Center",
		insert_after="ownership"),
	dict(fieldname="fleet_col_1", fieldtype="Column Break", insert_after="fleet_cost_center"),
	dict(fieldname="current_driver", fieldtype="Link", options="Driver", label="Current Driver",
		insert_after="fleet_col_1", read_only=1, in_standard_filter=1),
	dict(fieldname="service_plan", fieldtype="Link", options="Service Plan", label="Service Plan",
		insert_after="current_driver"),
	dict(fieldname="gps_device", fieldtype="Link", options="GPS Device", label="GPS Device",
		insert_after="service_plan", read_only=1),
	dict(fieldname="engine_no", fieldtype="Data", label="Engine No", insert_after="gps_device"),
	dict(fieldname="model_year", fieldtype="Int", label="Model Year", insert_after="engine_no"),
	dict(fieldname="fleet_section_2", fieldtype="Section Break", label="Capacity", insert_after="model_year"),
	dict(fieldname="tank_capacity", fieldtype="Float", label="Tank Capacity (L)", insert_after="fleet_section_2"),
	dict(fieldname="payload_kg", fieldtype="Float", label="Payload (kg)", insert_after="tank_capacity"),
	dict(fieldname="fleet_col_2", fieldtype="Column Break", insert_after="payload_kg"),
	dict(fieldname="passenger_seats", fieldtype="Int", label="Passenger Seats", insert_after="fleet_col_2"),
	dict(fieldname="fleet_section_3", fieldtype="Section Break", label="Last Known Position", collapsible=1,
		insert_after="passenger_seats"),
	dict(fieldname="last_position_lat", fieldtype="Float", label="Latitude", precision="8", read_only=1,
		insert_after="fleet_section_3"),
	dict(fieldname="last_position_lng", fieldtype="Float", label="Longitude", precision="8", read_only=1,
		insert_after="last_position_lat"),
	dict(fieldname="fleet_col_3", fieldtype="Column Break", insert_after="last_position_lng"),
	dict(fieldname="last_position_time", fieldtype="Datetime", label="Last Seen", read_only=1,
		insert_after="fleet_col_3"),
]

DRIVER_FIELDS = [
	dict(fieldname="fleet_section", fieldtype="Section Break", label="Fleet Management", insert_after="user"),
	dict(fieldname="current_vehicle", fieldtype="Link", options="Vehicle", label="Current Vehicle",
		insert_after="fleet_section", read_only=1),
	dict(fieldname="fleet_col_1", fieldtype="Column Break", insert_after="current_vehicle"),
	dict(fieldname="fleet_cost_center", fieldtype="Link", options="Cost Center", label="Fleet Cost Center",
		insert_after="fleet_col_1"),
]

DEFAULT_DOCUMENT_TYPES = [
	# name, applies_to, mandatory, alert_days, validity_months
	("Vehicle Registration", "Vehicle", 1, 30, 12),
	("Vehicle Insurance", "Vehicle", 1, 30, 12),
	("Technical Inspection", "Vehicle", 1, 30, 12),
	("Operating Card", "Vehicle", 0, 30, 12),
	("Transport Permit", "Vehicle", 0, 30, 12),
	("Driving License", "Driver", 1, 45, 60),
	("Medical Certificate", "Driver", 0, 30, 12),
	("Driver Permit", "Driver", 0, 30, 12),
]

DEFAULT_VEHICLE_TYPES = [
	("Sedan", "Car", "Petrol", 0), ("Van", "Van", "Diesel", 1000), ("Pickup", "Pickup", "Diesel", 1000),
	("Light Truck", "Truck", "Diesel", 3500), ("Heavy Truck", "Truck", "Diesel", 25000),
	("Trailer", "Trailer", "", 30000), ("Minibus", "Bus", "Diesel", 0), ("Bus", "Bus", "Diesel", 0),
]


def check_app_permission():
	if frappe.session.user == "Administrator":
		return True
	roles = set(frappe.get_roles())
	return bool(roles & {"Fleet Manager", "Fleet Operator", "System Manager"})


def after_install():
	_run(ensure_roles)
	_run(ensure_custom_fields)
	_run(seed_defaults)
	_run(setup_desk)
	frappe.clear_cache()


def after_migrate():
	_run(ensure_roles)
	_run(ensure_custom_fields)
	_run(setup_desk)
	frappe.clear_cache()


def _run(fn):
	"""One failing step must never abort install/migrate: log it and continue."""
	try:
		fn()
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title=f"ledgerx_fleet install step failed: {fn.__name__}")


def ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def ensure_custom_fields():
	create_custom_fields({"Vehicle": VEHICLE_FIELDS, "Driver": DRIVER_FIELDS}, update=True)


def seed_defaults():
	"""Run once on install: starter document and vehicle types (edit or delete freely afterwards)."""
	for name, applies_to, mandatory, alert, months in DEFAULT_DOCUMENT_TYPES:
		if not frappe.db.exists("Fleet Document Type", name):
			frappe.get_doc(
				{"doctype": "Fleet Document Type", "type_name": name, "applies_to": applies_to,
					"mandatory": mandatory, "alert_days": alert, "validity_months": months}
			).insert(ignore_permissions=True)
	for name, category, fuel, payload in DEFAULT_VEHICLE_TYPES:
		if not frappe.db.exists("Vehicle Type", name):
			frappe.get_doc(
				{"doctype": "Vehicle Type", "vehicle_type": name, "category": category,
					"default_fuel_type": fuel, "payload_kg": payload}
			).insert(ignore_permissions=True)
	company = frappe.defaults.get_global_default("company")
	if company:
		frappe.db.set_single_value("Fleet Settings", "company", company)


# ---------------------------------------------------------------- desk (workspace, sidebar, tile)
def _sections():
	"""(section title, icon, [(label, doctype or report, kind)])"""
	return [
		("Vehicles and Drivers", "truck", [
			("Vehicle", "Vehicle", "DocType"), ("Driver", "Driver", "DocType"),
			("Fleet Assignment", "Fleet Assignment", "DocType"), ("Vehicle Type", "Vehicle Type", "DocType"),
			("Fleet Document", "Fleet Document", "DocType"), ("Fleet Document Type", "Fleet Document Type", "DocType"),
			("Vehicle Tire", "Vehicle Tire", "DocType"),
		]),
		("Maintenance", "wrench", [
			("Service Plan", "Service Plan", "DocType"), ("Service Schedule", "Service Schedule", "DocType"),
			("Fleet Work Order", "Fleet Work Order", "DocType"), ("Fuel Log", "Fuel Log", "DocType"),
		]),
		("Operations", "route", [
			("Fleet Trip", "Fleet Trip", "DocType"), ("Rental Contract", "Rental Contract", "DocType"),
			("Traffic Fine", "Traffic Fine", "DocType"), ("Fleet Incident", "Fleet Incident", "DocType"),
		]),
		("Tracking", "map-pin", [
			("GPS Device", "GPS Device", "DocType"), ("Fleet GPS Position", "Fleet GPS Position", "DocType"),
		]),
		("Reports", "chart-bar", [
			("Document Expiry", "Document Expiry", "Report"), ("Maintenance Due", "Maintenance Due", "Report"),
			("Vehicle Cost Analysis", "Vehicle Cost Analysis", "Report"),
			("Fuel Consumption", "Fuel Consumption", "Report"), ("Trip Profitability", "Trip Profitability", "Report"),
		]),
		("Setup", "settings", [("Fleet Settings", "Fleet Settings", "DocType")]),
	]


def setup_desk():
	_run(_workspace)
	_run(_sidebar)
	_run(_app_icon)


def _workspace():
	import uuid

	shortcuts = [("Vehicle", "DocType"), ("Fleet Trip", "DocType"), ("Fleet Work Order", "DocType"),
		("Fuel Log", "DocType"), ("Rental Contract", "DocType"), ("Fleet Document", "DocType")]
	content = [{"id": uuid.uuid4().hex[:10], "type": "header",
		"data": {"text": '<span class="h4"><b>Fleet Management</b></span>', "col": 12}}]
	for label, _t in shortcuts:
		content.append({"id": uuid.uuid4().hex[:10], "type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
	content.append({"id": uuid.uuid4().hex[:10], "type": "spacer", "data": {"col": 12}})
	for title, _icon, _items in _sections():
		content.append({"id": uuid.uuid4().hex[:10], "type": "card", "data": {"card_name": title, "col": 4}})

	doc = frappe.get_doc("Workspace", WORKSPACE) if frappe.db.exists("Workspace", WORKSPACE) \
		else frappe.new_doc("Workspace")
	doc.label = WORKSPACE
	doc.title = WORKSPACE
	doc.module = MODULE
	doc.public = 1
	doc.icon = "truck"
	doc.is_hidden = 0
	doc.content = json.dumps(content)
	doc.set("shortcuts", [])
	doc.set("links", [])
	for label, t in shortcuts:
		doc.append("shortcuts", {"label": label, "type": t, "link_to": label, "doc_view": "List"})
	for title, _icon, items in _sections():
		doc.append("links", {"type": "Card Break", "label": title})
		for label, target, kind in items:
			row = {"type": "Link", "label": label, "link_type": kind, "link_to": target, "onboard": 0}
			if kind == "Report":
				row["is_query_report"] = 1
			doc.append("links", row)
	doc.flags.ignore_permissions = True
	doc.save()


def _sidebar():
	if not frappe.db.exists("DocType", "Workspace Sidebar"):
		return  # older Frappe: the classic workspace above is enough
	doc = frappe.get_doc("Workspace Sidebar", WORKSPACE) if frappe.db.exists("Workspace Sidebar", WORKSPACE) \
		else frappe.new_doc("Workspace Sidebar")
	doc.title = WORKSPACE
	doc.header_icon = "truck"
	doc.app = "ledgerx_fleet"
	doc.module = MODULE
	doc.standard = 0
	doc.set("items", [])
	doc.append("items", {"type": "Link", "label": "Home", "link_type": "Workspace", "link_to": WORKSPACE,
		"icon": "house", "child": 0})
	for title, icon, items in _sections():
		doc.append("items", {"type": "Section Break", "label": title, "icon": icon, "indent": 1,
			"collapsible": 1, "keep_closed": 1 if title in ("Tracking", "Setup") else 0})
		for label, target, kind in items:
			doc.append("items", {"type": "Link", "label": label, "link_type": kind, "link_to": target, "child": 1})
	doc.flags.ignore_permissions = True
	doc.save()


def _app_icon():
	if not frappe.db.exists("DocType", "Desktop Icon"):
		return
	label = "Fleet Management"
	doc = frappe.get_doc("Desktop Icon", label) if frappe.db.exists("Desktop Icon", label) \
		else frappe.new_doc("Desktop Icon")
	doc.label = label
	doc.icon_type = "App"
	doc.link_type = "External"
	doc.link = "/desk/fleet-management"
	doc.logo_url = "/assets/ledgerx_fleet/images/fleet.svg"
	doc.app = "ledgerx_fleet"
	doc.standard = 0
	doc.hidden = 0
	doc.flags.ignore_permissions = True
	doc.save()
