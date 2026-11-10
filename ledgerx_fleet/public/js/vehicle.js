frappe.ui.form.on("Vehicle", {
	refresh(frm) {
		if (frm.is_new()) return;
		const make = (doctype, extra) => () =>
			frappe.new_doc(doctype, Object.assign({ vehicle: frm.doc.name, company: frm.doc.company }, extra || {}));
		frm.add_custom_button(__("Fuel Log"), make("Fuel Log"), __("Create"));
		frm.add_custom_button(__("Work Order"), make("Fleet Work Order"), __("Create"));
		frm.add_custom_button(__("Fleet Trip"), make("Fleet Trip"), __("Create"));
		frm.add_custom_button(__("Fleet Document"), make("Fleet Document", { applies_to: "Vehicle" }), __("Create"));
		frm.add_custom_button(__("Traffic Fine"), make("Traffic Fine"), __("Create"));
		frm.add_custom_button(__("Fleet Incident"), make("Fleet Incident"), __("Create"));
		frm.add_custom_button(__("Fleet Assignment"), make("Fleet Assignment"), __("Create"));
		if (frm.doc.last_position_lat && frm.doc.last_position_lng) {
			frm.add_custom_button(__("Show on Map"), () => {
				window.open(`https://www.openstreetmap.org/?mlat=${frm.doc.last_position_lat}&mlon=${frm.doc.last_position_lng}#map=16/${frm.doc.last_position_lat}/${frm.doc.last_position_lng}`);
			});
		}
	},
});
