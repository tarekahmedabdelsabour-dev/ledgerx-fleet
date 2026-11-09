frappe.ui.form.on("Service Plan", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Apply to Vehicle"), () => {
			frappe.prompt(
				[{ fieldname: "vehicle", fieldtype: "Link", options: "Vehicle", label: __("Vehicle"), reqd: 1 }],
				(v) => {
					frappe.call({
						method: "ledgerx_fleet.fleet_management.doctype.service_plan.service_plan.apply_plan_to_vehicle",
						args: { plan: frm.doc.name, vehicle: v.vehicle },
						callback: (r) => frappe.show_alert({ message: __("{0} schedules created", [r.message]), indicator: "green" }),
					});
				},
				__("Apply Plan")
			);
		});
	},
});
