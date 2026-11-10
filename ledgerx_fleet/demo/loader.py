"""Load the sample company (see data.py) into the current site.

    bench --site mysite.localhost execute ledgerx_fleet.demo.loader.load --kwargs "{'company': 'Your Company'}"

Safe to run twice: existing records are skipped. Every record is created in its own savepoint, so one
failure never stops the rest; the report lists what was created, skipped and failed (printed and written to
sites/<site>/private/files/fleet-demo-report.txt). Back up the site first (bench --site X backup).
"""

import traceback

import frappe
from frappe.utils import add_days, add_to_date, get_datetime, nowdate

from ledgerx_fleet.demo import data as D


class Report:
	def __init__(self):
		self.created, self.skipped, self.failed = {}, {}, []

	def ok(self, doctype):
		self.created[doctype] = self.created.get(doctype, 0) + 1

	def skip(self, doctype):
		self.skipped[doctype] = self.skipped.get(doctype, 0) + 1

	def fail(self, doctype, label, err):
		self.failed.append((doctype, label, str(err).strip().splitlines()[-1][:300] if str(err).strip() else repr(err)))

	def text(self):
		out = ["LedgerX Fleet demo data", "=" * 40, "Created:"]
		out += [f"  {k}: {v}" for k, v in sorted(self.created.items())] or ["  (nothing)"]
		out += ["Already existed (skipped):"]
		out += [f"  {k}: {v}" for k, v in sorted(self.skipped.items())] or ["  (nothing)"]
		out += [f"FAILED: {len(self.failed)}"]
		out += [f"  [{d}] {label}: {err}" for d, label, err in self.failed]
		return "\n".join(out)


def _day(offset):
	return add_days(nowdate(), offset)


def _make(rep, doctype, values, filters=None, label=None, submit=False):
	"""Create one record if it does not exist yet; never raise."""
	label = label or values.get("name") or str(filters or values)[:60]
	try:
		if filters and frappe.db.exists(doctype, filters):
			rep.skip(doctype)
			return frappe.db.get_value(doctype, filters, "name")
		frappe.db.savepoint("lx_demo")
		doc = frappe.get_doc({"doctype": doctype, **values})
		doc.insert(ignore_permissions=True)
		if submit:
			doc.submit()
		rep.ok(doctype)
		return doc.name
	except Exception as e:
		frappe.db.rollback(save_point="lx_demo")
		rep.fail(doctype, label, e)
		frappe.log_error(title=f"fleet demo: {doctype} {label}", message=traceback.format_exc())
		return None


def _first(doctype, filters, fallback):
	return frappe.db.get_value(doctype, filters, "name") or fallback


