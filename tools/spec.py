"""Field specs for every Fleet Management DocType. See gen.py."""


def F(fieldname, ftype, label, **o):
	return ("F", fieldname, ftype, label, o)


def S(label="", **o):
	return ("S", label, o)


def C(**o):
	return ("C", o)


def COMPANY(**o):
	d = {"options": "Company"}
	d.update(o)
	return F("company", "Link", "Company", **d)


def COST_CENTER(label="Cost Center", **o):
	return F("cost_center", "Link", label, **{"options": "Cost Center", **o})


FUEL_TYPES = "Petrol\nDiesel\nCNG\nLPG\nElectric\nHybrid"

DOCTYPES = []

# --------------------------------------------------------------------------- settings
DOCTYPES.append(dict(
	name="Fleet Settings", single=True, perms="settings", icon="fa fa-cog",
	fields=[
		S("General"),
		COMPANY(),
		COST_CENTER(label="Default Cost Center"),
		C(),
		F("block_expired_documents", "Check", "Block Expired Mandatory Documents", default=1,
			description="Trips and rentals cannot use a vehicle or driver that has an expired mandatory document."),
		F("max_speed_kmh", "Int", "Speed Limit (km/h)", default=120,
			description="GPS positions above this are flagged as Speeding. 0 = off."),
		S("Alerts"),
		F("enable_expiry_alerts", "Check", "Enable Expiry and Service Alerts", default=1),
		F("default_alert_days", "Int", "Default Alert Days Before Expiry", default=30),
		C(),
		F("alert_email_recipients", "Small Text", "Extra Alert Emails",
			description="Comma separated. Users with the Fleet Manager role are always notified."),
		F("service_alert_km", "Int", "Service Alert Before (km)", default=1000),
		F("service_alert_days", "Int", "Service Alert Before (days)", default=14),
		S("Accounting"),
		F("post_journal_entries", "Check", "Post Journal Entries Automatically",
			description="Fuel, workshop costs and company-paid fines create a Journal Entry on submit."),
		F("accrual_account", "Link", "Credit (Accrual / Cash) Account", options="Account",
			depends_on="post_journal_entries",
			description="Use a non-party account (e.g. Accrued Expenses, Cash). Debit accounts are below."),
		C(),
		F("fuel_expense_account", "Link", "Fuel Expense Account", options="Account", depends_on="post_journal_entries"),
		F("maintenance_expense_account", "Link", "Maintenance Expense Account", options="Account", depends_on="post_journal_entries"),
		F("fine_expense_account", "Link", "Fines Expense Account", options="Account", depends_on="post_journal_entries"),
		F("other_expense_account", "Link", "Other Fleet Expenses Account", options="Account", depends_on="post_journal_entries",
			description="Tolls, parking, washing and other driver expenses."),
		F("custody_account", "Link", "Driver Custody Account", options="Account", depends_on="post_journal_entries",
			description="Asset account holding the cash that drivers carry (e.g. Employee Advances)."),
		F("cash_account", "Link", "Cash / Bank Account for Custody", options="Account", depends_on="post_journal_entries",
			description="Cash or bank account the custody is paid from and returned to."),
		S("Stock and Billing"),
		F("issue_parts_from_stock", "Check", "Issue Spare Parts from Stock"),
		F("default_warehouse", "Link", "Default Parts Warehouse", options="Warehouse", depends_on="issue_parts_from_stock"),
		C(),
		F("trip_item", "Link", "Item for Trip Invoices", options="Item"),
		F("rental_item", "Link", "Item for Rental Invoices", options="Item"),
		F("fine_salary_component", "Link", "Salary Component for Fine Deductions", options="Salary Component"),
		S("GPS / Telematics"),
		F("gps_log_retention_days", "Int", "Keep GPS Positions (days)", default=90),
		C(),
		F("gps_api_token", "Password", "GPS API Token",
			description="Devices or your tracking platform send this token to /api/method/ledgerx_fleet.api.gps.ingest"),
	],
))

# --------------------------------------------------------------------------- masters
DOCTYPES.append(dict(
	name="Vehicle Type", autoname="field:vehicle_type", title_field="vehicle_type", icon="fa fa-truck",
	fields=[
		F("vehicle_type", "Data", "Vehicle Type", reqd=1, unique=1, in_list_view=1),
		F("category", "Select", "Category", in_list_view=1, in_standard_filter=1,
			options="\nCar\nVan\nPickup\nTruck\nTrailer\nBus\nMotorcycle\nHeavy Equipment\nOther"),
		C(),
		F("default_fuel_type", "Select", "Default Fuel Type", options="\n" + FUEL_TYPES),
		F("default_service_plan", "Link", "Default Service Plan", options="Service Plan"),
		S("Capacity"),
		F("tank_capacity", "Float", "Tank Capacity (L)"),
		C(),
		F("payload_kg", "Float", "Payload (kg)"),
		F("passenger_seats", "Int", "Passenger Seats"),
	],
))

