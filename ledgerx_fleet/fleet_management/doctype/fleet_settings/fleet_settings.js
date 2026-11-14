frappe.ui.form.on("Fleet Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Create Driver Incentives"), () => {
			frappe.prompt([
				{ fieldname: "from_date", fieldtype: "Date", label: __("From Date"), reqd: 1, default: frappe.datetime.month_start() },
				{ fieldname: "to_date", fieldtype: "Date", label: __("To Date"), reqd: 1, default: frappe.datetime.month_end() },
			], (v) => {
				frappe.call({
					method: "ledgerx_fleet.fleet_management.doctype.fleet_settings.fleet_settings.create_driver_incentives",
					args: v,
					callback: (r) => frappe.msgprint(__("{0} draft Additional Salary created for HR review", [(r.message || []).length])),
				});
			}, __("Driver Incentives"));
		}, __("HR"));
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
