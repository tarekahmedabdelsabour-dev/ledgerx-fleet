import frappe


def on_update(doc, method=None):
	"""Choosing a service plan on the vehicle creates its schedules."""
	if doc.get("service_plan") and doc.has_value_changed("service_plan"):
		from ledgerx_fleet.fleet_management.doctype.service_plan.service_plan import apply_plan

		apply_plan(doc.service_plan, doc.name)


def get_dashboard_data(data):
	"""Add the fleet records to the 'Connections' panel of the Vehicle form."""
	data.setdefault("non_standard_fieldnames", {})
	data.setdefault("transactions", [])
	# ERPNext's Vehicle is keyed by license_plate; every fleet document points to it through "vehicle"
	for dt in ("Fleet Document", "Fleet Assignment", "Vehicle Tire", "GPS Device", "Service Schedule",
			"Fleet Work Order", "Fuel Log", "Fleet Trip", "Traffic Fine", "Fleet Incident"):
		data["non_standard_fieldnames"][dt] = "vehicle"
	data["transactions"] += [
		{"label": "Fleet", "items": ["Fleet Document", "Fleet Assignment", "Vehicle Tire", "GPS Device"]},
		{"label": "Maintenance", "items": ["Service Schedule", "Fleet Work Order", "Fuel Log"]},
		{"label": "Operations", "items": ["Fleet Trip", "Traffic Fine", "Fleet Incident"]},
	]
	return data