DOCTYPES.append(dict(
	name="Service Plan Task", istable=True,
	fields=[
		F("task", "Data", "Task", reqd=1, in_list_view=1),
		F("category", "Select", "Category", in_list_view=1,
			options="Oil and Filters\nBrakes\nTires\nInspection\nElectrical\nBody\nOther"),
		F("interval_km", "Int", "Every (km)", in_list_view=1),
		F("interval_days", "Int", "Every (days)", in_list_view=1),
		F("estimated_cost", "Currency", "Estimated Cost", in_list_view=1),
	],
))

DOCTYPES.append(dict(
	name="Service Plan", autoname="field:plan_name", title_field="plan_name", icon="fa fa-calendar-check-o",
	fields=[
		F("plan_name", "Data", "Plan Name", reqd=1, unique=1, in_list_view=1),
		F("vehicle_type", "Link", "Vehicle Type", options="Vehicle Type", in_list_view=1, in_standard_filter=1),
		C(),
		F("is_active", "Check", "Is Active", default=1),
		S("Tasks"),
		F("tasks", "Table", "Tasks", options="Service Plan Task", reqd=1),
	],
))

DOCTYPES.append(dict(
	name="Fleet Document Type", autoname="field:type_name", title_field="type_name", icon="fa fa-id-card-o",
	fields=[
		F("type_name", "Data", "Document Type", reqd=1, unique=1, in_list_view=1),
		F("applies_to", "Select", "Applies To", reqd=1, default="Vehicle", options="Vehicle\nDriver",
			in_list_view=1, in_standard_filter=1),
		C(),
		F("mandatory", "Check", "Mandatory", in_list_view=1,
			description="An expired mandatory document blocks trips and rentals (see Fleet Settings)."),
		F("alert_days", "Int", "Alert Days Before Expiry", description="0 = use the default in Fleet Settings."),
		F("validity_months", "Int", "Typical Validity (months)",
			description="Used to suggest the expiry date from the issue date."),
	],
))

DOCTYPES.append(dict(
	name="Fleet Document", autoname="format:FDOC-{YYYY}-{#####}", title_field="title", icon="fa fa-file-text-o",
	search_fields="document_type,document_no,vehicle,driver", perms="master",
	fields=[
		F("title", "Data", "Title", read_only=1, hidden=1),
		F("applies_to", "Select", "Applies To", reqd=1, default="Vehicle", options="Vehicle\nDriver",
			in_standard_filter=1),
		F("vehicle", "Link", "Vehicle", options="Vehicle", depends_on="eval:doc.applies_to=='Vehicle'",
			mandatory_depends_on="eval:doc.applies_to=='Vehicle'", in_list_view=1, in_standard_filter=1),
		F("driver", "Link", "Driver", options="Driver", depends_on="eval:doc.applies_to=='Driver'",
			mandatory_depends_on="eval:doc.applies_to=='Driver'", in_list_view=1, in_standard_filter=1),
		C(),
		F("document_type", "Link", "Document Type", options="Fleet Document Type", reqd=1, in_list_view=1,
			in_standard_filter=1),
		F("document_no", "Data", "Document No"),
		F("status", "Select", "Status", options="Active\nExpiring Soon\nExpired\nRenewed", default="Active",
			read_only=1, in_list_view=1, in_standard_filter=1, no_copy=1),
		S("Validity"),
		F("issue_date", "Date", "Issue Date"),
		F("expiry_date", "Date", "Expiry Date", reqd=1, in_list_view=1, search_index=1),
		C(),
		F("days_left", "Int", "Days Left", read_only=1, no_copy=1),
		F("issuer", "Data", "Issuer"),
		F("cost", "Currency", "Cost"),
		S("Attachment"),
		F("attachment", "Attach", "Attachment"),
		C(),
		F("renewed_by", "Link", "Renewed By", options="Fleet Document", read_only=1, no_copy=1),
		F("notes", "Small Text", "Notes"),
	],
))

