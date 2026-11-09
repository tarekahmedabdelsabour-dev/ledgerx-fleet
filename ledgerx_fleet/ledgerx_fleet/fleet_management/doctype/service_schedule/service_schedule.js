frappe.ui.form.on("Service Schedule", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.status === "OK" || frm.doc.status === "Disabled") return;
		frm.add_custom_button(__("Create Work Order"), () => {
			frappe.new_doc("Fleet Work Order", { vehicle: frm.doc.vehicle, work_type: "Preventive" }, (doc) => {
				frappe.model.add_child(doc, "tasks", { description: frm.doc.task, schedule: frm.doc.name });
			});
		});
	},
});
