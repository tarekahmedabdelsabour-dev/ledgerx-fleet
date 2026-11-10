import unittest
from datetime import date, datetime

from ledgerx_fleet.utils import logic as L


class TestLogic(unittest.TestCase):
	def test_overlap(self):
		d = date
		self.assertTrue(L.ranges_overlap(d(2026, 1, 1), d(2026, 1, 10), d(2026, 1, 10), d(2026, 1, 12)))
		self.assertFalse(L.ranges_overlap(d(2026, 1, 1), d(2026, 1, 9), d(2026, 1, 10), d(2026, 1, 12)))
		self.assertTrue(L.ranges_overlap(d(2026, 1, 1), None, d(2030, 1, 1), None))
		self.assertFalse(L.ranges_overlap(None, None, d(2030, 1, 1), None))
		dt = datetime
		self.assertTrue(L.ranges_overlap(dt(2026, 1, 1, 8), dt(2026, 1, 1, 12), dt(2026, 1, 1, 11), None))

	def test_document_status(self):
		t = date(2026, 6, 1)
		self.assertEqual(L.document_status("2026-05-31", t, 30), "Expired")
		self.assertEqual(L.document_status("2026-06-01", t, 30), "Expiring Soon")
		self.assertEqual(L.document_status("2026-07-01", t, 30), "Expiring Soon")
		self.assertEqual(L.document_status("2026-07-02", t, 30), "Active")
		self.assertEqual(L.days_left("2026-06-11", t), 10)

	def test_add_months(self):
		self.assertEqual(L.add_months("2026-01-31", 1), date(2026, 2, 28))
		self.assertEqual(L.add_months("2026-11-15", 14), date(2028, 1, 15))

	def test_schedule(self):
		nd, no = L.next_due("2026-01-01", 10000, 90, 5000)
		self.assertEqual(nd, date(2026, 4, 1))
		self.assertEqual(no, 15000)
		self.assertEqual(L.schedule_status(nd, no, date(2026, 2, 1), 12000, 14, 1000), "OK")
		self.assertEqual(L.schedule_status(nd, no, date(2026, 2, 1), 14500, 14, 1000), "Due Soon")
		self.assertEqual(L.schedule_status(nd, no, date(2026, 3, 25), 12000, 14, 1000), "Due Soon")
		self.assertEqual(L.schedule_status(nd, no, date(2026, 4, 2), 12000, 14, 1000), "Overdue")
		self.assertEqual(L.schedule_status(nd, no, date(2026, 2, 1), 15001, 14, 1000), "Overdue")
		self.assertEqual(L.next_due(None, None, 90, 5000), (None, None))
		self.assertEqual(L.next_due("2026-01-01", 0, 0, 5000), (None, 5000))

	def test_fuel(self):
		self.assertEqual(L.consumption_l_per_100km(500, 40), 8.0)
		self.assertEqual(L.consumption_l_per_100km(0, 40), 0.0)

	def test_trip_revenue(self):
		self.assertEqual(L.trip_revenue("Fixed", 1000, 300, 0), 1000)
		self.assertEqual(L.trip_revenue("Per Km", 5, 300, 0), 1500)
		self.assertEqual(L.trip_revenue("Per Ton", 200, 0, 12500), 2500)

	def test_rental(self):
		self.assertEqual(L.rental_days("2026-01-01 08:00:00", "2026-01-01 18:00:00"), 1)
		self.assertEqual(L.rental_days("2026-01-01 08:00:00", "2026-01-02 08:00:00"), 1)
		self.assertEqual(L.rental_days("2026-01-01 08:00:00", "2026-01-02 08:00:01"), 2)
		self.assertEqual(L.rental_days("2026-01-01 08:00:00.000000", "2026-01-04 09:00:00.000000"), 4)
		self.assertEqual(L.extra_km(900, 200, 3), 300)
		self.assertEqual(L.extra_km(500, 200, 3), 0)
		self.assertEqual(L.extra_km(900, 0, 3), 0)

	def test_tire(self):
		self.assertEqual(L.tire_km(1000, 21000, 60000), (20000, 40000))
		self.assertEqual(L.tire_km(1000, 99000, 60000), (98000, 0))

	def test_gps(self):
		p = L.normalize_position({"id": 7, "lat": "30.04", "lon": "31.23", "speed": "54", "timestamp": "1767225600"}, "knots")
		self.assertEqual(p["device_id"], "7")
		self.assertAlmostEqual(p["speed"], 100.01, places=1)
		self.assertEqual(p["position_time"], datetime(2026, 1, 1, 0, 0))
		p = L.normalize_position({"device_id": "A", "latitude": 1, "longitude": 2, "ignition": "on"})
		self.assertEqual(p["ignition"], 1)
		self.assertIsNone(p["position_time"])
		p = L.normalize_position({"device_id": "A", "latitude": 1, "longitude": 2, "fixTime": "2026-01-01T10:00:00.000+00:00"})
		self.assertTrue(p["is_utc"])
		self.assertEqual(p["position_time"], datetime(2026, 1, 1, 10, 0))
		with self.assertRaises(ValueError):
			L.normalize_position({"device_id": "A", "latitude": 91, "longitude": 2})
		with self.assertRaises(ValueError):
			L.normalize_position({"latitude": 1, "longitude": 2})