DOCTYPES.append(dict(
	name="Fleet Assignment", autoname="format:FASN-{YYYY}-{#####}", icon="fa fa-exchange",
	title_field="vehicle", search_fields="vehicle,driver", perms="ops_nosubmit",
	fields=[
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_list_view=1, in_standard_filter=1),
		F("driver", "Link", "Driver", options="Driver", reqd=1, in_list_view=1, in_standard_filter=1),
		F("driver_name", "Data", "Driver Name", fetch_from="driver.full_name", read_only=1),
		C(),
		F("from_date", "Date", "From Date", reqd=1, default="Today", in_list_view=1),
		F("to_date", "Date", "To Date", in_list_view=1, description="Empty = still assigned."),
		F("status", "Select", "Status", options="Active\nEnded", read_only=1, default="Active", in_list_view=1,
			in_standard_filter=1),
		S("Odometer"),
		F("start_odometer", "Int", "Start Odometer"),
		C(),
		F("end_odometer", "Int", "End Odometer"),
		F("notes", "Small Text", "Notes"),
	],
))

DOCTYPES.append(dict(
	name="Vehicle Tire", autoname="field:tire_serial", title_field="tire_serial", icon="fa fa-circle-o",
	search_fields="tire_serial,vehicle,brand",
	fields=[
		F("tire_serial", "Data", "Tire Serial No", reqd=1, unique=1, in_list_view=1),
		F("status", "Select", "Status", options="In Stock\nMounted\nRetired", default="In Stock", in_list_view=1,
			in_standard_filter=1),
		C(),
		F("brand", "Data", "Brand", in_list_view=1),
		F("size", "Data", "Size"),
		F("tire_type", "Select", "Tire Type", options="All Season\nSummer\nWinter\nRetread"),
		S("Mounting"),
		F("vehicle", "Link", "Vehicle", options="Vehicle", in_list_view=1, in_standard_filter=1,
			mandatory_depends_on="eval:doc.status=='Mounted'"),
		F("position", "Select", "Position", in_list_view=1,
			options="\nFront Left\nFront Right\nRear Left\nRear Right\nSpare\nOther",
			mandatory_depends_on="eval:doc.status=='Mounted'"),
		F("mounted_on", "Date", "Mounted On"),
		C(),
		F("mount_odometer", "Int", "Odometer at Mounting"),
		F("removed_on", "Date", "Removed On"),
		F("removal_odometer", "Int", "Odometer at Removal"),
		S("Life"),
		F("purchase_date", "Date", "Purchase Date"),
		F("cost", "Currency", "Cost"),
		C(),
		F("expected_life_km", "Int", "Expected Life (km)", default=60000),
		F("km_run", "Int", "Distance Run (km)", read_only=1),
		F("remaining_km", "Int", "Remaining (km)", read_only=1),
	],
))

DOCTYPES.append(dict(
	name="GPS Device", autoname="field:device_id", title_field="device_id", icon="fa fa-map-marker",
	search_fields="device_id,vehicle,imei",
	fields=[
		F("device_id", "Data", "Device ID", reqd=1, unique=1, in_list_view=1,
			description="The identifier your tracker or platform sends (IMEI, unique ID...)."),
		F("vehicle", "Link", "Vehicle", options="Vehicle", in_list_view=1, in_standard_filter=1),
		F("status", "Select", "Status", options="Active\nInactive", default="Active", in_list_view=1,
			in_standard_filter=1),
		C(),
		F("provider", "Data", "Provider"),
		F("imei", "Data", "IMEI"),
		F("sim_number", "Data", "SIM Number"),
		S("Last Known Position"),
		F("last_seen", "Datetime", "Last Seen", read_only=1, in_list_view=1),
		F("last_latitude", "Float", "Latitude", precision="8", read_only=1),
		F("last_longitude", "Float", "Longitude", precision="8", read_only=1),
		C(),
		F("last_speed", "Float", "Speed (km/h)", read_only=1),
		F("ignition_on", "Check", "Ignition On", read_only=1),
	],
))

DOCTYPES.append(dict(
	name="Fleet GPS Position", autoname="hash", icon="fa fa-location-arrow", perms="log",
	title_field="vehicle", sort_field="position_time",
	fields=[
		F("device", "Link", "GPS Device", options="GPS Device", in_standard_filter=1),
		F("vehicle", "Link", "Vehicle", options="Vehicle", in_list_view=1, in_standard_filter=1, search_index=1),
		F("position_time", "Datetime", "Position Time", reqd=1, in_list_view=1, search_index=1),
		C(),
		F("event", "Select", "Event", options="Position\nSpeeding\nIgnition On\nIgnition Off", default="Position",
			in_list_view=1, in_standard_filter=1),
		F("speed", "Float", "Speed (km/h)", in_list_view=1),
		F("heading", "Float", "Heading"),
		S("Location"),
		F("latitude", "Float", "Latitude", precision="8", reqd=1),
		C(),
		F("longitude", "Float", "Longitude", precision="8", reqd=1),
		F("ignition", "Check", "Ignition On"),
		F("odometer", "Float", "Odometer (km)"),
	],
))

