from ledgerx_fleet import __version__ as app_version  # noqa: F401

app_name = "ledgerx_fleet"
app_title = "LedgerX Fleet"
app_publisher = "LedgerX"
app_description = "Fleet management for ERPNext: vehicles, drivers, documents, maintenance, trips, rentals, GPS and accounting"
app_email = "hello@ledgerx.local"
app_license = "mit"

required_apps = ["erpnext", "hrms"]

# Dock icons (same mechanism as HRMS)
app_include_icons = ["/assets/ledgerx_fleet/icons/module-icons.svg"]

# Tile on the desk home screen / apps screen
add_to_apps_screen = [
	{
		"name": "ledgerx_fleet",
		"logo": "/assets/ledgerx_fleet/images/fleet.svg",
		"title": "Fleet Management",
		"route": "/desk/fleet",
		"has_permission": "ledgerx_fleet.install.check_app_permission",
	}
]

# Vehicle form: quick buttons (documents, fuel, work orders, trips...)
doctype_js = {"Vehicle": "public/js/vehicle.js"}

# "Connections" panel on the Vehicle form
override_doctype_dashboards = {"Vehicle": "ledgerx_fleet.overrides.vehicle.get_dashboard_data"}

doc_events = {
	"Vehicle": {"on_update": "ledgerx_fleet.overrides.vehicle.on_update"},
}

after_install = "ledgerx_fleet.install.after_install"
after_migrate = "ledgerx_fleet.install.after_migrate"

scheduler_events = {
	"daily": [
		"ledgerx_fleet.tasks.daily",
	],
	"daily_long": [
		"ledgerx_fleet.tasks.daily_long",
	],
}
