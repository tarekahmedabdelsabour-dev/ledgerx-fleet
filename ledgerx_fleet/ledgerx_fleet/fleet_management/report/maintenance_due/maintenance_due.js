frappe.query_reports["Maintenance Due"] = {
	filters: [
		{ fieldname: "vehicle", label: __("Vehicle"), fieldtype: "Link", options: "Vehicle" },
		{ fieldname: "status", label: __("Status"), fieldtype: "Select", options: "\nOverdue\nDue Soon\nOK" },
	],
};
