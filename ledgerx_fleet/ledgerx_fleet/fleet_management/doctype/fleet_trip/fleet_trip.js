frappe.ui.form.on("Fleet Trip", {
	setup(frm) {
		frm.set_query("trailer", () => ({ filters: { name: ["!=", frm.doc.vehicle || ""] } }));
	},
	refresh(frm) {
		const call = (status) =>
			frappe.call({
				method: "ledgerx_fleet.fleet_management.doctype.fleet_trip.fleet_trip.set_trip_status",
				args: { name: frm.doc.name, status },
				freeze: true,
				callback: () => frm.reload_doc(),
			});
		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			if (frm.doc.status === "Planned") frm.add_custom_button(__("Dispatch"), () => call("Dispatched"), __("Status"));
			if (["Planned", "Dispatched"].includes(frm.doc.status)) {
				frm.add_custom_button(__("Start Trip"), () => call("In Transit"), __("Status"));
			}
		}
		if (frm.doc.docstatus === 1 && frm.doc.trip_type === "Customer Haulage" && frm.doc.billable &&
			flt(frm.doc.revenue) > 0 && !frm.doc.sales_invoice) {
			frm.add_custom_button(__("Sales Invoice"), () => {
				frappe.call({
					method: "ledgerx_fleet.fleet_management.doctype.fleet_trip.fleet_trip.make_sales_invoice",
					args: { name: frm.doc.name },
					freeze: true,
					callback: (r) => frappe.set_route("Form", "Sales Invoice", r.message),
				});
			}, __("Create"));
		}
	},
	vehicle(frm) {
		if (!frm.doc.vehicle) return;
		frappe.db.get_value("Vehicle", frm.doc.vehicle, ["last_odometer", "current_driver"]).then((r) => {
			const v = r.message || {};
			frm.set_value("start_odometer", v.last_odometer || 0);
			if (v.current_driver && !frm.doc.driver) frm.set_value("driver", v.current_driver);
		});
	},
});
