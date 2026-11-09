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
STAMP = "2026-11-09 12:00:00.000000"

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
		("Fleet Trip", "Fleet Trip", "DocType", "route"), ("Rental Contract", "Rental Contract", "DocType", "key-round"),
		("Traffic Fine", "Traffic Fine", "DocType", "triangle-alert"),
		("Fleet Incident", "Fleet Incident", "DocType", "siren"),
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
	"Vehicle Cost Analysis": "Vehicle", "Fuel Consumption": "Fuel Log", "Trip Profitability": "Fleet Trip"}


def dump(path, data):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		json.dump(data, fh, indent=1, ensure_ascii=False, sort_keys=True)
		fh.write("\n")


def scrub(n):
	return n.lower().replace(" ", "_")


def item(label, link_to, link_type, icon="", child=0):
	return {"child": child, "collapsible": 1, "icon": icon, "indent": 0, "keep_closed": 0, "label": label,
		"link_to": link_to, "link_type": link_type, "show_arrow": 0, "type": "Link"}


def section(label, icon, closed=1):
	return {"child": 0, "collapsible": 1, "icon": icon, "indent": 1, "keep_closed": closed, "label": label,
		"link_type": "DocType", "show_arrow": 0, "type": "Section Break"}


def main():
	dock_items, icons = [], []
	for idx, (title, lucide, dock_icon, items, related) in enumerate(MODULES):
		# ---- workspace (landing page of the module)
		content = [{"id": uuid.uuid4().hex[:10], "type": "header",
			"data": {"text": f'<span class="h4"><b>{title}</b></span>', "col": 12}}]
		shortcuts = []
		for label, target, kind, ic in items:
			content.append({"id": uuid.uuid4().hex[:10], "type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
			sc = {"label": label, "link_to": target, "type": kind}
			if kind == "DocType":
				sc["doc_view"] = "List"
			else:
				sc["report_ref_doctype"] = REPORT_DT[target]
			shortcuts.append(sc)
		dump(os.path.join(APP, "fleet_management", "workspace", scrub(title), scrub(title) + ".json"), {
			"charts": [], "content": json.dumps(content), "creation": STAMP, "custom_blocks": [], "docstatus": 0,
			"doctype": "Workspace", "for_user": "", "hide_custom": 1, "icon": lucide, "idx": idx + 1,
			"is_hidden": 0, "label": title, "links": [], "modified": STAMP, "modified_by": "Administrator",
			"module": MODULE, "name": title, "number_cards": [], "owner": "Administrator", "parent_page": "",
			"public": 1, "quick_lists": [], "roles": [], "sequence_id": float(idx + 20), "shortcuts": shortcuts,
			"title": title, "type": "Workspace",
		})
		# ---- sidebar
		sb = [item("Home", title, "Workspace", "house")]
		for label, target, kind, ic in items:
			sb.append(item(label, target, kind, ic))
		if related:
			sb.append(section("Related", "link-2"))
			for label, target, ic in related:
				sb.append(item(label, target, "DocType", ic, child=1))
		dump(os.path.join(APP, "workspace_sidebar", scrub(title) + ".json"), {
			"app": "ledgerx_fleet", "creation": STAMP, "docstatus": 0, "doctype": "Workspace Sidebar",
			"for_user": "", "header_icon": lucide, "idx": idx, "items": sb, "modified": STAMP,
			"modified_by": "Administrator", "name": title, "owner": "Administrator", "title": title,
		})
		# ---- dock entry + child tile of the app folder
		dock_items.append({"added": 0, "hidden": 0, "icon": dock_icon, "link_to": title, "link_type": "Sidebar", "title": title})
		dump(os.path.join(APP, "desktop_icon", scrub(title) + ".json"), {
			"app": "ledgerx_fleet", "creation": STAMP, "docstatus": 0, "doctype": "Desktop Icon", "hidden": 0,
			"icon": lucide, "icon_type": "Link", "idx": idx, "label": title, "link_to": title,
			"link_type": "Workspace Sidebar", "modified": STAMP, "modified_by": "Administrator", "name": title,
			"owner": "Administrator", "parent_icon": APP_LABEL, "restrict_removal": 0, "roles": [], "standard": 1,
		})

	dump(os.path.join(APP, "desktop_icon", "fleet_management.json"), {
		"app": "ledgerx_fleet", "creation": STAMP, "docstatus": 0, "doctype": "Desktop Icon", "hidden": 0,
		"icon_type": "App", "idx": 20, "label": APP_LABEL, "link": APP_ROUTE, "link_type": "External",
		"logo_url": "/assets/ledgerx_fleet/images/fleet.svg", "modified": STAMP, "modified_by": "Administrator",
		"name": APP_LABEL, "owner": "Administrator", "roles": [], "standard": 1,
	})
	dump(os.path.join(APP, "dock", "ledgerx_fleet", "ledgerx_fleet.json"), {
		"app": "ledgerx_fleet", "creation": STAMP, "docstatus": 0, "doctype": "Dock", "idx": 0, "items": dock_items,
	})


if __name__ == "__main__":
	main()
