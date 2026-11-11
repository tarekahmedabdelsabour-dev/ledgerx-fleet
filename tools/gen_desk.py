"""Generate the desk files exactly like HRMS ships them: app tile (Desktop Icon), module rail (Dock),
one Workspace + Workspace Sidebar per module, and the icon sprite.   python3 tools/gen_desk.py"""
import json
import os
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "ledgerx_fleet")
MODULE = "Fleet Management"
APP_LABEL = "Fleet Management"
APP_ROUTE = "/desk/fleet"
STAMP = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")  # newer than the DB copy, or migrate skips the file

# (title, lucide icon, dock icon, [(label, link_to, kind, icon)], [related (label, doctype, icon)])
MODULES = [
	("Fleet", "truck", "fleet-soft", [
		("Vehicle", "Vehicle", "DocType", "car"), ("Driver", "Driver", "DocType", "user-round"),
		("Fleet Assignment", "Fleet Assignment", "DocType", "arrow-left-right"),
		("Fleet Document", "Fleet Document", "DocType", "file-badge"),
		("Fleet Document Type", "Fleet Document Type", "DocType", "files"),
		("Vehicle Type", "Vehicle Type", "DocType", "tags"), ("Vehicle Tire", "Vehicle Tire", "DocType", "circle-dot"),
		("Document Expiry", "Document Expiry", "Report", "calendar-clock"),
	], [("Employee", "Employee", "square-user-round"), ("Company", "Company", "building-2")]),
	("Fleet Maintenance", "wrench", "wrench-soft", [
		("Service Plan", "Service Plan", "DocType", "list-checks"),
		("Service Schedule", "Service Schedule", "DocType", "calendar-check"),
		("Fleet Work Order", "Fleet Work Order", "DocType", "wrench"), ("Fuel Log", "Fuel Log", "DocType", "fuel"),
		("Maintenance Due", "Maintenance Due", "Report", "alarm-clock"),
		("Fuel Consumption", "Fuel Consumption", "Report", "gauge"),
	], [("Item", "Item", "package"), ("Warehouse", "Warehouse", "warehouse"), ("Stock Entry", "Stock Entry", "arrow-right-left"),
		("Supplier", "Supplier", "truck")]),
	("Fleet Operations", "route", "route-soft", [
		("Driver Screen", "/driver", "URL", "smartphone"),
		("Fleet Trip", "Fleet Trip", "DocType", "route"), ("Rental Contract", "Rental Contract", "DocType", "key-round"),
		("Traffic Fine", "Traffic Fine", "DocType", "triangle-alert"),
		("Fleet Incident", "Fleet Incident", "DocType", "siren"),
		("Driver Odometer Log", "Driver Odometer Log", "DocType", "gauge"),
		("Driver Expense", "Driver Expense", "DocType", "receipt"),
		("Driver Custody Entry", "Driver Custody Entry", "DocType", "wallet"),
		("Driver Custody", "Driver Custody", "Report", "banknote"),
		("Trip Profitability", "Trip Profitability", "Report", "trending-up"),
	], [("Customer", "Customer", "users"), ("Sales Invoice", "Sales Invoice", "receipt"),
		("Additional Salary", "Additional Salary", "wallet")]),
	("Fleet Tracking", "map-pin", "pin-soft", [
		("GPS Device", "GPS Device", "DocType", "satellite-dish"),
		("Fleet GPS Position", "Fleet GPS Position", "DocType", "map-pinned"),
	], []),
	("Fleet Reports", "chart-bar", "chart-soft", [
		("Vehicle Cost Analysis", "Vehicle Cost Analysis", "Report", "chart-no-axes-combined"),
		("Fuel Consumption", "Fuel Consumption", "Report", "gauge"),
		("Trip Profitability", "Trip Profitability", "Report", "trending-up"),
		("Document Expiry", "Document Expiry", "Report", "calendar-clock"),
		("Maintenance Due", "Maintenance Due", "Report", "alarm-clock"),
		("Fleet Settings", "Fleet Settings", "DocType", "settings"),
	], [("Journal Entry", "Journal Entry", "book-open"), ("Account", "Account", "landmark"),
		("Cost Center", "Cost Center", "network")]),
]

REPORT_DT = {"Document Expiry": "Fleet Document", "Maintenance Due": "Service Schedule",
	"Vehicle Cost Analysis": "Vehicle", "Fuel Consumption": "Fuel Log", "Trip Profitability": "Fleet Trip", "Driver Custody": "Driver Expense"}


def dump(path, data):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		json.dump(data, fh, indent=1, ensure_ascii=False, sort_keys=True)
		fh.write("\n")


def scrub(n):
	return n.lower().replace(" ", "_")


def item(label, link_to, link_type, icon="", child=0):
	if link_type == "URL":
		return {"child": child, "collapsible": 1, "icon": icon, "indent": 0, "keep_closed": 0, "label": label,
			"url": link_to, "link_type": "URL", "show_arrow": 0, "type": "Link"}
	return {"child": child, "collapsible": 1, "icon": icon, "indent": 0, "keep_closed": 0, "label": label,
		"link_to": link_to, "link_type": link_type, "show_arrow": 0, "type": "Link"}