# --------------------------------------------------------------------------- maintenance
DOCTYPES.append(dict(
	name="Service Schedule", autoname="format:SCH-{#####}", title_field="task", icon="fa fa-clock-o",
	search_fields="vehicle,task", perms="ops_nosubmit",
	fields=[
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_list_view=1, in_standard_filter=1),
		F("task", "Data", "Task", reqd=1, in_list_view=1),
		F("category", "Select", "Category",
			options="Oil and Filters\nBrakes\nTires\nInspection\nElectrical\nBody\nOther"),
		C(),
		F("status", "Select", "Status", options="OK\nDue Soon\nOverdue\nDisabled", default="OK", read_only=1,
			in_list_view=1, in_standard_filter=1),
		F("is_active", "Check", "Is Active", default=1),
		F("source_plan", "Link", "Service Plan", options="Service Plan"),
		S("Interval"),
		F("interval_km", "Int", "Every (km)"),
		F("interval_days", "Int", "Every (days)"),
		C(),
		F("last_service_date", "Date", "Last Service Date"),
		F("last_service_odometer", "Int", "Last Service Odometer"),
		F("last_work_order", "Link", "Last Work Order", options="Fleet Work Order", read_only=1),
		S("Next Due"),
		F("next_due_date", "Date", "Next Due Date", read_only=1, in_list_view=1),
		F("next_due_odometer", "Int", "Next Due Odometer", read_only=1, in_list_view=1),
		C(),
		F("current_odometer", "Int", "Current Odometer", read_only=1),
		F("remaining_km", "Int", "Remaining (km)", read_only=1),
		F("remaining_days", "Int", "Remaining (days)", read_only=1),
	],
))

DOCTYPES.append(dict(
	name="Work Order Task", istable=True,
	fields=[
		F("description", "Small Text", "Description", reqd=1, in_list_view=1),
		F("schedule", "Link", "Service Schedule", options="Service Schedule", in_list_view=1),
		F("task_cost", "Currency", "Cost", in_list_view=1),
		F("done", "Check", "Done", in_list_view=1),
	],
))

DOCTYPES.append(dict(
	name="Work Order Part", istable=True,
	fields=[
		F("item_code", "Link", "Item", options="Item", reqd=1, in_list_view=1),
		F("item_name", "Data", "Item Name", fetch_from="item_code.item_name", read_only=1),
		F("qty", "Float", "Qty", reqd=1, default=1, in_list_view=1),
		F("rate", "Currency", "Rate", in_list_view=1),
		F("amount", "Currency", "Amount", read_only=1, in_list_view=1),
		F("warehouse", "Link", "Warehouse", options="Warehouse"),
	],
))

DOCTYPES.append(dict(
	name="Fleet Work Order", autoname="format:FWO-{YYYY}-{#####}", title_field="vehicle", icon="fa fa-wrench",
	search_fields="vehicle,work_type,status", submittable=True, perms="ops",
	fields=[
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_list_view=1, in_standard_filter=1),
		F("odometer", "Int", "Odometer", in_list_view=0),
		F("work_type", "Select", "Work Type", reqd=1, default="Preventive", in_list_view=1, in_standard_filter=1,
			options="Preventive\nCorrective\nInspection\nTire\nBody"),
		F("priority", "Select", "Priority", options="Low\nMedium\nHigh\nUrgent", default="Medium", in_standard_filter=1),
		C(),
		F("status", "Select", "Status", options="Open\nIn Progress\nWaiting Parts\nCompleted\nCancelled",
			default="Open", in_list_view=1, in_standard_filter=1, allow_on_submit=0),
		F("open_date", "Date", "Open Date", default="Today", reqd=1),
		F("start_date", "Date", "Start Date"),
		F("completion_date", "Date", "Completion Date", mandatory_depends_on="eval:doc.docstatus==1"),
		S("Workshop"),
		F("workshop_type", "Select", "Workshop", options="Internal\nExternal", default="Internal"),
		F("supplier", "Link", "Supplier", options="Supplier", depends_on="eval:doc.workshop_type=='External'"),
		C(),
		F("reported_by", "Data", "Reported By"),
		F("incident", "Link", "Incident", options="Fleet Incident"),
		F("problem", "Small Text", "Problem / Request"),
		S("Tasks"),
		F("tasks", "Table", "Tasks", options="Work Order Task"),
		S("Spare Parts"),
		F("parts", "Table", "Parts", options="Work Order Part"),
		S("Costs"),
		F("parts_cost", "Currency", "Parts Cost", read_only=1),
		F("labor_cost", "Currency", "Labor Cost"),
		C(),
		F("other_cost", "Currency", "Other Cost"),
		F("total_cost", "Currency", "Total Cost", read_only=1, in_list_view=1),
		S("Accounting", collapsible=1),
		COMPANY(),
		COST_CENTER(),
		C(),
		F("journal_entry", "Link", "Journal Entry", options="Journal Entry", read_only=1, no_copy=1),
		F("stock_entry", "Link", "Stock Entry", options="Stock Entry", read_only=1, no_copy=1),
		F("notes", "Text", "Notes"),
		F("amended_from", "Link", "Amended From", options="Fleet Work Order", read_only=1, no_copy=1, print_hide=1),
	],
))

