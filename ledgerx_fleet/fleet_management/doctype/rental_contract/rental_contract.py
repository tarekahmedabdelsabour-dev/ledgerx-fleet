import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, now_datetime

from ledgerx_fleet.utils import fleet
from ledgerx_fleet.utils import logic


class RentalContract(Document):
	def validate(self):
		s = fleet.get_settings()
		if not self.company:
			self.company = s.company
		if not self.cost_center:
			self.cost_center = s.default_cost_center
		if logic.to_datetime(self.to_date) <= logic.to_datetime(self.from_date):
			frappe.throw(_("'To' must be after 'From'"))
		seen = set()
		for r in self.vehicles:
			if r.vehicle in seen:
				frappe.throw(_("Row {0}: {1} is listed twice").format(r.idx, frappe.bold(r.vehicle)))
			seen.add(r.vehicle)
		if self.docstatus == 0:
			for r in self.vehicles:
				fleet.assert_vehicle_free(r.vehicle, self.from_date, self.to_date, ("Rental Contract", self.name))
				fleet.assert_documents_valid(vehicle=r.vehicle, driver=self.chauffeur,
					on_date=str(logic.to_datetime(self.from_date).date()))
		self.calculate()

	def calculate(self):
		end = logic.to_datetime(self.to_date)
		if self.actual_return and logic.to_datetime(self.actual_return) > end:
			end = logic.to_datetime(self.actual_return)  # late return is charged
		self.days = logic.rental_days(self.from_date, end)
		subtotal = extra = 0
		for r in self.vehicles:
			r.line_amount = flt(r.rate_per_day) * self.days
			if r.in_odometer and r.out_odometer is not None:
				r.extra_km = logic.extra_km(int(r.in_odometer) - int(r.out_odometer), r.km_included_per_day, self.days)
			else:
				r.extra_km = 0
			subtotal += flt(r.line_amount)
			extra += flt(r.extra_km) * flt(r.extra_km_rate)
		self.subtotal = subtotal
		self.extra_km_charges = extra
		self.grand_total = subtotal + extra + flt(self.damage_charges) - flt(self.discount)

	def on_cancel(self):
		self.db_set("status", "Cancelled")
		for r in self.vehicles:
			fleet.set_vehicle_status(r.vehicle, "Active", only_if=("Rented Out",))


def _contract(name, status_in):
	doc = frappe.get_doc("Rental Contract", name)
	doc.check_permission("write")
	if doc.docstatus != 1:
		frappe.throw(_("Submit the contract first"))
	if doc.status not in status_in:
		frappe.throw(_("Not allowed while the contract is {0}").format(_(doc.status)))
	return doc


@frappe.whitelist()
def hand_over(name):
	doc = _contract(name, ("Reserved",))
	for r in doc.vehicles:
		fleet.assert_documents_valid(vehicle=r.vehicle, driver=doc.chauffeur)
		odo = frappe.db.get_value("Vehicle", r.vehicle, "last_odometer") or 0
		frappe.db.set_value("Rental Vehicle", r.name, "out_odometer", odo, update_modified=False)
		fleet.set_vehicle_status(r.vehicle, "Rented Out")
	doc.db_set("status", "Active")
	return "Active"


@frappe.whitelist()
def return_vehicles(name, actual_return, in_odometers, damage_charges=0, discount=0):
	"""in_odometers: JSON {child row name: odometer in}."""
	doc = _contract(name, ("Active", "Overdue"))
	odos = json.loads(in_odometers) if isinstance(in_odometers, str) else in_odometers
	doc.actual_return = get_datetime(actual_return)
	if doc.actual_return < get_datetime(doc.from_date):
		frappe.throw(_("Return time cannot be before the start of the contract"))
	doc.damage_charges = flt(damage_charges)
	doc.discount = flt(discount)
	odos = {str(k): v for k, v in odos.items()}
	for r in doc.vehicles:
		if str(r.name) not in odos:
			frappe.throw(_("Enter the return odometer for {0}").format(frappe.bold(r.vehicle)))
		odo_in = int(odos[str(r.name)])
		if odo_in < int(r.out_odometer or 0):
			frappe.throw(_("Return odometer of {0} cannot be lower than {1}").format(r.vehicle, r.out_odometer))
		r.in_odometer = odo_in
	doc.calculate()
	for r in doc.vehicles:
		frappe.db.set_value(
			"Rental Vehicle", r.name,
			{"in_odometer": r.in_odometer, "extra_km": r.extra_km, "line_amount": r.line_amount},
			update_modified=False,
		)
		fleet.update_vehicle_odometer(r.vehicle, r.in_odometer)
		fleet.set_vehicle_status(r.vehicle, "Active", only_if=("Rented Out",))
	doc.db_set(
		{
			"status": "Returned", "actual_return": doc.actual_return, "days": doc.days,
			"subtotal": doc.subtotal, "extra_km_charges": doc.extra_km_charges,
			"damage_charges": doc.damage_charges, "discount": doc.discount, "grand_total": doc.grand_total,
		},
		update_modified=True,
	)
	return doc.grand_total


@frappe.whitelist()
def make_sales_invoice(name):
	doc = _contract(name, ("Returned",))
	frappe.has_permission("Sales Invoice", "create", throw=True)
	if doc.sales_invoice:
		frappe.throw(_("Already invoiced: {0}").format(doc.sales_invoice))
	item = fleet.get_settings().rental_item
	if not item:
		frappe.throw(_("Set 'Item for Rental Invoices' in Fleet Settings"))
	lines = []
	for r in doc.vehicles:
		lines.append({"item_code": item, "qty": doc.days, "rate": r.rate_per_day, "cost_center": doc.cost_center,
			"description": _("Rental of {0} ({1} → {2})").format(r.vehicle, doc.from_date, doc.actual_return)})
		if flt(r.extra_km) > 0 and flt(r.extra_km_rate) > 0:
			lines.append({"item_code": item, "qty": r.extra_km, "rate": r.extra_km_rate, "cost_center": doc.cost_center,
				"description": _("Extra km - {0}").format(r.vehicle)})
	if flt(doc.damage_charges) > 0:
		lines.append({"item_code": item, "qty": 1, "rate": doc.damage_charges, "cost_center": doc.cost_center,
			"description": _("Damage charges")})
	si = frappe.get_doc(
		{
			"doctype": "Sales Invoice", "customer": doc.customer, "company": doc.company,
			"remarks": _("Rental contract {0}").format(doc.name), "items": lines,
			"apply_discount_on": "Grand Total", "discount_amount": flt(doc.discount),
		}
	)
	si.set_missing_values()
	si.insert()
	doc.db_set("sales_invoice", si.name)
	return si.name


def mark_overdue():
	frappe.db.sql(
		"""update `tabRental Contract` set status = 'Overdue'
		where docstatus = 1 and status = 'Active' and to_date < %s""",
		now_datetime(),
	)