def section(label, icon, closed=1):
	return {"child": 0, "collapsible": 1, "icon": icon, "indent": 1, "keep_closed": closed, "label": label,
		"link_type": "DocType", "show_arrow": 0, "type": "Section Break"}


# ---------------------------------------------------------------- dashboards
def _f(*rows):
	return json.dumps([list(r) for r in rows])


# name: (doctype, filters, function, sum_field)
CARDS = {
	"Active Vehicles": ("Vehicle", _f(("Vehicle", "fleet_status", "=", "Active")), "Count", None),
	"Vehicles In Maintenance": ("Vehicle", _f(("Vehicle", "fleet_status", "=", "In Maintenance")), "Count", None),
	"Expired Documents": ("Fleet Document", _f(("Fleet Document", "status", "=", "Expired")), "Count", None),
	"Documents Expiring Soon": ("Fleet Document", _f(("Fleet Document", "status", "=", "Expiring Soon")), "Count", None),
	"Overdue Services": ("Service Schedule", _f(("Service Schedule", "status", "=", "Overdue")), "Count", None),
	"Services Due Soon": ("Service Schedule", _f(("Service Schedule", "status", "=", "Due Soon")), "Count", None),
	"Open Work Orders": ("Fleet Work Order", _f(("Fleet Work Order", "status", "in", ["Open", "In Progress", "Waiting Parts"]), ("Fleet Work Order", "docstatus", "<", 2)), "Count", None),
	"Fuel Cost This Month": ("Fuel Log", _f(("Fuel Log", "docstatus", "=", 1), ("Fuel Log", "posting_date", "Timespan", "this month")), "Sum", "amount"),
	"Trips In Progress": ("Fleet Trip", _f(("Fleet Trip", "status", "in", ["Dispatched", "In Transit"]), ("Fleet Trip", "docstatus", "<", 2)), "Count", None),
	"Active Rentals": ("Rental Contract", _f(("Rental Contract", "status", "in", ["Active", "Overdue"]), ("Rental Contract", "docstatus", "=", 1)), "Count", None),
	"Unpaid Fines": ("Traffic Fine", _f(("Traffic Fine", "status", "=", "Unpaid")), "Count", None),
	"Open Incidents": ("Fleet Incident", _f(("Fleet Incident", "status", "not in", ["Claim Settled", "Closed"])), "Count", None),
	"Active GPS Devices": ("GPS Device", _f(("GPS Device", "status", "=", "Active")), "Count", None),
}

# name: (doctype, kind, type, filters, group_by_or_(based_on,value_field), timespan)
CHARTS = {
	"Vehicles by Status": ("Vehicle", "Group By", "Donut", _f(), "fleet_status"),
	"Documents by Status": ("Fleet Document", "Group By", "Donut", _f(), "status"),
	"Work Orders by Status": ("Fleet Work Order", "Group By", "Donut", _f(("Fleet Work Order", "docstatus", "<", 2)), "status"),
	"Maintenance Cost per Month": ("Fleet Work Order", "Sum", "Bar", _f(("Fleet Work Order", "docstatus", "=", 1)), ("completion_date", "total_cost")),
	"Fuel Cost per Month": ("Fuel Log", "Sum", "Bar", _f(("Fuel Log", "docstatus", "=", 1)), ("posting_date", "amount")),
	"Trip Revenue per Month": ("Fleet Trip", "Sum", "Line", _f(("Fleet Trip", "docstatus", "=", 1)), ("planned_start", "revenue")),
	"Trips by Status": ("Fleet Trip", "Group By", "Donut", _f(("Fleet Trip", "docstatus", "<", 2)), "status"),
}

DASH = {
	"Fleet": (["Active Vehicles", "Vehicles In Maintenance", "Expired Documents", "Documents Expiring Soon"], ["Vehicles by Status", "Documents by Status"]),
	"Fleet Maintenance": (["Overdue Services", "Services Due Soon", "Open Work Orders", "Fuel Cost This Month"], ["Maintenance Cost per Month", "Fuel Cost per Month"]),
	"Fleet Operations": (["Trips In Progress", "Active Rentals", "Unpaid Fines", "Open Incidents"], ["Trip Revenue per Month", "Trips by Status"]),
	"Fleet Tracking": (["Active GPS Devices"], []),
	"Fleet Reports": (["Fuel Cost This Month", "Expired Documents", "Overdue Services", "Unpaid Fines"], ["Maintenance Cost per Month", "Trip Revenue per Month"]),
}


