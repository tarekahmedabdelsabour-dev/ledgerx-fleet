const RC = "ledgerx_fleet.fleet_management.doctype.rental_contract.rental_contract.";

frappe.ui.form.on("Rental Contract", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;
		if (frm.doc.status === "Reserved") {
			frm.add_custom_button(__("Hand Over"), () => {
				frappe.call({ method: RC + "hand_over", args: { name: frm.doc.name }, freeze: true, callback: () => frm.reload_doc() });
			}, __("Status"));
		}
		if (["Active", "Overdue"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Return Vehicles"), () => return_dialog(frm), __("Status"));
		}
		if (frm.doc.status === "Returned" && !frm.doc.sales_invoice) {
			frm.add_custom_button(__("Sales Invoice"), () => {
				frappe.call({
					method: RC + "make_sales_invoice", args: { name: frm.doc.name }, freeze: true,
					callback: (r) => frappe.set_route("Form", "Sales Invoice", r.message),
				});
			}, __("Create"));
		}
	},
});

function return_dialog(frm) {
	const fields = [
		{ fieldname: "actual_return", fieldtype: "Datetime", label: __("Actual Return"), reqd: 1, default: frappe.datetime.now_datetime() },
		{ fieldname: "damage_charges", fieldtype: "Currency", label: __("Damage Charges"), default: 0 },
		{ fieldname: "discount", fieldtype: "Currency", label: __("Discount"), default: 0 },
		{ fieldtype: "Section Break", label: __("Vehicles") },
	];
	(frm.doc.vehicles || []).forEach((r) => {
		fields.push({ fieldname: "odo_" + r.name, fieldtype: "Int", label: `${r.vehicle} - ${__("Odometer In")} (${__("Odometer Out")}: ${r.out_odometer || 0})`, reqd: 1, default: r.out_odometer || 0 });
	});
	const d = new frappe.ui.Dialog({
		title: __("Return Vehicles"),
		fields,
		primary_action_label: __("Return"),
		primary_action(v) {
			const odos = {};
			(frm.doc.vehicles || []).forEach((r) => (odos[r.name] = v["odo_" + r.name]));
			frappe.call({
				method: RC + "return_vehicles",
				args: { name: frm.doc.name, actual_return: v.actual_return, in_odometers: JSON.stringify(odos), damage_charges: v.damage_charges, discount: v.discount },
				freeze: true,
				callback: () => { d.hide(); frm.reload_doc(); },
			});
		},
	});
	d.show();
}
