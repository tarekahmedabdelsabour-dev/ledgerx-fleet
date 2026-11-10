frappe.ui.form.on("Fleet Document", {
	setup(frm) {
		frm.set_query("document_type", () => ({ filters: { applies_to: frm.doc.applies_to } }));
	},
	applies_to(frm) {
		frm.set_value("document_type", "");
	},
	issue_date(frm) {
		if (!frm.doc.issue_date || frm.doc.expiry_date || !frm.doc.document_type) return;
		frappe.db.get_value("Fleet Document Type", frm.doc.document_type, "validity_months").then((r) => {
			const m = r.message && r.message.validity_months;
			if (m) frm.set_value("expiry_date", frappe.datetime.add_months(frm.doc.issue_date, m));
		});
	},
});