# --------------------------------------------------------------------------- fuel
DOCTYPES.append(dict(
	name="Fuel Log", autoname="format:FUEL-{YYYY}-{#####}", title_field="vehicle", icon="fa fa-tint",
	search_fields="vehicle,driver,station_name", submittable=True, perms="ops",
	fields=[
		F("posting_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_list_view=1, in_standard_filter=1),
		F("driver", "Link", "Driver", options="Driver", in_standard_filter=1),
		C(),
		F("odometer", "Int", "Odometer", reqd=1, in_list_view=1),
		F("last_odometer", "Int", "Last Odometer", read_only=1, no_copy=1),
		F("distance", "Int", "Distance Since Last Fill", read_only=1, no_copy=1),
		S("Fuel"),
		F("fuel_type", "Select", "Fuel Type", options=FUEL_TYPES),
		F("quantity", "Float", "Quantity (L / kWh)", reqd=1, in_list_view=1),
		F("rate", "Currency", "Rate", reqd=1),
		C(),
		F("amount", "Currency", "Amount", read_only=1, in_list_view=1),
		F("full_tank", "Check", "Full Tank", default=1,
			description="Consumption is calculated between two full-tank fills."),
		F("consumption", "Float", "Consumption (L/100 km)", read_only=1, no_copy=1, precision="2"),
		S("Station and Payment"),
		F("station_name", "Data", "Station"),
		F("payment_mode", "Select", "Payment Mode", options="Cash\nFuel Card\nCard\nCredit", default="Cash"),
		C(),
		F("receipt", "Attach", "Receipt"),
		S("Accounting", collapsible=1),
		COMPANY(),
		COST_CENTER(),
		C(),
		F("journal_entry", "Link", "Journal Entry", options="Journal Entry", read_only=1, no_copy=1),
		F("driver_expense", "Link", "Driver Expense", options="Driver Expense", read_only=1, no_copy=1,
			description="Set when this log came from an approved driver expense; that expense posts the accounting entry."),
		F("amended_from", "Link", "Amended From", options="Fuel Log", read_only=1, no_copy=1, print_hide=1),
	],
))

# --------------------------------------------------------------------------- operations
DOCTYPES.append(dict(
	name="Trip Expense", istable=True,
	fields=[
		F("expense_type", "Select", "Expense Type", reqd=1, in_list_view=1,
			options="Toll\nParking\nDriver Allowance\nLoading and Unloading\nOther"),
		F("description", "Data", "Description", in_list_view=1),
		F("amount", "Currency", "Amount", reqd=1, in_list_view=1),
		F("receipt", "Attach", "Receipt"),
	],
))

DOCTYPES.append(dict(
	name="Fleet Trip", autoname="format:TRIP-{YYYY}-{#####}", title_field="vehicle", icon="fa fa-road",
	search_fields="vehicle,driver,customer,origin,destination", submittable=True, perms="ops",
	fields=[
		F("trip_type", "Select", "Trip Type", options="Internal\nCustomer Haulage", default="Internal",
			reqd=1, in_standard_filter=1),
		F("customer", "Link", "Customer", options="Customer", depends_on="eval:doc.trip_type=='Customer Haulage'",
			mandatory_depends_on="eval:doc.trip_type=='Customer Haulage'", in_list_view=1, in_standard_filter=1),
		F("status", "Select", "Status", options="Planned\nDispatched\nIn Transit\nCompleted\nCancelled",
			default="Planned", read_only=1, in_list_view=1, in_standard_filter=1, no_copy=1),
		C(),
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_list_view=1, in_standard_filter=1),
		F("trailer", "Link", "Trailer", options="Vehicle"),
		F("driver", "Link", "Driver", options="Driver", reqd=1, in_list_view=1, in_standard_filter=1),
		S("Route"),
		F("origin", "Data", "Origin", reqd=1),
		F("destination", "Data", "Destination", reqd=1),
		C(),
		F("planned_start", "Datetime", "Planned Start", reqd=1),
		F("planned_end", "Datetime", "Planned End"),
		F("actual_start", "Datetime", "Actual Start", no_copy=1),
		F("actual_end", "Datetime", "Actual End", no_copy=1, mandatory_depends_on="eval:doc.docstatus==1"),
		S("Odometer"),
		F("start_odometer", "Int", "Start Odometer"),
		F("end_odometer", "Int", "End Odometer", no_copy=1, mandatory_depends_on="eval:doc.docstatus==1"),
		C(),
		F("distance", "Int", "Distance (km)", read_only=1, no_copy=1),
		S("Cargo"),
		F("cargo_description", "Small Text", "Cargo Description"),
		C(),
		F("cargo_weight_kg", "Float", "Cargo Weight (kg)"),
		S("Revenue", depends_on="eval:doc.trip_type=='Customer Haulage'"),
		F("billable", "Check", "Billable", default=1),
		F("rate_basis", "Select", "Rate Basis", options="Fixed\nPer Km\nPer Ton", default="Fixed"),
		C(),
		F("rate", "Currency", "Rate"),
		F("revenue", "Currency", "Revenue", read_only=1, in_list_view=1),
		S("Expenses"),
		F("expenses", "Table", "Expenses", options="Trip Expense"),
		F("total_expenses", "Currency", "Total Expenses", read_only=1),
		C(),
		F("profit", "Currency", "Profit", read_only=1),
		S("Accounting", collapsible=1),
		COMPANY(),
		COST_CENTER(),
		C(),
		F("sales_invoice", "Link", "Sales Invoice", options="Sales Invoice", read_only=1, no_copy=1),
		F("crm_deal", "Data", "CRM Deal", read_only=1, no_copy=1,
			description="The CRM deal this was created from."),
		F("amended_from", "Link", "Amended From", options="Fleet Trip", read_only=1, no_copy=1, print_hide=1),
	],
))

