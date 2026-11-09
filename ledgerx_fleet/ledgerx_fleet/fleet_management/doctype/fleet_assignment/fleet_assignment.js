frappe.ui.form.on("Fleet Assignment", {
	vehicle(frm) {
		if (!frm.doc.vehicle) return;
		frappe.db.get_value("Vehicle", frm.doc.vehicle, "last_odometer").then((r) => {
			if (r.message) frm.set_value("start_odometer", r.message.last_odometer);
		});
	},
});
