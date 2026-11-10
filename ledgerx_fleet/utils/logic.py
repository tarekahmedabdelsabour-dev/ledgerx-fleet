"""Pure business rules (no Frappe imports) so they can be unit-tested anywhere."""
import calendar
import math
import re
from datetime import date, datetime, timedelta, timezone

KNOTS_TO_KMH = 1.852


def to_date(v):
	if v is None or v == "":
		return None
	if isinstance(v, datetime):
		return v.date()
	if isinstance(v, date):
		return v
	return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()


def to_datetime(v):
	if v is None or v == "":
		return None
	if isinstance(v, datetime):
		return v
	if isinstance(v, date):
		return datetime(v.year, v.month, v.day)
	s = re.sub(r"(Z|[+-]\d\d:?\d\d)$", "", str(v).strip().replace("T", " "))
	for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
		try:
			return datetime.strptime(s, fmt)
		except ValueError:
			continue
	raise ValueError(f"Unrecognized datetime: {v!r}")


def add_months(d, months):
	d = to_date(d)
	m = d.month - 1 + int(months)
	y = d.year + m // 12
	m = m % 12 + 1
	return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def ranges_overlap(s1, e1, s2, e2):
	"""Inclusive overlap of two ranges. A missing end means open-ended; a missing start never overlaps."""
	if s1 is None or s2 is None:
		return False
	far = datetime.max if isinstance(s1, datetime) else date.max
	e1 = e1 or far
	e2 = e2 or far
	return s1 <= e2 and s2 <= e1


# ---- documents -------------------------------------------------------------------------
def days_left(expiry, today):
	return (to_date(expiry) - to_date(today)).days


def document_status(expiry, today, alert_days):
	left = days_left(expiry, today)
	if left < 0:
		return "Expired"
	if left <= int(alert_days or 0):
		return "Expiring Soon"
	return "Active"


# ---- maintenance -----------------------------------------------------------------------
def next_due(last_date, last_odometer, interval_days, interval_km):
	nd = None
	no = None
	if interval_days and last_date:
		nd = to_date(last_date) + timedelta(days=int(interval_days))
	if interval_km and last_odometer is not None:
		no = int(last_odometer) + int(interval_km)
	return nd, no


def schedule_status(next_date, next_odo, today, current_odo, alert_days, alert_km):
	"""Overdue if either limit is passed, Due Soon if either is within the alert window."""
	overdue = soon = False
	if next_date:
		left = days_left(next_date, today)
		overdue |= left < 0
		soon |= 0 <= left <= int(alert_days or 0)
	if next_odo is not None and current_odo is not None:
		left_km = int(next_odo) - int(current_odo)
		overdue |= left_km < 0
		soon |= 0 <= left_km <= int(alert_km or 0)
	return "Overdue" if overdue else "Due Soon" if soon else "OK"


# ---- fuel ------------------------------------------------------------------------------
def consumption_l_per_100km(distance, liters):
	if not distance or distance <= 0 or not liters or liters <= 0:
		return 0.0
	return round(liters / distance * 100, 2)


# ---- trips -----------------------------------------------------------------------------
def trip_revenue(rate_basis, rate, distance, weight_kg):
	rate = float(rate or 0)
	if rate_basis == "Per Km":
		return round(rate * float(distance or 0), 2)
	if rate_basis == "Per Ton":
		return round(rate * float(weight_kg or 0) / 1000.0, 2)
	return round(rate, 2)


# ---- rental ----------------------------------------------------------------------------
def rental_days(start, end):
	"""Charged days: every started 24h counts, minimum 1."""
	secs = (to_datetime(end) - to_datetime(start)).total_seconds()
	return max(1, math.ceil(secs / 86400.0 - 1e-9))


def extra_km(distance, km_included_per_day, days):
	"""km_included_per_day == 0 means unlimited."""
	if not km_included_per_day:
		return 0.0
	return max(0.0, float(distance or 0) - float(km_included_per_day) * float(days))


# ---- tires -----------------------------------------------------------------------------
def tire_km(mount_odometer, current_odometer, expected_life):
	run = max(0, int(current_odometer or 0) - int(mount_odometer or 0))
	return run, max(0, int(expected_life or 0) - run)


# ---- GPS -------------------------------------------------------------------------------
def _first(d, *keys):
	for k in keys:
		if k in d and d[k] not in (None, ""):
			return d[k]
	return None


def normalize_position(raw, speed_unit="kmh"):
	"""Map the many tracker/platform key spellings onto one record, or raise ValueError."""
	device = _first(raw, "device_id", "deviceId", "id", "imei", "uniqueId")
	lat = _first(raw, "latitude", "lat")
	lng = _first(raw, "longitude", "lon", "lng", "long")
	if device is None or lat is None or lng is None:
		raise ValueError("device_id, latitude and longitude are required")
	lat, lng = float(lat), float(lng)
	if not (-90 <= lat <= 90 and -180 <= lng <= 180):
		raise ValueError("coordinates out of range")
	speed = float(_first(raw, "speed") or 0)
	if speed_unit == "knots":
		speed = round(speed * KNOTS_TO_KMH, 2)
	is_utc = False
	ts = _first(raw, "position_time", "timestamp", "time", "fixTime")
	if isinstance(ts, (int, float)) or (isinstance(ts, str) and ts.isdigit()):
		t = float(ts)
		if t > 1e11:  # milliseconds
			t /= 1000.0
		pt = datetime.fromtimestamp(t, timezone.utc).replace(tzinfo=None)
		is_utc = True
	elif ts:
		pt = to_datetime(ts)
		is_utc = str(ts).endswith(("Z", "+00:00"))
	else:
		pt = None
	ign = _first(raw, "ignition")
	if isinstance(ign, str):
		ign = ign.strip().lower() in ("1", "true", "on", "yes")
	odo = _first(raw, "odometer", "totalDistance")
	return {
		"device_id": str(device),
		"latitude": lat,
		"longitude": lng,
		"speed": speed,
		"heading": float(_first(raw, "heading", "bearing", "course") or 0),
		"position_time": pt,
		"is_utc": is_utc,
		"ignition": None if ign is None else int(bool(ign)),
		"odometer": None if odo is None else float(odo),
	}


def custody_summary(entries, expenses):
	"""Driver custody ("عهدة") balance.

	entries:  iterable of (entry_type, amount)  - Advance / Return / Reimbursement
	expenses: iterable of (paid_from, status, amount) - Custody|Personal, Pending|Approved|Rejected

	custody_balance = advances - returns - expenses paid from custody (not rejected)
	owed_to_driver  = approved personal expenses - reimbursements
	Rejected expenses never count. Pending custody expenses already reduce the balance.
	"""
	adv = ret = reimb = 0.0
	for t, a in entries:
		a = float(a or 0)
		if t == "Advance":
			adv += a
		elif t == "Return":
			ret += a
		elif t == "Reimbursement":
			reimb += a
	spent = personal = pending = 0.0
	for paid_from, status, a in expenses:
		a = float(a or 0)
		if status == "Rejected":
			continue
		if paid_from == "Custody":
			spent += a
			if status == "Pending":
				pending += a
		elif status == "Approved":
			personal += a
	return {
		"advances": adv, "returns": ret, "spent": spent, "pending": pending,
		"custody_balance": round(adv - ret - spent, 2),
		"owed_to_driver": round(personal - reimb, 2),
	}