DOCTYPES.append(dict(
	name="Traffic Fine", autoname="format:FINE-{YYYY}-{#####}", title_field="vehicle", icon="fa fa-ticket",
	search_fields="vehicle,driver,fine_number,violation", perms="ops_nosubmit",
	fields=[
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_list_view=1, in_standard_filter=1),
		F("fine_datetime", "Datetime", "Violation Date and Time", reqd=1, in_list_view=1),
		F("violation", "Data", "Violation", reqd=1, in_list_view=1),
		C(),
		F("status", "Select", "Status", options="Unpaid\nPaid\nAppealed\nCancelled", default="Unpaid",
			in_list_view=1, in_standard_filter=1),
		F("amount", "Currency", "Amount", reqd=1, in_list_view=1),
		F("due_date", "Date", "Due Date"),
		F("paid_date", "Date", "Paid Date", mandatory_depends_on="eval:doc.status=='Paid'"),
		S("Details"),
		F("fine_number", "Data", "Fine Number"),
		F("authority", "Data", "Issuing Authority"),
		F("location", "Data", "Location"),
		C(),
		F("attachment", "Attach", "Attachment"),
		F("notes", "Small Text", "Notes"),
		S("Responsibility"),
		F("responsibility", "Select", "Responsible", options="Driver\nCompany\nCustomer", default="Company"),
		F("driver", "Link", "Driver", options="Driver", in_standard_filter=1),
		C(),
		F("rental_contract", "Link", "Rental Contract", options="Rental Contract"),
		F("customer", "Link", "Customer", options="Customer"),
		S("Deduction", depends_on="eval:doc.responsibility=='Driver'"),
		F("deduct_from_salary", "Check", "Deduct from Salary"),
		C(),
		F("additional_salary", "Link", "Additional Salary", options="Additional Salary", read_only=1, no_copy=1),
		S("Accounting", collapsible=1),
		COMPANY(),
		COST_CENTER(),
		C(),
		F("journal_entry", "Link", "Journal Entry", options="Journal Entry", read_only=1, no_copy=1),
	],
))

DOCTYPES.append(dict(
	name="Fleet Attachment", istable=True,
	fields=[
		F("file", "Attach", "File", reqd=1, in_list_view=1),
		F("description", "Data", "Description", in_list_view=1),
	],
))

