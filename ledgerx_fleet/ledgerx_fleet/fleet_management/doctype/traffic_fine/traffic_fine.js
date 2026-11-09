frappe.ui.form.on("Traffic Fine", {
	status(frm) {
		if (frm.doc.status === "Paid" && !frm.doc.paid_date) frm.set_value("paid_date", frappe.datetime.get_today());
	},
});