if __name__ == "__main__":
	unittest.main()


class TestDemoData(unittest.TestCase):
	"""Static check: every key the demo loader writes exists in the DocType JSON."""

	def test_loader_fields_exist(self):
		import ast, glob, json, os, re
		base = os.path.dirname(os.path.dirname(__file__))
		fields = {}
		for f in glob.glob(os.path.join(base, "fleet_management/doctype/*/*.json")):
			d = json.load(open(f))
			if d.get("doctype") == "DocType":
				fields[d["name"]] = {x["fieldname"] for x in d["fields"]}
		src = open(os.path.join(base, "demo/loader.py"), encoding="utf-8").read()
		for dt in ("Fleet Document", "Fuel Log", "Fleet Trip", "Rental Contract", "Traffic Fine", "Fleet Incident"):
			self.assertIn(dt, fields)
		self.assertNotIn("default_cost_center", src)
		self.assertIn("cost_center", fields["Fleet Settings"])
		self.assertIn("station_name", fields["Fuel Log"])
		from ledgerx_fleet.demo import data
		cats = {"Oil and Filters", "Brakes", "Tires", "Inspection", "Electrical", "Body", "Other"}
		for _p, _v, tasks in data.SERVICE_PLANS:
			for t in tasks:
				self.assertIn(t[1], cats)
		for v in data.VEHICLES:
			self.assertIn(v[5], ("Petrol", "Diesel"))


class TestCustody(unittest.TestCase):
	def test_balance(self):
		r = L.custody_summary(
			[("Advance", 5000), ("Advance", 1000), ("Return", 500), ("Reimbursement", 100)],
			[("Custody", "Approved", 1200), ("Custody", "Pending", 300), ("Custody", "Rejected", 999),
				("Personal", "Approved", 250), ("Personal", "Pending", 80), ("Personal", "Rejected", 40)],
		)
		self.assertEqual(r["custody_balance"], 5000 + 1000 - 500 - 1200 - 300)
		self.assertEqual(r["pending"], 300)
		self.assertEqual(r["owed_to_driver"], 250 - 100)
		self.assertEqual(L.custody_summary([], [])["custody_balance"], 0)

	def test_driver_api_fields_exist(self):
		import json, os, re
		base = os.path.dirname(os.path.dirname(__file__))
		def fields(dt):
			p = os.path.join(base, "fleet_management/doctype", dt.lower().replace(" ", "_"), dt.lower().replace(" ", "_") + ".json")
			return {f["fieldname"]: f for f in json.load(open(p))["fields"]}
		src = open(os.path.join(base, "api/driver.py"), encoding="utf-8").read()
		for dt, keys in {
			"Driver Odometer Log": ["driver", "vehicle", "log_date", "log_type", "odometer", "notes", "latitude", "longitude", "logged_at", "photo"],
			"Driver Expense": ["driver", "vehicle", "expense_date", "category", "amount", "paid_from", "litres", "odometer", "description", "status", "receipt"],
			"Fleet Incident": ["vehicle", "driver", "incident_datetime", "incident_type", "severity", "location", "description", "injuries", "status", "attachments"],
		}.items():
			f = fields(dt)
			for k in keys:
				self.assertIn(k, f, f"{dt}.{k}")
		# select options used by the page / api must exist in the doctypes
		opts = lambda dt, k: set(fields(dt)[k]["options"].split("\n"))
		self.assertTrue({"Fuel", "Maintenance", "Tires", "Toll", "Parking", "Wash", "Other"} <= opts("Driver Expense", "category"))
		self.assertTrue({"Breakdown", "Collision", "Theft", "Fire", "Vandalism", "Injury", "Other"} <= opts("Fleet Incident", "incident_type"))
		self.assertTrue({"Minor", "Moderate", "Severe", "Total Loss"} <= opts("Fleet Incident", "severity"))
		self.assertTrue({"Start of Day", "End of Day"} <= opts("Driver Odometer Log", "log_type"))
		html = open(os.path.join(base, "www/driver.html"), encoding="utf-8").read()
		for m in re.findall(r'<option value="([A-Za-z ]+)"', html):
			self.assertTrue(any(m in o for dt, k in [("Driver Expense", "category"), ("Driver Expense", "paid_from"),
				("Fleet Incident", "incident_type"), ("Fleet Incident", "severity")] for o in [opts(dt, k)]), m)