DOCTYPES.append(dict(
	name="Fleet Incident", autoname="format:INC-{YYYY}-{#####}", title_field="vehicle", icon="fa fa-exclamation-triangle",
	search_fields="vehicle,driver,incident_type,police_report_no", perms="ops_nosubmit",
	fields=[
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_list_view=1, in_standard_filter=1),
		F("driver", "Link", "Driver", options="Driver", in_list_view=1, in_standard_filter=1),
		F("incident_datetime", "Datetime", "Date and Time", reqd=1, default="Now", in_list_view=1),
		C(),
		F("status", "Select", "Status", options="Reported\nUnder Review\nClaim Filed\nClaim Settled\nClosed",
			default="Reported", in_list_view=1, in_standard_filter=1),
		F("incident_type", "Select", "Type", reqd=1, in_standard_filter=1,
			options="Collision\nBreakdown\nTheft\nFire\nVandalism\nInjury\nOther"),
		F("severity", "Select", "Severity", options="Minor\nModerate\nSevere\nTotal Loss", default="Minor"),
		S("What Happened"),
		F("location", "Data", "Location"),
		F("fault", "Select", "Fault", options="Unknown\nOur Driver\nThird Party\nShared"),
		C(),
		F("injuries", "Check", "Injuries"),
		F("police_report_no", "Data", "Police Report No"),
		F("description", "Text", "Description"),
		S("Insurance Claim"),
		F("insurer", "Data", "Insurer"),
		F("claim_no", "Data", "Claim No"),
		F("claim_status", "Select", "Claim Status", options="\nNot Filed\nFiled\nApproved\nRejected\nPaid"),
		C(),
		F("claimed_amount", "Currency", "Claimed Amount"),
		F("approved_amount", "Currency", "Approved Amount"),
		F("deductible", "Currency", "Deductible"),
		S("Cost"),
		F("work_orders_cost", "Currency", "Repair Cost (Work Orders)", read_only=1),
		F("other_cost", "Currency", "Other Cost"),
		C(),
		F("net_loss", "Currency", "Net Loss", read_only=1),
		S("Attachments"),
		F("attachments", "Table", "Attachments", options="Fleet Attachment"),
		S("Accounting", collapsible=1),
		COMPANY(),
		COST_CENTER(),
	],
))

# --------------------------------------------------------------------------- rental
DOCTYPES.append(dict(
	name="Rental Vehicle", istable=True,
	fields=[
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_list_view=1),
		F("rate_per_day", "Currency", "Rate per Day", reqd=1, in_list_view=1),
		F("km_included_per_day", "Int", "Km Included per Day", default=0, in_list_view=1,
			description="0 = unlimited"),
		F("extra_km_rate", "Currency", "Extra Km Rate"),
		F("out_odometer", "Int", "Odometer Out"),
		F("in_odometer", "Int", "Odometer In"),
		F("extra_km", "Float", "Extra Km", read_only=1),
		F("line_amount", "Currency", "Amount", read_only=1, in_list_view=1),
	],
))

DOCTYPES.append(dict(
	name="Rental Contract", autoname="format:RENT-{YYYY}-{#####}", title_field="customer_name", icon="fa fa-handshake-o",
	search_fields="customer,customer_name", submittable=True, perms="ops",
	fields=[
		F("customer", "Link", "Customer", options="Customer", reqd=1, in_list_view=1, in_standard_filter=1),
		F("customer_name", "Data", "Customer Name", fetch_from="customer.customer_name", read_only=1),
		F("status", "Select", "Status", options="Reserved\nActive\nOverdue\nReturned\nCancelled", default="Reserved",
			read_only=1, in_list_view=1, in_standard_filter=1, no_copy=1),
		C(),
		F("from_date", "Datetime", "From", reqd=1, in_list_view=1),
		F("to_date", "Datetime", "To", reqd=1, in_list_view=1),
		F("actual_return", "Datetime", "Actual Return", read_only=1, no_copy=1),
		F("chauffeur", "Link", "Chauffeur (optional)", options="Driver"),
		S("Vehicles"),
		F("vehicles", "Table", "Vehicles", options="Rental Vehicle", reqd=1),
		S("Charges"),
		F("days", "Float", "Days", read_only=1),
		F("subtotal", "Currency", "Rental Amount", read_only=1),
		F("extra_km_charges", "Currency", "Extra Km Charges", read_only=1),
		C(),
		F("damage_charges", "Currency", "Damage Charges", read_only=1, no_copy=1),
		F("discount", "Currency", "Discount", read_only=1, no_copy=1),
		F("grand_total", "Currency", "Grand Total", read_only=1, in_list_view=1),
		F("deposit", "Currency", "Deposit"),
		S("Terms", collapsible=1),
		F("terms", "Text", "Terms and Conditions"),
		S("Accounting", collapsible=1),
		COMPANY(),
		COST_CENTER(),
		C(),
		F("sales_invoice", "Link", "Sales Invoice", options="Sales Invoice", read_only=1, no_copy=1),
		F("crm_deal", "Data", "CRM Deal", read_only=1, no_copy=1,
			description="The CRM deal this was created from."),
		F("amended_from", "Link", "Amended From", options="Rental Contract", read_only=1, no_copy=1, print_hide=1),
	],
))

