frappe.ui.form.on("Vehicle Tire", {
	status(frm) {
		if (frm.doc.status === "Mounted" && !frm.doc.mounted_on) {
			frm.set_value("mounted_on", frappe.datetime.get_today());
		}
	},
});
