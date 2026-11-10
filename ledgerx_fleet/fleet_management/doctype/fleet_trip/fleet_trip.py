import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

from ledgerx_fleet.utils import fleet
from ledgerx_fleet.utils import logic


class FleetTrip(Document):
	def validate(self):
		s = fleet.get_settings()
		if not self.company:
			self.company = s.company
		if not self.cost_center:
			self.cost_center = fleet.cost_center_for(self.vehicle) or s.cost_center
		if self.vehicle and self.trailer and self.vehicle == self.trailer:
			frappe.throw(_("Trailer must be a different vehicle"))
		if self.planned_end and logic.to_datetime(self.planned_end) < logic.to_datetime(self.planned_start):
			frappe.throw(_("Planned End cannot be before Planned Start"))
		if self.docstatus == 0:
			self.check_resources()
		if not self.start_odometer:
			self.start_odometer = frappe.db.get_value("Vehicle", self.vehicle, "last_odometer") or 0
		if self.end_odometer:
			if int(self.end_odometer) < int(self.start_odometer or 0):
				frappe.throw(_("End Odometer cannot be lower than Start Odometer"))
			self.distance = int(self.end_odometer) - int(self.start_odometer or 0)
		else:
			self.distance = 0
		self.total_expenses = sum(flt(e.amount) for e in self.expenses)
		if self.trip_type == "Customer Haulage" and self.billable:
			self.revenue = logic.trip_revenue(self.rate_basis, self.rate, self.distance, self.cargo_weight_kg)
		else:
			self.revenue = 0
		self.profit = flt(self.revenue) - flt(self.total_expenses)
		payload = frappe.db.get_value("Vehicle", self.vehicle, "payload_kg")
		if payload and flt(self.cargo_weight_kg) > flt(payload):
			frappe.msgprint(
				_("Cargo weight {0} kg exceeds the vehicle payload of {1} kg").format(self.cargo_weight_kg, payload),
				indicator="orange", alert=True,
			)

	def check_resources(self):
		ex = ("Fleet Trip", self.name)
		fleet.assert_vehicle_free(self.vehicle, self.planned_start, self.planned_end, ex)
		if self.trailer:
			fleet.assert_vehicle_free(self.trailer, self.planned_start, self.planned_end, ex)
		clash = frappe.db.sql(
			"""select name from `tabFleet Trip` where docstatus < 2 and status not in ('Completed', 'Cancelled')
			and driver = %(d)s and name != %(n)s and planned_start <= %(e)s
			and ifnull(planned_end, date_add(planned_start, interval 1 day)) >= %(s)s""",
			{"d": self.driver, "n": self.name or "", "s": logic.to_datetime(self.planned_start),
				"e": logic.to_datetime(self.planned_end) if self.planned_end
				else logic.to_datetime(self.planned_start)},
		)
		if clash:
			frappe.throw(_("Driver {0} is already on trip {1}").format(frappe.bold(self.driver), clash[0][0]))
		if self.status in ("Planned", "Dispatched"):
			fleet.assert_documents_valid(self.vehicle, self.driver, str(logic.to_datetime(self.planned_start).date()))

	def before_submit(self):
		if not self.end_odometer or not self.actual_end:
			frappe.throw(_("Enter the End Odometer and Actual End to complete the trip"))

	def on_submit(self):
		self.db_set("status", "Completed")
		fleet.update_vehicle_odometer(self.vehicle, self.end_odometer)
		fleet.set_vehicle_status(self.vehicle, "Active", only_if=("On Trip",))

	def before_cancel(self):
		if self.sales_invoice and frappe.db.get_value("Sales Invoice", self.sales_invoice, "docstatus") < 2:
			frappe.throw(_("Cancel Sales Invoice {0} first").format(self.sales_invoice))

	def on_cancel(self):
		self.db_set("status", "Cancelled")
		fleet.set_vehicle_status(self.vehicle, "Active", only_if=("On Trip",))


@frappe.whitelist()
def set_trip_status(name, status):
	"""Planned -> Dispatched -> In Transit (the trip is completed by submitting it)."""
	doc = frappe.get_doc("Fleet Trip", name)
	doc.check_permission("write")
	if doc.docstatus != 0:
		frappe.throw(_("Only draft trips can change status"))
	allowed = {"Dispatched": ("Planned",), "In Transit": ("Dispatched", "Planned"), "Planned": ("Dispatched",)}
	if status not in allowed or doc.status not in allowed[status]:
		frappe.throw(_("Cannot change status from {0} to {1}").format(_(doc.status), _(status)))
	if status == "Dispatched":
		doc.check_resources()
	doc.status = status
	if status == "In Transit" and not doc.actual_start:
		doc.actual_start = now_datetime()
	doc.save()
	if status in ("Dispatched", "In Transit"):
		fleet.set_vehicle_status(doc.vehicle, "On Trip", only_if=("Active", None, ""))
	else:
		fleet.set_vehicle_status(doc.vehicle, "Active", only_if=("On Trip",))
	return doc.status


@frappe.whitelist()
def make_sales_invoice(name):
	doc = frappe.get_doc("Fleet Trip", name)
	doc.check_permission("read")
	frappe.has_permission("Sales Invoice", "create", throw=True)
	if doc.docstatus != 1:
		frappe.throw(_("Submit the trip first"))
	if doc.trip_type != "Customer Haulage" or not doc.billable or flt(doc.revenue) <= 0:
		frappe.throw(_("This trip has no billable revenue"))
	if doc.sales_invoice:
		frappe.throw(_("Already invoiced: {0}").format(doc.sales_invoice))
	item = fleet.get_settings().trip_item
	if not item:
		frappe.throw(_("Set 'Item for Trip Invoices' in Fleet Settings"))
	si = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"customer": doc.customer,
			"company": doc.company,
			"posting_date": frappe.utils.nowdate(),
			"set_posting_time": 0,
			"remarks": _("Trip {0}: {1} → {2}").format(doc.name, doc.origin, doc.destination),
			"items": [
				{
					"item_code": item,
					"qty": 1,
					"rate": doc.revenue,
					"description": _("Transport {0} → {1} ({2}, {3})").format(
						doc.origin, doc.destination, doc.vehicle, doc.name),
					"cost_center": doc.cost_center,
				}
			],
		}
	)
	si.flags.ignore_permissions = False
	si.set_missing_values()
	si.insert()
	doc.db_set("sales_invoice", si.name)
	return si.name