# --------------------------------------------------------------------------- driver app (mobile page /driver)
DOCTYPES.append(dict(
	name="Driver Odometer Log", autoname="format:ODO-{YYYY}-{#####}", title_field="driver", icon="fa fa-tachometer",
	search_fields="driver,vehicle", perms="ops_nosubmit",
	fields=[
		F("driver", "Link", "Driver", options="Driver", reqd=1, in_list_view=1, in_standard_filter=1),
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_list_view=1, in_standard_filter=1),
		F("log_date", "Date", "Date", reqd=1, default="Today", in_list_view=1, in_standard_filter=1),
		C(),
		F("log_type", "Select", "Log Type", options="Start of Day\nEnd of Day", reqd=1, in_list_view=1,
			in_standard_filter=1),
		F("odometer", "Int", "Odometer", reqd=1, in_list_view=1),
		F("day_distance", "Int", "Day Distance (km)", read_only=1, no_copy=1,
			description="Filled on End of Day: end reading minus start reading."),
		S("Proof"),
		F("photo", "Attach Image", "Odometer Photo"),
		F("logged_at", "Datetime", "Logged At", default="Now", read_only=1),
		C(),
		F("latitude", "Float", "Latitude", read_only=1, precision="6"),
		F("longitude", "Float", "Longitude", read_only=1, precision="6"),
		F("notes", "Small Text", "Notes"),
	],
))

DOCTYPES.append(dict(
	name="Driver Expense", autoname="format:DEXP-{YYYY}-{#####}", title_field="driver", icon="fa fa-money",
	search_fields="driver,vehicle,category", perms="ops_nosubmit",
	fields=[
		F("driver", "Link", "Driver", options="Driver", reqd=1, in_list_view=1, in_standard_filter=1),
		F("vehicle", "Link", "Vehicle", options="Vehicle", reqd=1, in_standard_filter=1),
		F("expense_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
		C(),
		F("category", "Select", "Category", reqd=1, in_list_view=1, in_standard_filter=1,
			options="Fuel\nMaintenance\nTires\nToll\nParking\nWash\nOther"),
		F("amount", "Currency", "Amount", reqd=1, in_list_view=1),
		F("paid_from", "Select", "Paid From", options="Custody\nPersonal", default="Custody", reqd=1,
			in_list_view=1, description="Custody = from the cash the company gave the driver. Personal = driver paid from his own pocket."),
		S("Details"),
		F("litres", "Float", "Litres", depends_on="eval:doc.category=='Fuel'",
			mandatory_depends_on="eval:doc.category=='Fuel'"),
		F("odometer", "Int", "Odometer", depends_on="eval:doc.category=='Fuel'"),
		C(),
		F("description", "Small Text", "Description"),
		F("receipt", "Attach Image", "Receipt Photo"),
		S("Review"),
		F("status", "Select", "Status", options="Pending\nApproved\nRejected", default="Pending",
			in_list_view=1, in_standard_filter=1),
		F("reviewed_by", "Link", "Reviewed By", options="User", read_only=1, no_copy=1),
		C(),
		F("rejection_reason", "Small Text", "Rejection Reason", depends_on="eval:doc.status=='Rejected'"),
		F("fuel_log", "Link", "Fuel Log", options="Fuel Log", read_only=1, no_copy=1),
		S("Accounting", collapsible=1),
		COMPANY(),
		COST_CENTER(),
		C(),
		F("journal_entry", "Link", "Journal Entry", options="Journal Entry", read_only=1, no_copy=1),
	],
))

DOCTYPES.append(dict(
	name="Driver Custody Entry", autoname="format:CUS-{YYYY}-{#####}", title_field="driver", icon="fa fa-briefcase",
	search_fields="driver,entry_type,reference", perms="ops", submittable=True,
	fields=[
		F("driver", "Link", "Driver", options="Driver", reqd=1, in_list_view=1, in_standard_filter=1),
		F("posting_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
		C(),
		F("entry_type", "Select", "Entry Type", reqd=1, in_list_view=1, in_standard_filter=1,
			options="Advance\nReturn\nReimbursement",
			description="Advance: cash given to the driver. Return: cash the driver hands back. Reimbursement: company repays expenses the driver paid personally."),
		F("amount", "Currency", "Amount", reqd=1, in_list_view=1),
		S("Details"),
		F("reference", "Data", "Reference"),
		F("notes", "Small Text", "Notes"),
		S("Accounting", collapsible=1),
		COMPANY(),
		COST_CENTER(),
		C(),
		F("journal_entry", "Link", "Journal Entry", options="Journal Entry", read_only=1, no_copy=1),
		F("amended_from", "Link", "Amended From", options="Driver Custody Entry", read_only=1, no_copy=1, print_hide=1),
	],
))

EXTRA_STRINGS = []
