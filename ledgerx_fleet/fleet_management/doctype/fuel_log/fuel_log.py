import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ledgerx_fleet.utils import fleet
from ledgerx_fleet.utils import logic

FUEL_OPTIONS = ("Petrol", "Diesel", "CNG", "LPG", "Electric", "Hybrid")


class FuelLog(Document):
	def validate(self):
		s = fleet.get_settings()
		if not self.company:
			self.company = s.company
		if not self.cost_center:
			self.cost_center = fleet.cost_center_for(self.vehicle) or s.cost_center
		v = frappe.db.get_value("Vehicle", self.vehicle, ["last_odometer", "fuel_type", "current_driver"], as_dict=True)
		if not self.driver:
			self.driver = v.current_driver
		if not self.fuel_type and v.fuel_type in FUEL_OPTIONS:
			self.fuel_type = v.fuel_type
		if flt(self.quantity) <= 0 or flt(self.rate) < 0:
			frappe.throw(_("Quantity must be greater than zero"))
		self.amount = flt(self.quantity) * flt(self.rate)

		prev = self.previous_log()
		self.last_odometer = prev.odometer if prev else (v.last_odometer or 0)
		if prev and self.odometer < prev.odometer:
			frappe.throw(
				_("Odometer {0} is lower than the previous fill ({1} on {2})").format(
					self.odometer, prev.odometer, prev.posting_date)
			)
		self.distance = max(0, int(self.odometer or 0) - int(self.last_odometer or 0))
		self.consumption = self.calc_consumption()

	def previous_log(self):
		rows = frappe.db.sql(
			"""select name, odometer, posting_date from `tabFuel Log`
			where docstatus = 1 and vehicle = %s and name != %s and posting_date <= %s
			order by posting_date desc, odometer desc limit 1""",
			(self.vehicle, self.name or "", self.posting_date),
			as_dict=True,
		)
		return rows[0] if rows else None

	def calc_consumption(self):
		if not self.full_tank:
			return 0
		prev_full = frappe.db.sql(
			"""select odometer from `tabFuel Log` where docstatus = 1 and vehicle = %s and full_tank = 1
			and name != %s and odometer < %s order by odometer desc limit 1""",
			(self.vehicle, self.name or "", self.odometer),
		)
		if not prev_full:
			return 0
		base = prev_full[0][0]
		liters = frappe.db.sql(
			"""select ifnull(sum(quantity), 0) from `tabFuel Log` where docstatus = 1 and vehicle = %s
			and name != %s and odometer > %s and odometer < %s""",
			(self.vehicle, self.name or "", base, self.odometer),
		)[0][0]
		return logic.consumption_l_per_100km(self.odometer - base, flt(liters) + flt(self.quantity))

	def on_submit(self):
		fleet.update_vehicle_odometer(self.vehicle, self.odometer)
		if self.driver_expense:
			return  # the approved Driver Expense already posted the accounting entry
		s = fleet.get_settings()
		je = fleet.post_journal_entry(
			self, s.fuel_expense_account, self.amount, _("Fuel {0} - {1}").format(self.name, self.vehicle),
			self.posting_date,
		)
		if je:
			self.db_set("journal_entry", je)

	def on_cancel(self):
		fleet.cancel_linked("Journal Entry", self.journal_entry)
