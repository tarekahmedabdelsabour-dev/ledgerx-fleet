frappe.ui.form.on("Fleet Incident", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Work Order"), () => {
			frappe.new_doc("Fleet Work Order", {
				vehicle: frm.doc.vehicle,
				work_type: "Corrective",
				incident: frm.doc.name,
				problem: frm.doc.description || "",
			});
		}, __("Create"));
	},
});
