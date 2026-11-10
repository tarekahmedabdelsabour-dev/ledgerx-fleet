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
