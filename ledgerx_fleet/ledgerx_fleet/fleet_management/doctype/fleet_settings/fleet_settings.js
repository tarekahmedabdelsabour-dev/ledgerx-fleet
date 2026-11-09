frappe.ui.form.on("Fleet Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Generate GPS Token"), () => {
			frappe.confirm(__("A new token replaces the old one. Devices using the old token will stop working."), () => {
				frappe.call({
					method: "ledgerx_fleet.fleet_management.doctype.fleet_settings.fleet_settings.generate_gps_token",
					callback: (r) => {
						frappe.msgprint({
							title: __("GPS API Token"),
							message: `<code style="user-select:all">${frappe.utils.escape_html(r.message)}</code><br><br>` +
								__("Copy it now. It is stored encrypted and will not be shown again."),
						});
						frm.reload_doc();
					},
				});
			});
		});
	},
});
