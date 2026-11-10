"""Receive positions from trackers / telematics platforms.

POST /api/method/ledgerx_fleet.api.gps.ingest
Headers: X-Fleet-Token: <token from Fleet Settings>   (or Authorization: Bearer <token>)
Body (JSON), any of:
  {"device_id": "...", "latitude": .., "longitude": .., "speed": .., "timestamp": .., "ignition": true}
  {"positions": [ {...}, {...} ]}
  [ {...}, {...} ]
Traccar: enable forward.json with the URL above and header X-Fleet-Token (positions are accepted as-is).
"""
import hmac
import json

import frappe
from frappe import _
from frappe.utils import convert_utc_to_system_timezone, now_datetime

from ledgerx_fleet.utils import fleet, logic

MAX_BATCH = 1000


def _token_from_request():
	h = frappe.get_request_header("X-Fleet-Token")
	if h:
		return h.strip()
	auth = frappe.get_request_header("Authorization") or ""
	if auth.lower().startswith("bearer "):
		return auth[7:].strip()
	return None


def _check_token():
	supplied = _token_from_request()
	expected = frappe.utils.password.get_decrypted_password(
		"Fleet Settings", "Fleet Settings", "gps_api_token", raise_exception=False
	)
	if not expected or not supplied or not hmac.compare_digest(str(supplied), str(expected)):
		frappe.local.response["http_status_code"] = 401
		frappe.throw(_("Invalid or missing token"), frappe.AuthenticationError)


def _payload():
	body = frappe.request.get_json(silent=True) if frappe.request else None
	if body is None:
		body = {k: v for k, v in frappe.form_dict.items() if k not in ("cmd", "data")}
	if isinstance(body, dict) and isinstance(body.get("positions"), list):
		return body["positions"]
	if isinstance(body, dict) and isinstance(body.get("data"), list):
		return body["data"]
	if isinstance(body, dict) and isinstance(body.get("position"), dict):  # Traccar forward wrapper
		pos = dict(body["position"])
		dev = body.get("device") or {}
		pos.setdefault("device_id", dev.get("uniqueId") or pos.get("deviceId"))
		attrs = pos.get("attributes") or {}
		if "ignition" in attrs:
			pos["ignition"] = attrs["ignition"]
		if "totalDistance" in attrs:
			pos["odometer"] = float(attrs["totalDistance"]) / 1000.0
		if isinstance(pos.get("speed"), (int, float)):
			pos["speed"] = pos["speed"] * logic.KNOTS_TO_KMH  # Traccar reports knots
		return [pos]
	if isinstance(body, dict):
		return [body]
	if isinstance(body, list):
		return body
	return []


@frappe.whitelist(allow_guest=True, methods=["POST"])
def ingest(speed_unit="kmh"):
	_check_token()
	items = _payload()
	if not items:
		frappe.throw(_("No positions in the request"))
	if len(items) > MAX_BATCH:
		frappe.throw(_("At most {0} positions per request").format(MAX_BATCH))

	max_speed = fleet.get_settings().max_speed_kmh or 0
	devices = {}
	stored = 0
	unknown, rejected = set(), 0

	for raw in items:
		try:
			p = logic.normalize_position(raw, speed_unit if speed_unit in ("kmh", "knots") else "kmh")
		except (ValueError, TypeError, AttributeError):
			rejected += 1
			continue
		dev = devices.get(p["device_id"])
		if dev is None:
			dev = frappe.db.get_value(
				"GPS Device", p["device_id"], ["name", "vehicle", "status", "last_seen", "ignition_on"], as_dict=True
			) or False
			devices[p["device_id"]] = dev
		if not dev or dev.status != "Active":
			unknown.add(p["device_id"])
			continue

		when = p["position_time"] or now_datetime()
		if p["is_utc"]:
			when = convert_utc_to_system_timezone(when).replace(tzinfo=None)

		event = "Position"
		if max_speed and p["speed"] > max_speed:
			event = "Speeding"
		elif p["ignition"] is not None and bool(p["ignition"]) != bool(dev.ignition_on):
			event = "Ignition On" if p["ignition"] else "Ignition Off"

		doc = frappe.get_doc(
			{
				"doctype": "Fleet GPS Position",
				"device": dev.name,
				"vehicle": dev.vehicle,
				"position_time": when,
				"latitude": p["latitude"],
				"longitude": p["longitude"],
				"speed": p["speed"],
				"heading": p["heading"],
				"ignition": p["ignition"] or 0,
				"odometer": p["odometer"],
				"event": event,
			}
		)
		doc.name = frappe.generate_hash(length=12)
		doc.set_user_and_timestamp()
		doc.db_insert()
		stored += 1

		if not dev.last_seen or when >= dev.last_seen:
			dev.last_seen = when
			if p["ignition"] is not None:
				dev.ignition_on = p["ignition"]
			frappe.db.set_value(
				"GPS Device", dev.name,
				{"last_seen": when, "last_latitude": p["latitude"], "last_longitude": p["longitude"],
					"last_speed": p["speed"], "ignition_on": dev.ignition_on or 0},
				update_modified=False,
			)
			if dev.vehicle:
				frappe.db.set_value(
					"Vehicle", dev.vehicle,
					{"last_position_lat": p["latitude"], "last_position_lng": p["longitude"], "last_position_time": when},
					update_modified=False,
				)
				if p["odometer"]:
					fleet.update_vehicle_odometer(dev.vehicle, int(p["odometer"]))

	frappe.db.commit()
	return {"received": len(items), "stored": stored, "rejected": rejected, "unknown_devices": sorted(unknown)}
