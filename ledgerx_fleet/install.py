import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

MODULE = "Fleet Management"

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
	_run(ensure_modules)
	_run(ensure_roles)
	_run(ensure_custom_fields)
	_run(seed_defaults)
	frappe.clear_cache()


def after_migrate():
	_run(ensure_modules)
	_run(ensure_roles)
	_run(ensure_custom_fields)
	frappe.clear_cache()


def _run(fn):
	"""One failing step must never abort install/migrate: log it and continue."""
	try:
		fn()
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title=f"ledgerx_fleet install step failed: {fn.__name__}")


MODULES = ["Fleet Management", "Fleet", "Fleet Maintenance", "Fleet Operations", "Fleet Tracking", "Fleet Reports"]


def ensure_modules():
	"""One Module Def per dock icon (each icon in the desk rail is a module, like HR's)."""
	for name in MODULES:
		if not frappe.db.exists("Module Def", name):
			frappe.get_doc({"doctype": "Module Def", "module_name": name, "app_name": "ledgerx_fleet"}).insert(
				ignore_permissions=True
			)


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
