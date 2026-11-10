frappe.ui.form.on("Fuel Log", {
	vehicle(frm) {
		if (!frm.doc.vehicle) return;
		frappe.db.get_value("Vehicle", frm.doc.vehicle, ["last_odometer", "current_driver"]).then((r) => {
			const v = r.message || {};
			if (v.current_driver && !frm.doc.driver) frm.set_value("driver", v.current_driver);
			frm.set_value("last_odometer", v.last_odometer || 0);
		});
	},
	odometer(frm) {
		frm.set_value("distance", Math.max(0, cint(frm.doc.odometer) - cint(frm.doc.last_odometer)));
	},
	quantity: (frm) => set_amount(frm),
	rate: (frm) => set_amount(frm),
});

function set_amount(frm) {
	frm.set_value("amount", flt(frm.doc.quantity) * flt(frm.doc.rate));
}
