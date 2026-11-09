frappe.query_reports["Document Expiry"] = {
	filters: [
		{ fieldname: "applies_to", label: __("Applies To"), fieldtype: "Select", options: "\nVehicle\nDriver" },
		{ fieldname: "status", label: __("Status"), fieldtype: "Select", options: "\nExpired\nExpiring Soon\nActive" },
		{ fieldname: "within_days", label: __("Expiring Within (days)"), fieldtype: "Int" },
	],
};
