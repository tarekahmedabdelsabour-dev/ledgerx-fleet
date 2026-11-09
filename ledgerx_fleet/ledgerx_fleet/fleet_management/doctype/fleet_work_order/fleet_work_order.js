frappe.ui.form.on("Fleet Work Order", {
	setup(frm) {
		frm.set_query("schedule", "tasks", () => ({ filters: { vehicle: frm.doc.vehicle } }));
	},
	refresh(frm) {
		if (frm.doc.docstatus !== 0 || frm.is_new()) return;
		if (frm.doc.status === "Open") {
			frm.add_custom_button(__("Start Work"), () => {
				frm.set_value("status", "In Progress");
				frm.set_value("start_date", frappe.datetime.get_today());
				frm.save();
			});
		}
		if (frm.doc.status === "In Progress") {
			frm.add_custom_button(__("Waiting Parts"), () => {
				frm.set_value("status", "Waiting Parts");
				frm.save();
			});
		}
		if (frm.doc.status === "Waiting Parts") {
			frm.add_custom_button(__("Resume Work"), () => {
				frm.set_value("status", "In Progress");
				frm.save();
			});
		}
	},
	vehicle(frm) {
		if (!frm.doc.vehicle) return;
		frappe.db.get_value("Vehicle", frm.doc.vehicle, "last_odometer").then((r) => {
			if (r.message) frm.set_value("odometer", r.message.last_odometer);
		});
	},
});

frappe.ui.form.on("Work Order Part", {
	item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.item_code) return;
		frappe.db.get_value("Item", row.item_code, "valuation_rate").then((r) => {
			if (r.message && !row.rate) frappe.model.set_value(cdt, cdn, "rate", r.message.valuation_rate || 0);
		});
	},
	qty: (frm, cdt, cdn) => recalc_part(cdt, cdn),
	rate: (frm, cdt, cdn) => recalc_part(cdt, cdn),
});

function recalc_part(cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
}