def write_dashboards():
	for name, (dt, flt, fn, field) in CARDS.items():
		card = {"creation": STAMP, "docstatus": 0, "doctype": "Number Card", "document_type": dt, "filters_json": flt,
			"function": fn, "idx": 0, "is_public": 1, "is_standard": 1, "label": name, "modified": STAMP,
			"modified_by": "Administrator", "module": MODULE, "name": name, "owner": "Administrator",
			"show_percentage_stats": 1, "stats_time_interval": "Monthly", "type": "Document Type"}
		if field:
			card["aggregate_function_based_on"] = field
		dump(os.path.join(APP, "fleet_management", "number_card", scrub(name), scrub(name) + ".json"), card)
	for name, (dt, kind, typ, flt, spec) in CHARTS.items():
		ch = {"chart_name": name, "chart_type": kind, "creation": STAMP, "docstatus": 0, "doctype": "Dashboard Chart",
			"document_type": dt, "dynamic_filters_json": "", "filters_json": flt, "idx": 0, "is_public": 1,
			"is_standard": 1, "modified": STAMP, "modified_by": "Administrator", "module": MODULE, "name": name,
			"number_of_groups": 0, "owner": "Administrator", "type": typ, "use_report_chart": 0, "y_axis": []}
		if kind == "Group By":
			ch.update({"group_by_based_on": spec, "group_by_type": "Count", "timeseries": 0})
		else:
			ch.update({"based_on": spec[0], "value_based_on": spec[1], "timeseries": 1, "timespan": "Last Year",
				"time_interval": "Monthly"})
		dump(os.path.join(APP, "fleet_management", "dashboard_chart", scrub(name), scrub(name) + ".json"), ch)


def main():
	write_dashboards()
	dock_items, icons = [], []
	for idx, (title, lucide, dock_icon, items, related) in enumerate(MODULES):
		# ---- workspace (landing page of the module)
		content = [{"id": uuid.uuid4().hex[:10], "type": "header",
			"data": {"text": f'<span class="h4"><b>{title}</b></span>', "col": 12}}]
		cards, charts = DASH.get(title, ([], []))
		for c in charts:
			content.append({"id": uuid.uuid4().hex[:10], "type": "chart", "data": {"chart_name": c, "col": 6}})
		for c in cards:
			content.append({"id": uuid.uuid4().hex[:10], "type": "number_card", "data": {"number_card_name": c, "col": 3}})
		shortcuts = []
		for label, target, kind, ic in items:
			content.append({"id": uuid.uuid4().hex[:10], "type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
			sc = {"label": label, "link_to": target, "type": kind}
			if kind == "URL":
				sc = {"label": label, "url": target, "type": "URL"}
			elif kind == "DocType":
				sc["doc_view"] = "List"
			else:
				sc["report_ref_doctype"] = REPORT_DT[target]
			shortcuts.append(sc)
		mod = os.path.join(APP, scrub(title))
		os.makedirs(mod, exist_ok=True)
		open(os.path.join(mod, "__init__.py"), "a").close()
		dump(os.path.join(mod, "workspace", scrub(title), scrub(title) + ".json"), {
			"charts": [{"chart_name": c, "label": c} for c in charts], "content": json.dumps(content), "creation": STAMP, "custom_blocks": [], "docstatus": 0,
			"doctype": "Workspace", "for_user": "", "hide_custom": 1, "icon": lucide, "idx": idx + 1,
			"is_hidden": 0, "label": title, "links": [], "modified": STAMP, "modified_by": "Administrator",
			"module": title, "name": title, "number_cards": [{"label": c, "number_card_name": c} for c in cards], "owner": "Administrator", "parent_page": "",
			"public": 1, "quick_lists": [], "roles": [], "sequence_id": float(idx + 20), "shortcuts": shortcuts,
			"title": title, "type": "Workspace",
		})
		# ---- sidebar (frappe 16.5x: a standard `Sidebar` rooted at the app, owned by the module)
		sb = [item("Home", title, "Workspace", "house")]
		for label, target, kind, ic in items:
			sb.append(item(label, target, kind, ic))
		if related:
			sb.append(section("Related", "link-2"))
			for label, target, ic in related:
				sb.append(item(label, target, "DocType", ic, child=1))
		for i, it in enumerate(sb, start=1):
			it.update({"doctype": "Sidebar Item", "parentfield": "items", "parenttype": "Sidebar", "idx": i})
		dump(os.path.join(APP, "sidebar", scrub(title), scrub(title) + ".json"), {
			"doctype": "Sidebar", "name": title, "module": title, "title": title, "header_icon": lucide,
			"app": "ledgerx_fleet", "standard": 1, "items": sb,
		})
		# ---- dock entry
		dock_items.append({"added": 0, "hidden": 0, "icon": dock_icon, "link_to": title, "link_type": "Sidebar", "title": title})

	dump(os.path.join(APP, "dock", "ledgerx_fleet", "ledgerx_fleet.json"), {
		"app": "ledgerx_fleet", "creation": STAMP, "docstatus": 0, "doctype": "Dock", "idx": 0, "items": dock_items,
		"modified": STAMP, "modified_by": "Administrator", "name": "ledgerx_fleet", "owner": "Administrator", "standard": 1,
	})


if __name__ == "__main__":
	main()