def load(company=None, submit=1):
	submit = int(submit)
	rep = Report()
	company = company or frappe.db.get_single_value("Fleet Settings", "company") or frappe.defaults.get_global_default("company")
	if not company or not frappe.db.exists("Company", company):
		names = frappe.get_all("Company", pluck="name")
		raise SystemExit(f"Company '{company}' not found. Pass one of: {names}")

	frappe.flags.in_import = False
	try:
		from ledgerx_fleet.install import seed_defaults
		seed_defaults()  # starter document + vehicle types (skips existing)
		frappe.db.commit()
	except Exception as e:
		rep.fail("Setup", "seed_defaults", e)
	roots = frappe.get_all("Cost Center", filters={"company": company, "is_group": 1}, order_by="lft asc", limit=1, pluck="name")
	root_cc = roots[0] if roots else None
	supplier_group = _first("Supplier Group", {"is_group": 0}, "All Supplier Groups")
	customer_group = _first("Customer Group", {"is_group": 0}, "All Customer Groups")
	territory = _first("Territory", {"is_group": 0}, "All Territories")
	item_group = _first("Item Group", {"is_group": 0}, "All Item Groups")

	# --- settings
	fs = frappe.get_single("Fleet Settings")
	fs.company = company
	fs.save(ignore_permissions=True)

	# --- branches = cost centers
	cc = []
	for b in D.BRANCHES:
		name = frappe.db.get_value("Cost Center", {"cost_center_name": b, "company": company}, "name")
		if name:
			rep.skip("Cost Center")
		else:
			name = _make(rep, "Cost Center", {"cost_center_name": b, "parent_cost_center": root_cc, "company": company, "is_group": 0}, label=b)
		cc.append(name)
	if cc and cc[0] and not fs.cost_center:
		fs.cost_center = cc[0]
		fs.save(ignore_permissions=True)

	# --- suppliers, customers, items
	for s in D.SUPPLIERS:
		_make(rep, "Supplier", {"supplier_name": s, "supplier_group": supplier_group, "supplier_type": "Company"},
			{"supplier_name": s})
	customers = []
	for c in D.CUSTOMERS:
		customers.append(_make(rep, "Customer", {"customer_name": c, "customer_group": customer_group, "territory": territory,
			"customer_type": "Company"}, {"customer_name": c}))
	for code, name, rate in D.ITEMS:
		_make(rep, "Item", {"item_code": code, "item_name": name, "item_group": item_group, "stock_uom": "Nos",
			"is_stock_item": 1, "valuation_rate": rate, "standard_rate": rate}, code, label=code)
	frappe.db.commit()

	# --- service plans
	for plan, vtype, tasks in D.SERVICE_PLANS:
		_make(rep, "Service Plan", {"plan_name": plan, "vehicle_type": vtype if frappe.db.exists("Vehicle Type", vtype) else None,
			"is_active": 1, "tasks": [{"task": t, "category": cat, "interval_km": km, "interval_days": d, "estimated_cost": cost}
				for t, cat, km, d, cost in tasks]}, plan, label=plan)

	# --- drivers
	drivers = []
	for full, phone, lic, exp, bi in D.DRIVERS:
		drivers.append(_make(rep, "Driver", {"full_name": full, "status": "Active", "cell_number": phone, "license_number": lic,
			"issuing_date": _day(exp - 1825), "expiry_date": _day(exp), "fleet_cost_center": cc[bi]}, {"license_number": lic}, label=full))
	frappe.db.commit()

	# --- vehicles
	vehicles = []
	uom = "Litre" if frappe.db.exists("UOM", "Litre") else "Nos"
	for (plate, make, model, year, vtype, fuel, odo, value, color, bi, plan, tank, payload, owner) in D.VEHICLES:
		vehicles.append(_make(rep, "Vehicle", {
			"license_plate": plate, "make": make, "model": model, "model_year": year, "vehicle_type": vtype,
			"fuel_type": fuel, "uom": uom, "last_odometer": odo, "vehicle_value": value, "color": color,
			"acquisition_date": _day(-365 * 2), "location": D.BRANCHES[bi], "company": company,
			"fleet_cost_center": cc[bi], "service_plan": plan or None, "tank_capacity": tank, "payload_kg": payload,
			"ownership": owner, "fleet_status": "Active", "chassis_no": f"CH{year}{sum(ord(c) * (i + 1) for i, c in enumerate(plate)):08d}",
		}, plate, label=plate))
	frappe.db.commit()

	# --- documents (vehicles + driver licences)
	for vi, docs in D.VEHICLE_DOCS.items():
		for dtype, (issued_ago, to_expiry) in docs.items():
			if vehicles[vi] and frappe.db.exists("Fleet Document Type", dtype):
				_make(rep, "Fleet Document", {"applies_to": "Vehicle", "vehicle": vehicles[vi], "document_type": dtype,
					"issue_date": _day(-issued_ago), "expiry_date": _day(to_expiry),
					"document_no": f"{dtype[:3].upper()}-{vi + 1:03d}"},
					{"applies_to": "Vehicle", "vehicle": vehicles[vi], "document_type": dtype}, label=f"{vehicles[vi]} / {dtype}")
	for i, (full, phone, lic, exp, bi) in enumerate(D.DRIVERS):
		if drivers[i] and frappe.db.exists("Fleet Document Type", "Driving License"):
			_make(rep, "Fleet Document", {"applies_to": "Driver", "driver": drivers[i], "document_type": "Driving License",
				"issue_date": _day(exp - 1825), "expiry_date": _day(exp), "document_no": lic},
				{"applies_to": "Driver", "driver": drivers[i], "document_type": "Driving License"}, label=full)
	frappe.db.commit()

	# --- assignments, GPS devices, tires
	for di, vi in D.ASSIGNMENTS:
		if drivers[di] and vehicles[vi]:
			_make(rep, "Fleet Assignment", {"vehicle": vehicles[vi], "driver": drivers[di], "from_date": _day(-90),
				"start_odometer": D.VEHICLES[vi][6] - 4000}, {"vehicle": vehicles[vi], "driver": drivers[di]}, label=f"{vehicles[vi]} -> {drivers[di]}")
	for dev, vi in D.GPS_DEVICES:
		_make(rep, "GPS Device", {"device_id": dev, "vehicle": vehicles[vi], "provider": "Demo GPS", "status": "Active"}, dev, label=dev)
	for serial, brand, size, vi, pos, cost in D.TIRES:
		vals = {"tire_serial": serial, "brand": brand, "size": size, "cost": cost, "purchase_date": _day(-200), "expected_life_km": 80000}
		if vi is not None and vehicles[vi]:
			vals.update({"status": "Mounted", "vehicle": vehicles[vi], "position": pos, "mounted_on": _day(-180),
				"mount_odometer": D.VEHICLES[vi][6] - 9000})
		else:
			vals["status"] = "In Stock"
		_make(rep, "Vehicle Tire", vals, serial, label=serial)
	frappe.db.commit()

	# --- fuel logs (ascending odometer per vehicle)
	odo = {}
	for vi, ago, litres, rate, step in sorted(D.FUEL_LOGS, key=lambda r: (r[0], -r[1])):
		if not vehicles[vi]:
			continue
		odo[vi] = odo.get(vi, D.VEHICLES[vi][6]) + step
		drv = next((drivers[d] for d, v in D.ASSIGNMENTS if v == vi), None)
		_make(rep, "Fuel Log", {"posting_date": _day(-ago), "vehicle": vehicles[vi], "driver": drv, "odometer": odo[vi],
			"fuel_type": D.VEHICLES[vi][5], "quantity": litres, "rate": rate, "full_tank": 1, "station_name": D.SUPPLIERS[1],
			"payment_mode": "Cash", "company": company, "cost_center": cc[D.VEHICLES[vi][9]]},
			{"vehicle": vehicles[vi], "odometer": odo[vi]}, label=f"{vehicles[vi]} {odo[vi]}", submit=bool(submit))
	frappe.db.commit()

	# --- work orders
	for vi, wtype, prio, status, ago, tasks, parts, other, sub in D.WORK_ORDERS:
		if not vehicles[vi]:
			continue
		rates = {c: r for c, _n, r in D.ITEMS}
		vals = {"vehicle": vehicles[vi], "work_type": wtype, "priority": prio, "company": company,
			"status": "Open" if status == "Completed" else status, "workshop_type": "External", "supplier": D.SUPPLIERS[0],
			"open_date": _day(-ago), "start_date": _day(-ago) if status != "Open" else None,
			"problem": tasks[0][0], "other_cost": other,
			"tasks": [{"description": d, "task_cost": c} for d, c in tasks],
			"parts": [{"item_code": i, "qty": q, "rate": rates[i]} for i, q in parts]}
		if sub:
			vals["completion_date"] = _day(-ago + 1)
		_make(rep, "Fleet Work Order", vals, {"vehicle": vehicles[vi], "open_date": _day(-ago), "work_type": wtype},
			label=f"{vehicles[vi]} {wtype}", submit=bool(submit and sub))
	frappe.db.commit()

	# --- trips
	for vi, di, ttype, ci, origin, dest, basis, rate, kg, cargo, km, ago, sub in D.TRIPS:
		if not (vehicles[vi] and drivers[di]):
			continue
		start = get_datetime(_day(-ago if ago > 0 else -ago)).replace(hour=7)
		start_odo = D.VEHICLES[vi][6] + 5000  # above anything fuel logs produced
		vals = {"trip_type": ttype, "customer": customers[ci] if ci is not None else None, "vehicle": vehicles[vi],
			"driver": drivers[di], "company": company, "origin": origin, "destination": dest,
			"planned_start": start, "planned_end": add_to_date(start, hours=10), "cargo_description": cargo,
			"cargo_weight_kg": kg, "billable": 1 if ttype == "Customer Haulage" else 0, "rate_basis": basis, "rate": rate,
			"start_odometer": start_odo,
			"expenses": [{"expense_type": "Toll", "description": "رسوم طريق", "amount": 120},
				{"expense_type": "Driver Allowance", "description": "بدل سفر", "amount": 250}]}
		if sub and ago > 0:
			vals.update({"actual_start": start, "actual_end": add_to_date(start, hours=9), "end_odometer": start_odo + km})
		_make(rep, "Fleet Trip", vals, {"vehicle": vehicles[vi], "driver": drivers[di], "origin": origin, "destination": dest},
			label=f"{vehicles[vi]} {origin}->{dest}", submit=bool(submit and sub and ago > 0))
	frappe.db.commit()

	# --- rentals
	for vi, ci, s_off, e_off, daily, free, extra, sub in D.RENTALS:
		if not (vehicles[vi] and customers[ci]):
			continue
		_make(rep, "Rental Contract", {"customer": customers[ci], "company": company,
			"from_date": get_datetime(_day(s_off)).replace(hour=10), "to_date": get_datetime(_day(e_off)).replace(hour=10),
			"deposit": 3000, "vehicles": [{"vehicle": vehicles[vi], "rate_per_day": daily, "km_included_per_day": free,
				"extra_km_rate": extra, "out_odometer": D.VEHICLES[vi][6]}]},
			{"customer": customers[ci], "company": company, "from_date": get_datetime(_day(s_off)).replace(hour=10)},
			label=f"{vehicles[vi]} / {D.CUSTOMERS[ci]}", submit=bool(submit and sub))
	frappe.db.commit()

	# --- fines and incidents
	for vi, ago, what, amount, authority, who in D.FINES:
		if vehicles[vi]:
			vals = {"vehicle": vehicles[vi], "fine_datetime": add_to_date(_day(-ago), hours=14), "violation": what,
				"amount": amount, "authority": authority, "responsibility": who, "status": "Unpaid", "company": company,
				"due_date": _day(30 - ago)}
			if who == "Customer":
				vals["customer"] = customers[4]
			_make(rep, "Traffic Fine", vals, {"vehicle": vehicles[vi], "violation": what, "amount": amount}, label=f"{vehicles[vi]} {what}")
	for vi, di, ago, itype, sev, fault, text in D.INCIDENTS:
		if vehicles[vi]:
			_make(rep, "Fleet Incident", {"vehicle": vehicles[vi], "driver": drivers[di] if di is not None else None,
				"incident_datetime": add_to_date(_day(-ago), hours=11), "incident_type": itype, "severity": sev,
				"fault": fault, "description": text, "company": company, "location": "الطريق الدائري - القاهرة",
				"status": "Under Review"}, {"vehicle": vehicles[vi], "incident_type": itype, "description": text}, label=f"{vehicles[vi]} {itype}")
	frappe.db.commit()

	text = rep.text()
	print(text)
	try:
		path = frappe.get_site_path("private", "files", "fleet-demo-report.txt")
		with open(path, "w", encoding="utf-8") as fh:
			fh.write(text + "\n")
		print("\nReport saved:", path)
	except Exception:
		pass
	return {"created": rep.created, "failed": len(rep.failed)}
